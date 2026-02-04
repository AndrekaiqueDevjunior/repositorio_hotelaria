from typing import Dict, Any, List
from datetime import datetime, date
from fastapi import HTTPException
from app.schemas.reserva_schema import ReservaCreate, ReservaResponse
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.tarifa_suite_repo import TarifaSuiteRepository
from app.core.validators import ReservaValidator
from prisma import Client
from prisma.errors import UniqueViolationError
from app.services.notification_service import NotificationService
import secrets
import re

class ReservaRepository:
    def __init__(self, db: Client):
        self.db = db

    async def _obter_tarifa_diaria(self, suite_tipo: str, checkin_previsto: datetime) -> float:
        tarifa_repo = TarifaSuiteRepository(self.db)

        suite_tipo_norm = suite_tipo.value if hasattr(suite_tipo, "value") else str(suite_tipo)

        if not checkin_previsto:
            raise ValueError("Data de check-in inválida para buscar tarifa")

        data_ref = checkin_previsto.date() if isinstance(checkin_previsto, datetime) else checkin_previsto
        tarifa = await tarifa_repo.get_tarifa_ativa(suite_tipo_norm, data_ref)

        if not tarifa:
            raise ValueError(
                f"Tarifa não cadastrada para a suíte {suite_tipo_norm} na data {data_ref}. Cadastre uma tarifa antes de criar a reserva."
            )

        return float(tarifa.get("preco_diaria", 0.0))
    
    async def list_all(
        self,
        search: str = None,
        status: str = None,
        checkin_inicio: str = None,
        checkin_fim: str = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = None
    ) -> Dict[str, Any]:
        """Listar todas as reservas com filtros e busca"""
        where_conditions = {}
        
        # Filtro de busca (nome cliente ou número quarto)
        if search:
            where_conditions["OR"] = [
                {"clienteNome": {"contains": search, "mode": "insensitive"}},
                {"quartoNumero": {"contains": search, "mode": "insensitive"}},
                {"codigoReserva": {"contains": search, "mode": "insensitive"}}
            ]
        
        # Filtro de status
        if status:
            where_conditions["statusReserva"] = status
        
        # Filtro de data de checkin
        if checkin_inicio or checkin_fim:
            where_conditions["checkinPrevisto"] = {}
            if checkin_inicio:
                from app.utils.datetime_utils import to_utc
                where_conditions["checkinPrevisto"]["gte"] = to_utc(datetime.fromisoformat(checkin_inicio))
            if checkin_fim:
                from app.utils.datetime_utils import to_utc
                where_conditions["checkinPrevisto"]["lte"] = to_utc(datetime.fromisoformat(checkin_fim))
        
        # Buscar total de registros (para paginação)
        total = await self.db.reserva.count(where=where_conditions if where_conditions else None)
        
        # Processar ordenação
        order_clause = {"id": "desc"}  # Ordem padrão
        
        if order_by:
            # Formato esperado: "campo:ordem" (ex: "data_criacao:desc")
            if ":" in order_by:
                field, direction = order_by.split(":", 1)
                order_clause = {field: direction.lower()}
        
        # Buscar registros com paginação - P0-002: Incluir pagamentos e hospedagem
        registros = await self.db.reserva.find_many(
            where=where_conditions if where_conditions else None,
            include={
                "pagamentos": True,  # Incluir pagamentos para validação no frontend
                "hospedagem": True   # Incluir hospedagem para validação de checkout
            },
            order=order_clause,
            skip=offset,
            take=limit
        )
        
        return {
            "reservas": [self._serialize_reserva(r) for r in registros],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def create(self, reserva: ReservaCreate) -> Dict[str, Any]:
        """Criar nova reserva com validações"""
        # Verificar se cliente existe
        cliente = await self.db.cliente.find_unique(where={"id": reserva.cliente_id})
        if not cliente:
            raise ValueError("Cliente não encontrado")

        # VALIDAÇÃO: Verificar se cliente já tem reservas ativas
        reservas_ativas = await self.db.reserva.find_many(
            where={
                "clienteId": reserva.cliente_id,
                "statusReserva": {"in": ["PENDENTE", "CONFIRMADA", "HOSPEDADO"]}
            }
        )
        
        if reservas_ativas:
            # Verificar se há conflito de datas
            for reserva_ativa in reservas_ativas:
                # Se a reserva ativa estiver no mesmo período ou sobrepor o novo período
                if (reserva.checkin_previsto.date() <= reserva_ativa.checkoutPrevisto.date() and 
                    reserva.checkout_previsto.date() >= reserva_ativa.checkinPrevisto.date()):
                    
                    # Calcular dias restantes da reserva ativa
                    from app.utils.datetime_utils import to_utc, now_utc
                    checkout_previsto_utc = to_utc(reserva_ativa.checkinPrevisto)
                    dias_restantes = (checkout_previsto_utc.date() - now_utc().date()).days
                    
                    msg_erro = f"❌ CLIENTE JÁ POSSUI RESERVA ATIVA!"
                    msg_erro += f"\n\n📋 Reserva existente: {reserva_ativa.codigoReserva}"
                    msg_erro += f"\n  • Quarto: {reserva_ativa.quartoNumero}"
                    msg_erro += f"\n  • Check-in: {reserva_ativa.checkinPrevisto.strftime('%d/%m/%Y')}"
                    msg_erro += f"\n  • Check-out: {reserva_ativa.checkoutPrevisto.strftime('%d/%m/%Y')}"
                    msg_erro += f"\n  • Status: {reserva_ativa.statusReserva}"
                    
                    if dias_restantes > 0:
                        msg_erro += f"\n\n⚠️ Para fazer uma nova reserva, você deve:"
                        msg_erro += f"\n  1. Aguardar o check-in da reserva atual"
                        msg_erro += f"\n  2. Fazer check-out da reserva atual"
                        msg_erro += f"\n  3. Cancelar a reserva atual (se permitido)"
                    else:
                        msg_erro += f"\n\n📞 Entre em contato com a recepção para assistência."
                    
                    raise ValueError(msg_erro)

        valor_diaria = await self._obter_tarifa_diaria(
            reserva.tipo_suite,
            reserva.checkin_previsto,
        )

        quarto = await self.db.quarto.find_unique(where={"numero": reserva.quarto_numero})
        if not quarto:
            raise ValueError("Quarto não encontrado")
        
        if quarto.status in ("BLOQUEADO", "MANUTENCAO"):
            raise ValueError(f"❌ Quarto {reserva.quarto_numero} está {quarto.status.lower()} e não pode ser reservado")
        
        # VALIDAÇÃO CRÍTICA: Verificar disponibilidade usando DisponibilidadeService
        from app.services.disponibilidade_service import DisponibilidadeService
        disponibilidade_service = DisponibilidadeService(self.db)
        
        resultado = await disponibilidade_service.verificar_disponibilidade(
            reserva.quarto_numero,
            reserva.checkin_previsto,
            reserva.checkout_previsto
        )
        
        if not resultado["disponivel"]:
            # Sugerir quartos alternativos
            alternativas = await disponibilidade_service.sugerir_quartos_alternativos(
                reserva.tipo_suite,
                reserva.checkin_previsto,
                reserva.checkout_previsto,
                limite=3
            )
            
            msg_erro = f"❌ QUARTO INDISPONÍVEL! {resultado['motivo']}"
            
            if resultado["conflitos"]:
                msg_erro += f"\n\n📋 Conflitos encontrados:"
                for conflito in resultado["conflitos"]:
                    msg_erro += f"\n  • Reserva {conflito['codigo']} - {conflito['cliente']}"
                    msg_erro += f"\n    Check-in: {conflito['checkin'][:10]} | Check-out: {conflito['checkout'][:10]}"
            
            if alternativas:
                msg_erro += f"\n\n💡 Quartos {reserva.tipo_suite} disponíveis no período:"
                for alt in alternativas:
                    msg_erro += f"\n  • Quarto {alt['numero']}"
            else:
                msg_erro += f"\n\n⚠️ Nenhum quarto {reserva.tipo_suite} disponível neste período"
            
            raise ValueError(msg_erro)
        
        from app.utils.datetime_utils import now_utc
        
        # Gerar código único com retry (evita colisões em concorrência)
        tentativa = 0
        nova_reserva = None
        while tentativa < 5:
            tentativa += 1
            codigo_reserva = f"RCF-{now_utc().strftime('%Y%m')}-{secrets.token_hex(3).upper()}"

            try:
                nova_reserva = await self.db.reserva.create(
                    data={
                        "codigoReserva": codigo_reserva,
                        "clienteId": reserva.cliente_id,
                        "quartoId": quarto.id,
                        "quartoNumero": reserva.quarto_numero,
                        "tipoSuite": reserva.tipo_suite,
                        "clienteNome": cliente.nomeCompleto,
                        "checkinPrevisto": reserva.checkin_previsto,
                        "checkoutPrevisto": reserva.checkout_previsto,
                        "valorDiaria": valor_diaria,
                        "numDiarias": reserva.num_diarias,
                        "statusReserva": "PENDENTE"
                    }
                )
                break
            except UniqueViolationError:
                nova_reserva = None

        if not nova_reserva:
            raise ValueError("Não foi possível gerar um código de reserva único")
        
        # Criar notificação de nova reserva
        await NotificationService.notificar_nova_reserva(self.db, nova_reserva)
        
        return self._serialize_reserva(nova_reserva)
    
    async def get_by_id(self, reserva_id: int) -> Dict[str, Any]:
        """Obter reserva por ID com todos os dados relacionados"""
        # Buscar reserva com pagamentos incluídos
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"pagamentos": True}
        )
        if not reserva:
            raise ValueError("Reserva não encontrada")
        return self._serialize_reserva(reserva)

    async def get_by_codigo(self, codigo_reserva: str) -> Dict[str, Any]:
        """Obter reserva por código (codigoReserva) com dados relacionados"""
        codigo_upper = (codigo_reserva or "").upper().strip()
        if not codigo_upper:
            raise ValueError("Código de reserva inválido")

        reserva = await self.db.reserva.find_first(
            where={"codigoReserva": codigo_upper},
            include={"pagamentos": True}
        )

        if not reserva:
            raise ValueError("Reserva não encontrada")

        return self._serialize_reserva(reserva)
    
    async def checkin(self, reserva_id: int) -> Dict[str, Any]:
        """Realizar check-in da reserva"""
        from app.utils.datetime_utils import now_utc
        
        # P1-001: Buscar reserva com pagamentos para validação
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"pagamentos": True}
        )
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        # P1-001: VALIDAÇÃO 1 - Status deve ser CONFIRMADA (não mais PENDENTE)
        if reserva.statusReserva != "CONFIRMADA":
            raise ValueError(f"Check-in requer status CONFIRMADA. Status atual: {reserva.statusReserva}")
        
        # P1-001: VALIDAÇÃO 2 - Deve ter pagamento aprovado
        pagamentos_aprovados = [
            p for p in reserva.pagamentos
            if p.status in ("APROVADO", "PAGO", "CONFIRMADO", "CAPTURED", "AUTHORIZED")
        ]
        
        if not pagamentos_aprovados:
            raise ValueError("Check-in requer pagamento aprovado. Realize o pagamento antes do check-in.")
        
        # P1-001: VALIDAÇÃO 3 - Verificar se quarto está livre
        quarto = await self.db.quarto.find_unique(where={"numero": reserva.quartoNumero})
        if quarto and quarto.status != "LIVRE":
            raise ValueError(f"Quarto {reserva.quartoNumero} não está disponível (status: {quarto.status})")
        
        # Atualizar status da reserva
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": "HOSPEDADO",
                "checkinReal": now_utc()
            }
        )
        
        # Atualizar status do quarto
        quarto_numero_raw = (reserva.quartoNumero or "").strip()
        match = re.search(r"\d+", quarto_numero_raw)
        quarto_numero = match.group(0) if match else quarto_numero_raw
        await self.db.quarto.update(
            where={"numero": quarto_numero},
            data={"status": "OCUPADO"}
        )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        
        # Criar notificação de check-in
        await NotificationService.notificar_checkin_realizado(self.db, updated_reserva)
        
        return self._serialize_reserva(updated_reserva)
    
    async def checkout(self, reserva_id: int) -> Dict[str, Any]:
        """Realizar check-out da reserva"""
        from app.utils.datetime_utils import now_utc
        
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        # Verificar status da reserva
        if reserva.statusReserva not in ("HOSPEDADO", "CHECKIN_REALIZADO", "CHECKED_IN"):
            raise ValueError("Apenas reservas hospedadas podem fazer check-out")
        
        # VALIDAÇÃO CRÍTICA: Verificar se há pagamentos pendentes
        # Cliente não pode sair sem pagar!
        pagamentos = await self.db.pagamento.find_many(
            where={"reservaId": reserva_id}
        )
        
        # Calcular valor total da reserva
        valor_total_reserva = float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0.0
        
        # Calcular total pago (apenas pagamentos aprovados)
        total_pago = sum(
            float(p.valor) for p in pagamentos 
            if p.status in ("APROVADO", "CONFIRMADO")
        )
        
        # Calcular saldo pendente
        saldo_pendente = valor_total_reserva - total_pago
        
        # BLOQUEIO: Não permite check-out se houver dívida
        if saldo_pendente > 0.01:  # Tolerância de 1 centavo para arredondamento
            raise ValueError(
                f"❌ CHECK-OUT BLOQUEADO! Cliente possui saldo pendente de R$ {saldo_pendente:.2f}. "
                f"Valor total: R$ {valor_total_reserva:.2f} | Pago: R$ {total_pago:.2f}. "
                f"O pagamento deve ser realizado antes do check-out!"
            )
        
        # Atualizar status da reserva
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": "CHECKED_OUT",
                "checkoutReal": now_utc()
            }
        )
        
        # Atualizar status do quarto
        quarto_numero_raw = (reserva.quartoNumero or "").strip()
        match = re.search(r"\d+", quarto_numero_raw)
        quarto_numero = match.group(0) if match else quarto_numero_raw
        await self.db.quarto.update(
            where={"numero": quarto_numero},
            data={"status": "LIVRE"}
        )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        
        # Creditar pontos automaticamente para o cliente (idempotente)
        try:
            from app.services.pontos_checkout_service import creditar_rp_no_checkout

            resultado_pontos = await creditar_rp_no_checkout(
                self.db,
                reserva_id=reserva_id,
                funcionario_id=None,
                checkout_datetime=getattr(updated_reserva, "checkoutReal", None),
            )

            pontos_ganhos = int(resultado_pontos.get("pontos", 0) or 0) if resultado_pontos.get("creditado") else 0
        except Exception as e:
            pontos_ganhos = 0
            print(f"[CHECKOUT] Erro ao creditar pontos: {e}")
        
        # Criar notificação de check-out
        await NotificationService.notificar_checkout_realizado(self.db, updated_reserva)
        
        # Retornar reserva com informações de pontos
        resultado = self._serialize_reserva(updated_reserva)
        resultado["pontos_ganhos"] = pontos_ganhos if pontos_ganhos > 0 else 0
        
        return resultado
    
    async def cancelar(self, reserva_id: int) -> Dict[str, Any]:
        """
        Cancelar reserva com sistema de estornos automáticos
        
        RES-003 FIX: Processa estornos automaticamente quando possível
        """
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        if reserva.statusReserva not in ("PENDENTE", "CONFIRMADA", "HOSPEDADO"):
            raise ValueError("Apenas reservas pendentes, confirmadas ou hospedadas podem ser canceladas")
        
        # RES-003 FIX: Processar estornos ANTES do cancelamento
        estornos_processados = []
        estornos_pendentes = []
        
        try:
            # Buscar pagamentos aprovados para estorno
            pagamentos_aprovados = await self.db.pagamento.find_many(
                where={
                    "reservaId": reserva_id,
                    "status": {"in": ["APROVADO", "CONFIRMADO", "CAPTURED", "AUTHORIZED"]}
                }
            )
            
            if pagamentos_aprovados:
                print(f"[RES-003] Encontrados {len(pagamentos_aprovados)} pagamentos para estorno")
                
                for pagamento in pagamentos_aprovados:
                    try:
                        # Verificar se pode estornar (prazo, método, etc.)
                        pode_estornar = await self._pode_processar_estorno(pagamento)
                        
                        if pode_estornar["permitido"]:
                            # Processar estorno automático
                            resultado_estorno = await self._processar_estorno_automatico(pagamento)
                            
                            if resultado_estorno["sucesso"]:
                                estornos_processados.append({
                                    "pagamento_id": pagamento.id,
                                    "valor": float(pagamento.valor),
                                    "metodo": pagamento.metodo,
                                    "status": "ESTORNADO_AUTOMATICAMENTE"
                                })
                            else:
                                estornos_pendentes.append({
                                    "pagamento_id": pagamento.id,
                                    "valor": float(pagamento.valor),
                                    "metodo": pagamento.metodo,
                                    "motivo": resultado_estorno["erro"]
                                })
                        else:
                            # Adicionar à lista de estornos manuais
                            estornos_pendentes.append({
                                "pagamento_id": pagamento.id,
                                "valor": float(pagamento.valor),
                                "metodo": pagamento.metodo,
                                "motivo": pode_estornar["motivo"]
                            })
                            
                    except Exception as e:
                        print(f"⚠️ [RES-003] Erro ao processar estorno do pagamento {pagamento.id}: {e}")
                        estornos_pendentes.append({
                            "pagamento_id": pagamento.id,
                            "valor": float(pagamento.valor),
                            "metodo": pagamento.metodo,
                            "motivo": f"Erro no processamento: {str(e)}"
                        })
                        
        except Exception as e:
            print(f"⚠️ [RES-003] Erro geral no sistema de estornos: {e}")
            # Continua o cancelamento mesmo com erro nos estornos
        
        # Atualizar status da reserva
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": "CANCELADO"
            }
        )
        
        # CORREÇÃO CRÍTICA: Liberar quarto independente do status da reserva
        # Se estava HOSPEDADO, CONFIRMADA ou qualquer outro status ativo, liberar o quarto
        if reserva.statusReserva in ["HOSPEDADO", "CONFIRMADA", "PENDENTE", "AGUARDANDO_PAGAMENTO"]:
            # Verificar se o quarto realmente precisa ser liberado (não está LIVRE)
            quarto_numero_raw = (reserva.quartoNumero or "").strip()
            match = re.search(r"\d+", quarto_numero_raw)
            quarto_numero = match.group(0) if match else quarto_numero_raw
            quarto = await self.db.quarto.find_unique(where={"numero": quarto_numero})
            if quarto and quarto.status != "LIVRE":
                await self.db.quarto.update(
                    where={"numero": quarto_numero},
                    data={"status": "LIVRE"}
                )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        
        # RES-003 FIX: Notificar sobre estornos processados e pendentes
        if estornos_processados or estornos_pendentes:
            await self._notificar_estornos(reserva_id, estornos_processados, estornos_pendentes)
        
        # Criar notificação de cancelamento
        await NotificationService.notificar_reserva_cancelada(self.db, updated_reserva)
        
        # RES-003 FIX: Incluir informações de estorno no retorno
        resultado = self._serialize_reserva(updated_reserva)
        resultado["estornos"] = {
            "processados": estornos_processados,
            "pendentes": estornos_pendentes,
            "total_estornado": sum(e["valor"] for e in estornos_processados),
            "total_pendente": sum(e["valor"] for e in estornos_pendentes)
        }
        
        return resultado
    
    async def _pode_processar_estorno(self, pagamento) -> Dict[str, Any]:
        """
        RES-003 FIX: Verificar se pagamento pode ser estornado automaticamente
        
        Regras de negócio para estorno:
        - Cartão: até 120 dias após pagamento
        - PIX: até 90 dias após pagamento  
        - Dinheiro: não permite estorno automático
        """
        from datetime import timedelta
        from app.utils.datetime_utils import now_utc, to_utc
        
        try:
            # Verificar idade do pagamento
            pagamento_created_utc = to_utc(pagamento.createdAt)
            idade_pagamento = now_utc() - pagamento_created_utc
            
            # Regras por método de pagamento
            if pagamento.metodo in ["credit_card", "debit_card"]:
                if idade_pagamento.days > 120:
                    return {
                        "permitido": False,
                        "motivo": f"Pagamento com cartão muito antigo ({idade_pagamento.days} dias). Limite: 120 dias."
                    }
                return {"permitido": True, "motivo": "Cartão dentro do prazo"}
                
            elif pagamento.metodo == "pix":
                if idade_pagamento.days > 90:
                    return {
                        "permitido": False,
                        "motivo": f"PIX muito antigo ({idade_pagamento.days} dias). Limite: 90 dias."
                    }
                return {"permitido": True, "motivo": "PIX dentro do prazo"}
                
            elif pagamento.metodo in ["dinheiro", "cash"]:
                return {
                    "permitido": False,
                    "motivo": "Pagamentos em dinheiro requerem estorno manual na recepção"
                }
                
            else:
                return {
                    "permitido": False,
                    "motivo": f"Método {pagamento.metodo} não suporta estorno automático"
                }
                
        except Exception as e:
            return {
                "permitido": False,
                "motivo": f"Erro ao validar estorno: {str(e)}"
            }
    
    async def _processar_estorno_automatico(self, pagamento) -> Dict[str, Any]:
        """
        RES-003 FIX: Processar estorno automático via gateway
        """
        try:
            # Integrar com gateway de pagamento (Cielo, etc.)
            from app.services.cielo_service import CieloAPI
            
            cielo_api = CieloAPI()
            
            # Processar estorno baseado no método
            if pagamento.metodo in ["credit_card", "debit_card"]:
                resultado = await cielo_api.estornar_pagamento_cartao(
                    payment_id=pagamento.cieloPaymentId,
                    valor=float(pagamento.valor),
                    motivo="Cancelamento de reserva"
                )
            elif pagamento.metodo == "pix":
                resultado = await cielo_api.estornar_pix(
                    txid=pagamento.cieloPaymentId,
                    valor=float(pagamento.valor)
                )
            else:
                return {
                    "sucesso": False,
                    "erro": f"Método {pagamento.metodo} não implementado para estorno automático"
                }
            
            if resultado.get("success"):
                # Atualizar status do pagamento
                await self.db.pagamento.update(
                    where={"id": pagamento.id},
                    data={"status": "ESTORNADO"}
                )
                
                return {
                    "sucesso": True,
                    "estorno_id": resultado.get("refund_id"),
                    "valor_estornado": float(pagamento.valor)
                }
            else:
                return {
                    "sucesso": False,
                    "erro": resultado.get("error", "Erro desconhecido no gateway")
                }
                
        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro no processamento: {str(e)}"
            }
    
    async def _notificar_estornos(self, reserva_id: int, estornos_processados: list, estornos_pendentes: list):
        """
        RES-003 FIX: Notificar equipe sobre estornos processados e pendentes
        """
        try:
            # Notificação para equipe financeira
            total_estornado = sum(e["valor"] for e in estornos_processados)
            total_pendente = sum(e["valor"] for e in estornos_pendentes)
            
            mensagem_notificacao = f"""
🔔 CANCELAMENTO COM ESTORNOS - Reserva #{reserva_id}

✅ ESTORNOS PROCESSADOS AUTOMATICAMENTE:
"""
            
            for estorno in estornos_processados:
                mensagem_notificacao += f"   • R$ {estorno['valor']:.2f} ({estorno['metodo']})\n"
                
            if estornos_pendentes:
                mensagem_notificacao += f"""
⚠️ ESTORNOS PENDENTES (AÇÃO MANUAL NECESSÁRIA):
"""
                for estorno in estornos_pendentes:
                    mensagem_notificacao += f"   • R$ {estorno['valor']:.2f} ({estorno['metodo']}) - {estorno['motivo']}\n"
            
            mensagem_notificacao += f"""
💰 RESUMO:
   • Total estornado: R$ {total_estornado:.2f}
   • Total pendente: R$ {total_pendente:.2f}
"""

            # Enviar notificação (implementar conforme sistema de notificações)
            print(f"[RES-003] {mensagem_notificacao}")
            
            # TODO: Integrar com sistema de notificações (email, Slack, etc.)
            
        except Exception as e:
            print(f"⚠️ [RES-003] Erro ao enviar notificações de estorno: {e}")
    
    async def confirmar(self, reserva_id: int) -> Dict[str, Any]:
        """
        Confirmar reserva
        
        REGRA CRÍTICA: Não confirma sem pagamento autorizado!
        """
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        if reserva.statusReserva != "PENDENTE":
            raise ValueError("Apenas reservas pendentes podem ser confirmadas")
        
        # ⚠️ VALIDAÇÃO CRÍTICA: Verificar se há pagamento autorizado
        # NÃO CONFIRMAR RESERVA SEM PAGAMENTO!
        pagamentos = await self.db.pagamento.find_many(
            where={"reservaId": reserva_id}
        )
        
        # Verificar se existe pelo menos um pagamento aprovado/confirmado
        pagamentos_aprovados = [
            p for p in pagamentos 
            if p.statusPagamento in ("PAGO", "APROVADO")
        ]
        
        if not pagamentos_aprovados:
            raise ValueError(
                "❌ CONFIRMAÇÃO BLOQUEADA! Não é possível confirmar reserva sem pagamento autorizado. "
                "Realize o pagamento antes de confirmar a reserva."
            )
        
        # Verificar análise anti-fraude se houver
        from app.services.antifraude_service import AntifraaudeService
        analise = await AntifraaudeService.analisar_reserva(reserva_id)
        
        # Se risco ALTO ou CRÍTICO, adicionar delay de confirmação
        if analise.get("success") and analise.get("risco") in ["ALTO", "CRÍTICO"]:
            # Verificar se já passou o período de delay (24h)
            from datetime import timedelta
            from app.utils.datetime_utils import now_utc, to_utc
            
            reserva_created_utc = to_utc(reserva.createdAt)
            tempo_desde_criacao = now_utc() - reserva_created_utc
            
            if tempo_desde_criacao < timedelta(hours=24):
                horas_restantes = 24 - (tempo_desde_criacao.total_seconds() / 3600)
                raise ValueError(
                    f"⏳ CONFIRMAÇÃO EM ANÁLISE! Esta reserva possui risco {analise.get('risco')} "
                    f"e está em período de análise anti-fraude. "
                    f"Aguarde {horas_restantes:.1f} horas ou aprove manualmente. "
                    f"Score de risco: {analise.get('score')}"
                )
        
        # Atualizar status da reserva
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": "CONFIRMADA"
            }
        )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        
        # Criar hospedagem se não existir
        hospedagem_existente = await self.db.hospedagem.find_unique(
            where={"reservaId": reserva_id}
        )
        
        if not hospedagem_existente:
            await self.db.hospedagem.create(
                data={
                    "reservaId": reserva_id,
                    "statusHospedagem": "NAO_INICIADA"
                }
            )
            print(f"✅ Hospedagem criada para reserva {reserva_id}")
        
        # Gerar voucher automaticamente após confirmação
        try:
            from app.services.voucher_service import gerar_voucher
            voucher = await gerar_voucher(reserva_id)
            print(f"✅ Voucher gerado: {voucher.get('codigo')}")
        except Exception as e:
            print(f"⚠️ Erro ao gerar voucher: {e}")
        
        # Criar notificação de confirmação (comentado até corrigir)
        # await NotificationService.notificar_reserva_confirmada(updated_reserva)
        
        return self._serialize_reserva(updated_reserva)
    
    async def update(self, reserva_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar dados gerais da reserva"""
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        # Não permite editar reservas já finalizadas
        if reserva.statusReserva in ("CHECKED_OUT", "CANCELADO"):
            raise ValueError("Não é possível editar reservas finalizadas ou canceladas")
        
        # Mapear campos permitidos para atualização
        update_data = {}
        
        if "quarto_numero" in data:
            # Verificar se o novo quarto existe
            quarto = await self.db.quarto.find_unique(where={"numero": data["quarto_numero"]})
            if not quarto:
                raise ValueError("Quarto não encontrado")
            update_data["quartoNumero"] = data["quarto_numero"]
        
        if "tipo_suite" in data:
            update_data["tipoSuite"] = data["tipo_suite"]
        
        if "checkin_previsto" in data:
            update_data["checkinPrevisto"] = data["checkin_previsto"]
        
        if "checkout_previsto" in data:
            update_data["checkoutPrevisto"] = data["checkout_previsto"]
        
        if "valor_diaria" in data:
            pass
        
        if "num_diarias" in data:
            update_data["numDiarias"] = data["num_diarias"]

        if "tipo_suite" in data or "checkin_previsto" in data:
            suite_tipo = data.get("tipo_suite", reserva.tipoSuite)
            checkin_previsto = data.get("checkin_previsto", reserva.checkinPrevisto)
            update_data["valorDiaria"] = await self._obter_tarifa_diaria(suite_tipo, checkin_previsto)
        
        # Atualizar reserva
        await self.db.reserva.update(
            where={"id": reserva_id},
            data=update_data
        )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        return self._serialize_reserva(updated_reserva)
    
    def _serialize_reserva(self, reserva) -> Dict[str, Any]:
        """Serializar reserva para response com todos os campos"""
        # Calcular valor total
        valor_total = float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0.0
        
        # Serializar pagamentos para validação no frontend
        pagamentos = []
        if hasattr(reserva, 'pagamentos') and reserva.pagamentos:
            pagamentos = [
                {
                    "id": p.id,
                    "status": p.statusPagamento,
                    "valor": float(p.valor) if p.valor else 0.0,
                    "metodo": p.metodo,
                    "created_at": p.createdAt.isoformat() if p.createdAt else None
                } for p in reserva.pagamentos
            ]
        
        # Serializar hospedagem para validação de checkout
        hospedagem = None
        try:
            if hasattr(reserva, 'hospedagem') and reserva.hospedagem:
                hosp = reserva.hospedagem
                hospedagem = {
                    "id": getattr(hosp, 'id', None),
                    "status_hospedagem": getattr(hosp, 'statusHospedagem', None),
                    "data_checkin": getattr(hosp, 'checkinRealizadoEm', None),
                    "data_checkout": getattr(hosp, 'checkoutRealizadoEm', None),
                    "created_at": getattr(hosp, 'createdAt', None)
                }
        except Exception as e:
            print(f"DEBUG: Erro ao serializar hospedagem: {e}")
            hospedagem = None

        # Status da reserva (usar o valor real do banco)
        status_reserva = getattr(reserva, 'statusReserva', 'PENDENTE')
        
        return {
            "id": reserva.id,
            "codigo_reserva": reserva.codigoReserva,
            "cliente_id": reserva.clienteId,
            "cliente_nome": getattr(reserva, 'clienteNome', None),
            "quarto_numero": reserva.quartoNumero,
            "tipo_suite": reserva.tipoSuite,
            "checkin_previsto": reserva.checkinPrevisto.isoformat() if reserva.checkinPrevisto else None,
            "checkout_previsto": reserva.checkoutPrevisto.isoformat() if reserva.checkoutPrevisto else None,
            "checkin_realizado": reserva.checkinReal.isoformat() if hasattr(reserva, 'checkinReal') and reserva.checkinReal else None,
            "checkout_realizado": reserva.checkoutReal.isoformat() if hasattr(reserva, 'checkoutReal') and reserva.checkoutReal else None,
            "valor_diaria": float(reserva.valorDiaria) if reserva.valorDiaria else 0.0,
            "num_diarias": reserva.numDiarias,
            "valor_total": valor_total,
            "status": status_reserva,
            "pagamentos": pagamentos,
            "hospedagem": hospedagem,
            "created_at": reserva.createdAt.isoformat() if reserva.createdAt else None,
            "updated_at": reserva.updatedAt.isoformat() if hasattr(reserva, 'updatedAt') and reserva.updatedAt else None
        }