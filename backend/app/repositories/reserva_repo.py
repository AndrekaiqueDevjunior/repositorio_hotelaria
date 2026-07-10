from typing import Dict, Any, List
from datetime import datetime, date
from typing import Optional
from fastapi import HTTPException
from app.schemas.reserva_schema import ReservaCreate, ReservaResponse
from app.repositories.tarifa_suite_repo import TarifaSuiteRepository
from app.core.validators import ReservaValidator
from prisma import Client
from prisma.errors import UniqueViolationError
from app.services.notification_service import NotificationService
from app.services.whatsapp_service import get_whatsapp_service
import secrets
import re

STATUS_RESERVA_PENDENTES = {"PENDENTE", "PENDENTE_PAGAMENTO", "AGUARDANDO_PAGAMENTO"}
STATUS_RESERVA_HOSPEDADO = {"HOSPEDADO", "CHECKIN_REALIZADO", "CHECKED_IN"}
STATUS_RESERVA_FINALIZADO = {"CHECKED_OUT", "CHECKOUT_REALIZADO", "FINALIZADA"}
STATUS_RESERVA_CANCELADO = {"CANCELADO", "CANCELADA", "NO_SHOW"}
STATUS_PAGAMENTO_APROVADO = {"PAGO", "APROVADO", "CONFIRMADO", "CAPTURED", "AUTHORIZED"}

class ReservaRepository:
    def __init__(self, db: Client):
        self.db = db

    def _formatar_data_curta(self, valor) -> str:
        if not valor:
            return "-"
        try:
            return valor.strftime("%d/%m/%Y, %H:%M:%S")
        except Exception:
            return str(valor)[:10]

    async def _notificar_whatsapp_reserva(self, reserva, evento: str, detalhe: str = None) -> None:
        try:
            whatsapp_service = get_whatsapp_service()
            # Valor comunicado = valor final devido (com desconto de cupom).
            valor_total = await self._obter_valor_total_devido(
                getattr(reserva, "id", 0), reserva
            )
            cliente = getattr(reserva, "cliente", None)
            await whatsapp_service.enviar_notificacao_evento_reserva(
                evento=evento,
                codigo_reserva=getattr(reserva, "codigoReserva", None) or f"RES-{getattr(reserva, 'id', '')}",
                cliente_nome=getattr(reserva, "clienteNome", None) or "Cliente nao identificado",
                quarto_numero=getattr(reserva, "quartoNumero", None) or "N/A",
                checkin_previsto=self._formatar_data_curta(getattr(reserva, "checkinPrevisto", None)),
                checkout_previsto=self._formatar_data_curta(getattr(reserva, "checkoutPrevisto", None)),
                valor_total=valor_total,
                status=getattr(reserva, "statusReserva", None) or "-",
                detalhe=detalhe,
                reserva_id=getattr(reserva, "id", None),
                cliente_telefone=(
                    getattr(reserva, "telefoneContato", None)
                    or getattr(cliente, "telefone", None)
                ),
                cliente_email=(
                    getattr(reserva, "emailContato", None)
                    or getattr(cliente, "email", None)
                ),
                cliente_documento=getattr(cliente, "documento", None),
                responsavel_nome=getattr(reserva, "responsavelNome", None),
                tipo_suite=getattr(reserva, "tipoSuite", None),
                num_diarias=getattr(reserva, "numDiarias", None),
                valor_diaria=float(getattr(reserva, "valorDiaria", 0) or 0),
                origem=getattr(reserva, "origem", None),
                forma_pagamento=getattr(reserva, "formaPagamento", None),
                observacoes=getattr(reserva, "observacoes", None),
                cliente_id=getattr(reserva, "clienteId", None),
                created_at=self._formatar_data_curta(getattr(reserva, "createdAt", None)),
                updated_at=self._formatar_data_curta(getattr(reserva, "updatedAt", None)),
                criado_por="-",
            )
        except Exception as whatsapp_error:
            print(f"[WHATSAPP] Erro ao notificar reserva ({evento}): {whatsapp_error}")

    async def notificar_whatsapp_por_id(self, reserva_id: int, evento: str = "criada", detalhe: str = None) -> None:
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include=self._default_include(),
        )
        if reserva:
            await self._notificar_whatsapp_reserva(reserva, evento, detalhe=detalhe)

    def _default_include(self) -> Dict[str, Any]:
        return {
            "cliente": True,
            "pagamentos": True,
            "hospedagem": True,
            "cupomUso": {"include": {"cupom": True}},
        }

    def _calcular_valor_total_model(self, reserva) -> float:
        valor_total_salvo = getattr(reserva, "valorTotal", None)
        if valor_total_salvo is not None:
            return float(valor_total_salvo)
        return float(getattr(reserva, "valorDiaria", 0) or 0) * int(getattr(reserva, "numDiarias", 0) or 0)

    async def _obter_valor_total_devido(self, reserva_id: int, reserva=None) -> float:
        valor_bruto = self._calcular_valor_total_model(reserva) if reserva else 0.0
        cupom_uso = await self.db.cupomuso.find_first(where={"reservaId": reserva_id})
        if cupom_uso:
            return float(getattr(cupom_uso, "valorFinal", None) or valor_bruto)
        return valor_bruto

    def _normalizar_valor_texto(self, valor: Any) -> Optional[str]:
        if valor is None:
            return None
        valor_texto = str(valor).strip()
        return valor_texto or None

    def _coerce_datetime(self, valor: Any) -> Any:
        if not isinstance(valor, str):
            return valor
        valor_limpo = valor.strip()
        if not valor_limpo:
            return valor
        try:
            return datetime.fromisoformat(valor_limpo.replace("Z", "+00:00"))
        except ValueError:
            return valor

    async def _obter_tarifa_diaria(self, suite_tipo: str, checkin_previsto: datetime) -> tuple:
        tarifa_repo = TarifaSuiteRepository(self.db)

        suite_tipo_norm = suite_tipo.value if hasattr(suite_tipo, "value") else str(suite_tipo)

        if not checkin_previsto:
            raise ValueError("Data de check-in invÃ¡lida para buscar tarifa")

        data_ref = checkin_previsto.date() if isinstance(checkin_previsto, datetime) else checkin_previsto
        tarifa = await tarifa_repo.get_tarifa_ativa(suite_tipo_norm, data_ref)

        if not tarifa:
            raise ValueError(
                f"Tarifa nÃ£o cadastrada para a suÃ­te {suite_tipo_norm} na data {data_ref}. Cadastre uma tarifa antes de criar a reserva."
            )

        return float(tarifa.get("preco_diaria", 0.0)), tarifa.get("id")
    
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
        
        # Filtro de busca (nome cliente ou nÃºmero quarto)
        if search:
            search_digits = re.sub(r"\D", "", search or "")
            where_conditions["OR"] = [
                {"clienteNome": {"contains": search, "mode": "insensitive"}},
                {"quartoNumero": {"contains": search, "mode": "insensitive"}},
                {"codigoReserva": {"contains": search, "mode": "insensitive"}},
                {"telefoneContato": {"contains": search_digits or search, "mode": "insensitive"}},
                {"emailContato": {"contains": search, "mode": "insensitive"}},
                {"cliente": {"is": {"documento": {"contains": search_digits or search, "mode": "insensitive"}}}},
                {"cliente": {"is": {"telefone": {"contains": search_digits or search, "mode": "insensitive"}}}},
                {"cliente": {"is": {"email": {"contains": search, "mode": "insensitive"}}}},
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
        
        # Buscar total de registros (para paginaÃ§Ã£o)
        total = await self.db.reserva.count(where=where_conditions if where_conditions else None)
        
        # Processar ordenaÃ§Ã£o
        order_clause = {"id": "desc"}  # Ordem padrÃ£o
        
        if order_by:
            # Formato esperado: "campo:ordem" (ex: "data_criacao:desc")
            if ":" in order_by:
                field, direction = order_by.split(":", 1)
                order_clause = {field: direction.lower()}
        
        # Buscar registros com paginaÃ§Ã£o - P0-002: Incluir pagamentos e hospedagem
        registros = await self.db.reserva.find_many(
            where=where_conditions if where_conditions else None,
            include=self._default_include(),
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
    
    async def create(
        self,
        reserva: ReservaCreate,
        notificar: bool = True,
        criado_por_funcionario_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Criar nova reserva com validaÃ§Ãµes"""
        # Verificar se cliente existe
        cliente = await self.db.cliente.find_unique(where={"id": reserva.cliente_id})
        if not cliente:
            raise ValueError("Cliente nÃ£o encontrado")

        # VALIDAÃ‡ÃƒO: Verificar se cliente jÃ¡ tem reservas ativas
        reservas_ativas = await self.db.reserva.find_many(
            where={
                "clienteId": reserva.cliente_id,
                "statusReserva": {"in": ["PENDENTE", "CONFIRMADA", "HOSPEDADO"]}
            }
        )
        
        if reservas_ativas:
            # Verificar se hÃ¡ conflito de datas
            for reserva_ativa in reservas_ativas:
                # Se a reserva ativa estiver no mesmo perÃ­odo ou sobrepor o novo perÃ­odo
                if (reserva.checkin_previsto.date() <= reserva_ativa.checkoutPrevisto.date() and 
                    reserva.checkout_previsto.date() >= reserva_ativa.checkinPrevisto.date()):
                    
                    # Calcular dias restantes da reserva ativa
                    from app.utils.datetime_utils import to_utc, now_utc
                    checkout_previsto_utc = to_utc(reserva_ativa.checkinPrevisto)
                    dias_restantes = (checkout_previsto_utc.date() - now_utc().date()).days
                    
                    msg_erro = f"âŒ CLIENTE JÃ POSSUI RESERVA ATIVA!"
                    msg_erro += f"\n\nðŸ“‹ Reserva existente: {reserva_ativa.codigoReserva}"
                    msg_erro += f"\n  â€¢ Quarto: {reserva_ativa.quartoNumero}"
                    msg_erro += f"\n  â€¢ Check-in: {reserva_ativa.checkinPrevisto.strftime('%d/%m/%Y')}"
                    msg_erro += f"\n  â€¢ Check-out: {reserva_ativa.checkoutPrevisto.strftime('%d/%m/%Y')}"
                    msg_erro += f"\n  â€¢ Status: {reserva_ativa.statusReserva}"
                    
                    if dias_restantes > 0:
                        msg_erro += f"\n\nâš ï¸ Para fazer uma nova reserva, vocÃª deve:"
                        msg_erro += f"\n  1. Aguardar o check-in da reserva atual"
                        msg_erro += f"\n  2. Fazer check-out da reserva atual"
                        msg_erro += f"\n  3. Cancelar a reserva atual (se permitido)"
                    else:
                        msg_erro += f"\n\nðŸ“ž Entre em contato com a recepÃ§Ã£o para assistÃªncia."
                    
                    raise ValueError(msg_erro)

        valor_diaria, tarifa_suite_id = await self._obter_tarifa_diaria(
            reserva.tipo_suite,
            reserva.checkin_previsto,
        )

        quarto = await self.db.quarto.find_unique(where={"numero": reserva.quarto_numero})
        if not quarto:
            raise ValueError("Quarto nÃ£o encontrado")
        
        if quarto.status in ("BLOQUEADO", "MANUTENCAO"):
            raise ValueError(f"âŒ Quarto {reserva.quarto_numero} estÃ¡ {quarto.status.lower()} e nÃ£o pode ser reservado")
        
        # VALIDAÃ‡ÃƒO CRÃTICA: Verificar disponibilidade usando DisponibilidadeService
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
            
            msg_erro = f"âŒ QUARTO INDISPONÃVEL! {resultado['motivo']}"
            
            if resultado["conflitos"]:
                msg_erro += f"\n\nðŸ“‹ Conflitos encontrados:"
                for conflito in resultado["conflitos"]:
                    msg_erro += f"\n  â€¢ Reserva {conflito['codigo']} - {conflito['cliente']}"
                    msg_erro += f"\n    Check-in: {conflito['checkin'][:10]} | Check-out: {conflito['checkout'][:10]}"
            
            if alternativas:
                msg_erro += f"\n\nðŸ’¡ Quartos {reserva.tipo_suite} disponÃ­veis no perÃ­odo:"
                for alt in alternativas:
                    msg_erro += f"\n  â€¢ Quarto {alt['numero']}"
            else:
                msg_erro += f"\n\nâš ï¸ Nenhum quarto {reserva.tipo_suite} disponÃ­vel neste perÃ­odo"
            
            raise ValueError(msg_erro)
        
        from app.utils.datetime_utils import now_utc
        
        # Gerar cÃ³digo Ãºnico com retry (evita colisÃµes em concorrÃªncia)
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
                        "valorTotal": reserva.valor_total,
                        "numDiarias": reserva.num_diarias,
                        "statusReserva": "PENDENTE",
                        "origem": self._normalizar_valor_texto(reserva.origem) or "PARTICULAR",
                        "responsavelNome": self._normalizar_valor_texto(reserva.responsavel_nome),
                        "formaPagamento": self._normalizar_valor_texto(reserva.forma_pagamento),
                        "observacoes": self._normalizar_valor_texto(reserva.observacoes),
                        "telefoneContato": self._normalizar_valor_texto(reserva.telefone_contato),
                        "emailContato": self._normalizar_valor_texto(reserva.email_contato),
                        "criadoPorFuncionarioId": criado_por_funcionario_id,
                        "tarifaSuiteId": tarifa_suite_id,
                    }
                )
                break
            except UniqueViolationError:
                nova_reserva = None
            except Exception as exc:
                # Corrida real de disponibilidade: dois processos passaram na
                # checagem, mas a constraint de exclusao (migration 016) so
                # deixa um vencer. Sem este tratamento o perdedor recebia 500.
                if "reservas_quarto_periodo_no_overlap" in str(exc):
                    raise ValueError(
                        f"Quarto {reserva.quarto_numero} acabou de ser reservado por outra "
                        f"pessoa para este periodo. Atualize a disponibilidade e escolha "
                        f"outro quarto ou periodo."
                    )
                raise

        if not nova_reserva:
            raise ValueError("NÃ£o foi possÃ­vel gerar um cÃ³digo de reserva Ãºnico")
        
        # Criar notificaÃ§Ã£o de nova reserva
        if notificar:
            reserva_notificacao = await self.db.reserva.find_unique(
                where={"id": nova_reserva.id},
                include=self._default_include(),
            )
            # O alerta WhatsApp para o admin ja acontece dentro de
            # notificar_nova_reserva (garantido para todo caller, nao so este).
            await NotificationService.notificar_nova_reserva(self.db, reserva_notificacao or nova_reserva)

        try:
            from app.services.indicacao_service import IndicacaoService
            await IndicacaoService(self.db).registrar_reserva_realizada(nova_reserva.id)
        except Exception as e:
            print(f"[CONVITE REAL] Erro ao registrar reserva realizada: {e}")

        return self._serialize_reserva(nova_reserva)
    
    async def get_by_id(self, reserva_id: int) -> Dict[str, Any]:
        """Obter reserva por ID com todos os dados relacionados"""
        # Buscar reserva com pagamentos incluÃ­dos
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include=self._default_include(),
        )
        if not reserva:
            raise ValueError("Reserva nÃ£o encontrada")
        return self._serialize_reserva(reserva)

    async def get_by_codigo(self, codigo_reserva: str) -> Dict[str, Any]:
        """Obter reserva por cÃ³digo (codigoReserva) com dados relacionados"""
        codigo_upper = (codigo_reserva or "").upper().strip()
        if not codigo_upper:
            raise ValueError("CÃ³digo de reserva invÃ¡lido")

        reserva = await self.db.reserva.find_first(
            where={"codigoReserva": codigo_upper},
            include=self._default_include(),
        )

        if not reserva:
            raise ValueError("Reserva nÃ£o encontrada")

        return self._serialize_reserva(reserva)
    
    async def checkin(self, reserva_id: int) -> Dict[str, Any]:
        """Realizar check-in da reserva"""
        from app.utils.datetime_utils import now_utc
        
        # P1-001: Buscar reserva com pagamentos para validaÃ§Ã£o
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"pagamentos": True}
        )
        if not reserva:
            raise ValueError("Reserva nÃ£o encontrada")
        
        # P1-001: VALIDAÃ‡ÃƒO 1 - Status deve ser CONFIRMADA (nÃ£o mais PENDENTE)
        if reserva.statusReserva != "CONFIRMADA":
            raise ValueError(f"Check-in requer status CONFIRMADA. Status atual: {reserva.statusReserva}")
        
        # P1-001: VALIDAÃ‡ÃƒO 2 - Deve ter pagamento aprovado
        pagamentos_aprovados = [
            p for p in reserva.pagamentos
            if p.statusPagamento in STATUS_PAGAMENTO_APROVADO
        ]
        
        if not pagamentos_aprovados:
            raise ValueError("Check-in requer pagamento aprovado. Realize o pagamento antes do check-in.")
        
        # P1-001: VALIDAÃ‡ÃƒO 3 - Verificar se quarto estÃ¡ livre
        quarto = await self.db.quarto.find_unique(where={"numero": reserva.quartoNumero})
        if quarto and quarto.status != "LIVRE":
            raise ValueError(f"Quarto {reserva.quartoNumero} nÃ£o estÃ¡ disponÃ­vel (status: {quarto.status})")
        
        # Atualizar status da reserva
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": "HOSPEDADO",
                "checkinReal": now_utc()
            }
        )
        
        # Atualizar status do quarto
        quarto_numero = (reserva.quartoNumero or "").strip()
        await self.db.quarto.update(
            where={"numero": quarto_numero},
            data={"status": "OCUPADO"}
        )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include=self._default_include())
        
        # Criar notificaÃ§Ã£o de check-in
        await NotificationService.notificar_checkin_realizado(self.db, updated_reserva)
        await self._notificar_whatsapp_reserva(updated_reserva, "check-in realizado")
        
        return self._serialize_reserva(updated_reserva)
    
    async def checkout(self, reserva_id: int) -> Dict[str, Any]:
        """Realizar check-out da reserva"""
        from app.utils.datetime_utils import now_utc
        
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva nÃ£o encontrada")
        
        # Verificar status da reserva
        if reserva.statusReserva not in ("HOSPEDADO", "CHECKIN_REALIZADO", "CHECKED_IN"):
            raise ValueError("Apenas reservas hospedadas podem fazer check-out")
        
        # VALIDAÃ‡ÃƒO CRÃTICA: Verificar se hÃ¡ pagamentos pendentes
        # Cliente nÃ£o pode sair sem pagar!
        pagamentos = await self.db.pagamento.find_many(
            where={"reservaId": reserva_id}
        )
        
        valor_total_reserva = await self._obter_valor_total_devido(reserva_id, reserva)
        
        # Calcular total pago (apenas pagamentos aprovados)
        total_pago = sum(
            float(p.valor) for p in pagamentos 
            if p.statusPagamento in STATUS_PAGAMENTO_APROVADO
        )
        
        # Calcular saldo pendente
        saldo_pendente = valor_total_reserva - total_pago
        
        # BLOQUEIO: NÃ£o permite check-out se houver dÃ­vida
        if saldo_pendente > 0.01:  # TolerÃ¢ncia de 1 centavo para arredondamento
            raise ValueError(
                f"âŒ CHECK-OUT BLOQUEADO! Cliente possui saldo pendente de R$ {saldo_pendente:.2f}. "
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
        quarto_numero = (reserva.quartoNumero or "").strip()
        await self.db.quarto.update(
            where={"numero": quarto_numero},
            data={"status": "LIVRE"}
        )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include=self._default_include())
        
        # Creditar pontos automaticamente para o cliente (idempotente)
        try:
            from app.services.pontos_checkout_service import (
                creditar_bonus_cupom_no_checkout,
                creditar_bonus_promo_primeiros_no_checkout,
                creditar_rp_no_checkout,
            )

            resultado_pontos = await creditar_rp_no_checkout(
                self.db,
                reserva_id=reserva_id,
                funcionario_id=None,
                checkout_datetime=getattr(updated_reserva, "checkoutReal", None),
            )

            pontos_ganhos = int(resultado_pontos.get("pontos", 0) or 0) if resultado_pontos.get("creditado") else 0
            resultado_bonus = await creditar_bonus_cupom_no_checkout(
                self.db,
                reserva_id=reserva_id,
                funcionario_id=None,
            )
            pontos_bonus_cupom = int(resultado_bonus.get("pontos", 0) or 0) if resultado_bonus.get("creditado") else 0
            resultado_promo = await creditar_bonus_promo_primeiros_no_checkout(
                self.db,
                reserva_id=reserva_id,
                funcionario_id=None,
            )
            pontos_bonus_promo = int(resultado_promo.get("pontos", 0) or 0) if resultado_promo.get("creditado") else 0
        except Exception as e:
            pontos_ganhos = 0
            pontos_bonus_cupom = 0
            pontos_bonus_promo = 0
            print(f"[CHECKOUT] Erro ao creditar pontos: {e}")

        pontos_indicacao = 0
        try:
            from app.services.indicacao_service import IndicacaoService

            resultado_indicacao = await IndicacaoService(self.db).processar_credito_indicacao_apos_checkout(
                reserva_id=reserva_id,
                funcionario_id=None,
            )
            pontos_indicacao = (
                int(resultado_indicacao.get("pontos", 0) or 0)
                if resultado_indicacao.get("creditado")
                else 0
            )
            if pontos_indicacao:
                print(f"[CONVITE REAL] +{pontos_indicacao} pontos creditados por indicacao")
            elif resultado_indicacao.get("motivo"):
                print(f"[CONVITE REAL] Sem credito de indicacao: {resultado_indicacao.get('motivo')}")
        except Exception as e:
            print(f"[CONVITE REAL] Erro ao processar credito de indicacao: {e}")
        
        # Criar notificaÃ§Ã£o de check-out
        await NotificationService.notificar_checkout_realizado(self.db, updated_reserva)
        await self._notificar_whatsapp_reserva(
            updated_reserva,
            "check-out realizado",
            detalhe=(
                f"Pontos ganhos: {pontos_ganhos or 0} | "
                f"Bonus cupom: {pontos_bonus_cupom or 0} | "
                f"Bonus promo: {pontos_bonus_promo or 0} | "
                f"Convite Real: {pontos_indicacao or 0}"
            )
        )

        # Retornar reserva com informaÃ§Ãµes de pontos
        resultado = self._serialize_reserva(updated_reserva)
        resultado["pontos_ganhos"] = pontos_ganhos if pontos_ganhos > 0 else 0
        resultado["pontos_bonus_cupom"] = pontos_bonus_cupom if pontos_bonus_cupom > 0 else 0
        resultado["pontos_bonus_promo"] = pontos_bonus_promo if pontos_bonus_promo > 0 else 0
        resultado["pontos_convite_real"] = pontos_indicacao if pontos_indicacao > 0 else 0
        
        return resultado
    
    async def cancelar(self, reserva_id: int) -> Dict[str, Any]:
        """
        Cancelar reserva com sistema de estornos automÃ¡ticos
        
        RES-003 FIX: Processa estornos automaticamente quando possÃ­vel
        """
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva nÃ£o encontrada")
        
        if reserva.statusReserva not in STATUS_RESERVA_PENDENTES | {"CONFIRMADA"} | STATUS_RESERVA_HOSPEDADO:
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
                        # Verificar se pode estornar (prazo, mÃ©todo, etc.)
                        pode_estornar = await self._pode_processar_estorno(pagamento)
                        
                        if pode_estornar["permitido"]:
                            # Processar estorno automÃ¡tico
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
                            # Adicionar Ã  lista de estornos manuais
                            estornos_pendentes.append({
                                "pagamento_id": pagamento.id,
                                "valor": float(pagamento.valor),
                                "metodo": pagamento.metodo,
                                "motivo": pode_estornar["motivo"]
                            })
                            
                    except Exception as e:
                        print(f"âš ï¸ [RES-003] Erro ao processar estorno do pagamento {pagamento.id}: {e}")
                        estornos_pendentes.append({
                            "pagamento_id": pagamento.id,
                            "valor": float(pagamento.valor),
                            "metodo": pagamento.metodo,
                            "motivo": f"Erro no processamento: {str(e)}"
                        })
                        
        except Exception as e:
            print(f"âš ï¸ [RES-003] Erro geral no sistema de estornos: {e}")
            # Continua o cancelamento mesmo com erro nos estornos
        
        # Atualizar status da reserva
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "statusReserva": "CANCELADO"
            }
        )

        # Pontos agora sao creditados na hora do checkout (nao mais so apos
        # 48h), entao um cancelamento pode acontecer depois que os pontos ja
        # viraram saldo disponivel -- estorna automaticamente. Nunca bloqueia
        # o cancelamento se o estorno falhar (ex: cliente ja resgatou).
        estorno_pontos = {"success": True, "estornado": False}
        try:
            from app.services.pontos_checkout_service import estornar_pontos_cancelamento
            estorno_pontos = await estornar_pontos_cancelamento(self.db, reserva_id)
        except Exception as e:
            print(f"[PONTOS ESTORNO] Erro ao estornar pontos da reserva {reserva_id} cancelada: {e}")

        # CORREÃ‡ÃƒO CRÃTICA: Liberar quarto independente do status da reserva
        # Se estava HOSPEDADO, CONFIRMADA ou qualquer outro status ativo, liberar o quarto
        if reserva.statusReserva in STATUS_RESERVA_HOSPEDADO | {"CONFIRMADA"} | STATUS_RESERVA_PENDENTES:
            # Verificar se o quarto realmente precisa ser liberado (nÃ£o estÃ¡ LIVRE)
            quarto_numero = (reserva.quartoNumero or "").strip()
            quarto = await self.db.quarto.find_unique(where={"numero": quarto_numero})
            if quarto and quarto.status != "LIVRE":
                await self.db.quarto.update(
                    where={"numero": quarto_numero},
                    data={"status": "LIVRE"}
                )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include=self._default_include())
        
        # RES-003 FIX: Notificar sobre estornos processados e pendentes
        if estornos_processados or estornos_pendentes:
            await self._notificar_estornos(reserva_id, estornos_processados, estornos_pendentes)
        
        # Criar notificaÃ§Ã£o de cancelamento
        await NotificationService.notificar_reserva_cancelada(self.db, updated_reserva)
        await self._notificar_whatsapp_reserva(
            updated_reserva,
            "cancelada",
            detalhe=(
                f"Estornos processados: {len(estornos_processados)} | "
                f"Estornos pendentes: {len(estornos_pendentes)}"
            )
        )
        
        # RES-003 FIX: Incluir informaÃ§Ãµes de estorno no retorno
        resultado = self._serialize_reserva(updated_reserva)
        resultado["estornos"] = {
            "processados": estornos_processados,
            "pendentes": estornos_pendentes,
            "total_estornado": sum(e["valor"] for e in estornos_processados),
            "total_pendente": sum(e["valor"] for e in estornos_pendentes)
        }
        resultado["estorno_pontos"] = estorno_pontos

        return resultado
    
    async def _pode_processar_estorno(self, pagamento) -> Dict[str, Any]:
        """
        RES-003 FIX: Verificar se pagamento pode ser estornado automaticamente
        
        Regras de negÃ³cio para estorno:
        - CartÃ£o: atÃ© 120 dias apÃ³s pagamento
        - PIX: atÃ© 90 dias apÃ³s pagamento  
        - Dinheiro: nÃ£o permite estorno automÃ¡tico
        """
        from datetime import timedelta
        from app.utils.datetime_utils import now_utc, to_utc
        
        try:
            # Verificar idade do pagamento
            pagamento_created_utc = to_utc(pagamento.createdAt)
            idade_pagamento = now_utc() - pagamento_created_utc
            
            # Regras por mÃ©todo de pagamento
            if pagamento.metodo in ["credit_card", "debit_card"]:
                if idade_pagamento.days > 120:
                    return {
                        "permitido": False,
                        "motivo": f"Pagamento com cartÃ£o muito antigo ({idade_pagamento.days} dias). Limite: 120 dias."
                    }
                return {"permitido": True, "motivo": "CartÃ£o dentro do prazo"}
                
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
                    "motivo": "Pagamentos em dinheiro requerem estorno manual na recepÃ§Ã£o"
                }
                
            else:
                return {
                    "permitido": False,
                    "motivo": f"MÃ©todo {pagamento.metodo} nÃ£o suporta estorno automÃ¡tico"
                }
                
        except Exception as e:
            return {
                "permitido": False,
                "motivo": f"Erro ao validar estorno: {str(e)}"
            }
    
    async def _processar_estorno_automatico(self, pagamento) -> Dict[str, Any]:
        """
        RES-003 FIX: Processar estorno automÃ¡tico via gateway
        """
        try:
            # Integrar com gateway de pagamento (Cielo, etc.)
            from app.services.cielo_service import CieloAPI
            
            cielo_api = CieloAPI()
            
            # Processar estorno baseado no mÃ©todo
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
                    "erro": f"MÃ©todo {pagamento.metodo} nÃ£o implementado para estorno automÃ¡tico"
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
            # NotificaÃ§Ã£o para equipe financeira
            total_estornado = sum(e["valor"] for e in estornos_processados)
            total_pendente = sum(e["valor"] for e in estornos_pendentes)
            
            mensagem_notificacao = f"""
ðŸ”” CANCELAMENTO COM ESTORNOS - Reserva #{reserva_id}

âœ… ESTORNOS PROCESSADOS AUTOMATICAMENTE:
"""
            
            for estorno in estornos_processados:
                mensagem_notificacao += f"   â€¢ R$ {estorno['valor']:.2f} ({estorno['metodo']})\n"
                
            if estornos_pendentes:
                mensagem_notificacao += f"""
âš ï¸ ESTORNOS PENDENTES (AÃ‡ÃƒO MANUAL NECESSÃRIA):
"""
                for estorno in estornos_pendentes:
                    mensagem_notificacao += f"   â€¢ R$ {estorno['valor']:.2f} ({estorno['metodo']}) - {estorno['motivo']}\n"
            
            mensagem_notificacao += f"""
ðŸ’° RESUMO:
   â€¢ Total estornado: R$ {total_estornado:.2f}
   â€¢ Total pendente: R$ {total_pendente:.2f}
"""

            # Enviar notificaÃ§Ã£o (implementar conforme sistema de notificaÃ§Ãµes)
            print(f"[RES-003] {mensagem_notificacao}")
            
            # TODO: Integrar com sistema de notificaÃ§Ãµes (email, Slack, etc.)
            
        except Exception as e:
            print(f"âš ï¸ [RES-003] Erro ao enviar notificaÃ§Ãµes de estorno: {e}")
    
    async def confirmar(self, reserva_id: int) -> Dict[str, Any]:
        """
        Confirmar reserva
        
        REGRA CRÃTICA: NÃ£o confirma sem pagamento autorizado!
        """
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva nÃ£o encontrada")
        
        if reserva.statusReserva not in STATUS_RESERVA_PENDENTES:
            raise ValueError("Apenas reservas pendentes podem ser confirmadas")
        
        # âš ï¸ VALIDAÃ‡ÃƒO CRÃTICA: Verificar se hÃ¡ pagamento autorizado
        # NÃƒO CONFIRMAR RESERVA SEM PAGAMENTO!
        pagamentos = await self.db.pagamento.find_many(
            where={"reservaId": reserva_id}
        )
        
        # Verificar se existe pelo menos um pagamento aprovado/confirmado
        pagamentos_aprovados = [
            p for p in pagamentos 
            if p.statusPagamento in STATUS_PAGAMENTO_APROVADO
        ]
        
        if not pagamentos_aprovados:
            raise ValueError(
                "âŒ CONFIRMAÃ‡ÃƒO BLOQUEADA! NÃ£o Ã© possÃ­vel confirmar reserva sem pagamento autorizado. "
                "Realize o pagamento antes de confirmar a reserva."
            )
        
        # Verificar anÃ¡lise anti-fraude se houver
        from app.services.antifraude_service import AntifraaudeService
        analise = await AntifraaudeService.analisar_reserva(reserva_id)
        
        # Se risco ALTO ou CRÃTICO, adicionar delay de confirmaÃ§Ã£o
        if analise.get("success") and analise.get("risco") in ["ALTO", "CRÃTICO"]:
            # Verificar se jÃ¡ passou o perÃ­odo de delay (24h)
            from datetime import timedelta
            from app.utils.datetime_utils import now_utc, to_utc
            
            reserva_created_utc = to_utc(reserva.createdAt)
            tempo_desde_criacao = now_utc() - reserva_created_utc
            
            if tempo_desde_criacao < timedelta(hours=24):
                horas_restantes = 24 - (tempo_desde_criacao.total_seconds() / 3600)
                raise ValueError(
                    f"â³ CONFIRMAÃ‡ÃƒO EM ANÃLISE! Esta reserva possui risco {analise.get('risco')} "
                    f"e estÃ¡ em perÃ­odo de anÃ¡lise anti-fraude. "
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
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include=self._default_include())
        
        # Criar hospedagem se nÃ£o existir
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
            print(f"âœ… Hospedagem criada para reserva {reserva_id}")
        
        # Gerar voucher automaticamente apÃ³s confirmaÃ§Ã£o
        try:
            from app.services.voucher_service import gerar_voucher
            voucher = await gerar_voucher(reserva_id)
            print(f"âœ… Voucher gerado: {voucher.get('codigo')}")
        except Exception as e:
            print(f"âš ï¸ Erro ao gerar voucher: {e}")
        
        # Criar notificaÃ§Ã£o de confirmaÃ§Ã£o (comentado atÃ© corrigir)
        # await NotificationService.notificar_reserva_confirmada(updated_reserva)
        await self._notificar_whatsapp_reserva(updated_reserva, "confirmada")
        
        return self._serialize_reserva(updated_reserva)
    
    async def update(self, reserva_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar dados gerais da reserva"""
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva nÃ£o encontrada")
        
        # NÃ£o permite editar reservas jÃ¡ finalizadas
        if reserva.statusReserva in STATUS_RESERVA_FINALIZADO | STATUS_RESERVA_CANCELADO:
            raise ValueError("NÃ£o Ã© possÃ­vel editar reservas finalizadas ou canceladas")

        data = dict(data or {})
        for campo_data in ("checkin_previsto", "checkout_previsto"):
            if campo_data in data:
                data[campo_data] = self._coerce_datetime(data[campo_data])
        
        # Mapear campos permitidos para atualizaÃ§Ã£o
        update_data = {}
        
        if "quarto_numero" in data:
            # Verificar se o novo quarto existe
            quarto = await self.db.quarto.find_unique(where={"numero": data["quarto_numero"]})
            if not quarto:
                raise ValueError("Quarto nÃ£o encontrado")
            update_data["quartoNumero"] = data["quarto_numero"]
            update_data["quartoId"] = quarto.id
        
        if "tipo_suite" in data:
            update_data["tipoSuite"] = data["tipo_suite"]
        
        if "checkin_previsto" in data:
            update_data["checkinPrevisto"] = data["checkin_previsto"]
        
        if "checkout_previsto" in data:
            update_data["checkoutPrevisto"] = data["checkout_previsto"]
        
        if "valor_diaria" in data and data["valor_diaria"] is not None:
            update_data["valorDiaria"] = float(data["valor_diaria"])

        if "valor_total" in data:
            update_data["valorTotal"] = float(data["valor_total"]) if data["valor_total"] is not None else None
        
        if "num_diarias" in data:
            update_data["numDiarias"] = data["num_diarias"]

        if "tipo_suite" in data or "checkin_previsto" in data:
            suite_tipo = data.get("tipo_suite", reserva.tipoSuite)
            checkin_previsto = data.get("checkin_previsto", reserva.checkinPrevisto)
            if "valor_diaria" not in data:
                nova_diaria, nova_tarifa_id = await self._obter_tarifa_diaria(suite_tipo, checkin_previsto)
                update_data["valorDiaria"] = nova_diaria
                update_data["tarifaSuiteId"] = nova_tarifa_id

        campos_texto = {
            "origem": "origem",
            "responsavel_nome": "responsavelNome",
            "forma_pagamento": "formaPagamento",
            "observacoes": "observacoes",
            "telefone_contato": "telefoneContato",
            "email_contato": "emailContato",
        }
        for campo_api, campo_banco in campos_texto.items():
            if campo_api in data:
                update_data[campo_banco] = self._normalizar_valor_texto(data[campo_api])

        novo_quarto_numero = update_data.get("quartoNumero", reserva.quartoNumero)
        novo_checkin = update_data.get("checkinPrevisto", reserva.checkinPrevisto)
        novo_checkout = update_data.get("checkoutPrevisto", reserva.checkoutPrevisto)

        if novo_checkin and novo_checkout and novo_checkout <= novo_checkin:
            raise ValueError("Data de check-out deve ser posterior ao check-in")

        if any(campo in update_data for campo in ("quartoNumero", "checkinPrevisto", "checkoutPrevisto")):
            from app.services.disponibilidade_service import DisponibilidadeService
            disponibilidade = await DisponibilidadeService(self.db).verificar_disponibilidade(
                novo_quarto_numero,
                novo_checkin,
                novo_checkout,
                reserva_id_excluir=reserva_id,
            )
            if not disponibilidade.get("disponivel"):
                raise ValueError(disponibilidade.get("motivo") or "Quarto nÃ£o disponÃ­vel para o perÃ­odo")
        
        quarto_antigo = getattr(reserva, "quartoNumero", None)

        # Atualizar reserva
        try:
            await self.db.reserva.update(
                where={"id": reserva_id},
                data=update_data
            )
        except Exception as exc:
            # Mesma protecao do create: a constraint de exclusao e o arbitro
            # final quando a troca de quarto/datas colide com outra reserva.
            if "reservas_quarto_periodo_no_overlap" in str(exc):
                raise ValueError(
                    "O quarto/periodo escolhido acabou de ser ocupado por outra reserva. "
                    "Atualize a disponibilidade e tente novamente."
                )
            raise
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include=self._default_include())
        if update_data:
            if "quartoNumero" in update_data:
                detalhe = f"Quarto alterado de {quarto_antigo} para {update_data['quartoNumero']}"
                await self._notificar_whatsapp_reserva(updated_reserva, "quarto alterado", detalhe=detalhe)
            else:
                await self._notificar_whatsapp_reserva(updated_reserva, "atualizada")
        return self._serialize_reserva(updated_reserva)
    
    def _serialize_reserva(self, reserva) -> Dict[str, Any]:
        """Serializar reserva para response com todos os campos"""
        # Calcular valor total
        valor_total = self._calcular_valor_total_model(reserva)
        cupom_uso = None
        valor_desconto = 0.0
        valor_total_com_desconto = valor_total

        # Serializar pagamentos para validaÃ§Ã£o no frontend
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
        
        # Serializar hospedagem para validaÃ§Ã£o de checkout
        hospedagem = None
        try:
            if hasattr(reserva, 'hospedagem') and reserva.hospedagem:
                hosp = reserva.hospedagem
                hospedagem = {
                    "id": getattr(hosp, 'id', None),
                    "status_hospedagem": getattr(hosp, 'statusHospedagem', None),
                    "data_checkin": getattr(hosp, 'checkinRealizadoEm', None),
                    "data_checkout": getattr(hosp, 'checkoutRealizadoEm', None),
                    "checkin_realizado_por": getattr(hosp, 'checkinRealizadoPor', None),
                    "checkout_realizado_por": getattr(hosp, 'checkoutRealizadoPor', None),
                    "assinatura_checkin": getattr(hosp, 'assinaturaCheckin', None),
                    "assinatura_checkout": getattr(hosp, 'assinaturaCheckout', None),
                    "checkin_dados": getattr(hosp, 'checkinDados', None),
                    "checkout_dados": getattr(hosp, 'checkoutDados', None),
                    "created_at": getattr(hosp, 'createdAt', None)
                }
        except Exception as e:
            print(f"DEBUG: Erro ao serializar hospedagem: {e}")
            hospedagem = None

        try:
            if hasattr(reserva, 'cupomUso') and reserva.cupomUso:
                uso = reserva.cupomUso
                cupom = getattr(uso, 'cupom', None)
                valor_desconto = float(getattr(uso, 'valorDesconto', 0) or 0.0)
                valor_total_com_desconto = float(getattr(uso, 'valorFinal', valor_total) or valor_total)
                cupom_uso = {
                    "id": uso.id,
                    "cupom_id": uso.cupomId,
                    "codigo": getattr(cupom, 'codigo', None),
                    "tipo_desconto": getattr(cupom, 'tipoDesconto', None),
                    "valor_original": float(getattr(uso, 'valorOriginal', valor_total) or valor_total),
                    "valor_desconto": valor_desconto,
                    "valor_final": valor_total_com_desconto,
                    "pontos_bonus": int(getattr(cupom, 'pontosBonus', 0) or 0),
                    "created_at": uso.createdAt.isoformat() if getattr(uso, 'createdAt', None) else None,
                }
        except Exception as e:
            print(f"DEBUG: Erro ao serializar cupom: {e}")
            cupom_uso = None

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
            "origem": getattr(reserva, 'origem', None),
            "responsavel_nome": getattr(reserva, 'responsavelNome', None),
            "forma_pagamento": getattr(reserva, 'formaPagamento', None),
            "observacoes": getattr(reserva, 'observacoes', None),
            "telefone_contato": getattr(reserva, 'telefoneContato', None)
                or getattr(getattr(reserva, 'cliente', None), 'telefone', None),
            "email_contato": getattr(reserva, 'emailContato', None)
                or getattr(getattr(reserva, 'cliente', None), 'email', None),
            "criado_por_funcionario_id": getattr(reserva, 'criadoPorFuncionarioId', None),
            "tarifa_suite_id": getattr(reserva, 'tarifaSuiteId', None),
            "valor_desconto": valor_desconto,
            "valor_total_com_desconto": valor_total_com_desconto,
            "status": status_reserva,
            "pagamentos": pagamentos,
            "hospedagem": hospedagem,
            "cupom_uso": cupom_uso,
            "created_at": reserva.createdAt.isoformat() if reserva.createdAt else None,
            "updated_at": reserva.updatedAt.isoformat() if hasattr(reserva, 'updatedAt') and reserva.updatedAt else None
        }
