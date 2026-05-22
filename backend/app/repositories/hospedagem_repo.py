"""
Repository para Hospedagem (Estado Operacional)
Gerencia check-in, checkout e estado da hospedagem
"""
from typing import Dict, Any, Optional
from datetime import datetime
from prisma import Client
from app.core.state_validators import StateValidator
from app.utils.datetime_utils import now_utc

STATUS_PAGAMENTO_APROVADO = {"CONFIRMADO", "PAGO", "APROVADO", "APPROVED", "CAPTURED", "AUTHORIZED"}


class HospedagemRepository:
    """Repository para operações de hospedagem"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def get_by_reserva_id(self, reserva_id: int) -> Dict[str, Any]:
        """Buscar hospedagem por ID da reserva"""
        hospedagem = await self.db.hospedagem.find_unique(
            where={"reservaId": reserva_id},
            include={"reserva": True}
        )
        
        if not hospedagem:
            raise ValueError(f"Hospedagem não encontrada para reserva {reserva_id}")
        
        return self._serialize(hospedagem)
    
    async def checkin(
        self,
        reserva_id: int,
        num_hospedes: Optional[int] = None,
        num_criancas: Optional[int] = None,
        placa_veiculo: Optional[str] = None,
        observacoes: Optional[str] = None,
        assinatura_checkin: Optional[str] = None,
        checkin_dados: Optional[Dict[str, Any]] = None,
        funcionario_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Realizar check-in
        
        VALIDAÇÕES CRÍTICAS:
        1. Reserva deve estar CONFIRMADA
        2. Pagamento deve estar PAGO
        3. Hospedagem deve estar NAO_INICIADA
        """
        # Buscar dados completos
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={
                "hospedagem": True,
                "pagamentos": True
            }
        )
        
        if not reserva:
            raise ValueError(f"Reserva {reserva_id} não encontrada")
        
        # Se não existe hospedagem, criar uma nova para o check-in
        if not reserva.hospedagem:
            # Criar nova hospedagem para check-in
            hospedagem_nova = await self.db.hospedagem.create(
                data={
                    "reservaId": reserva_id,
                    "statusHospedagem": "NAO_INICIADA",
                    "createdAt": now_utc(),
                    "updatedAt": now_utc()
                }
            )
            
            # Buscar novamente para incluir a hospedagem criada
            reserva = await self.db.reserva.find_unique(
                where={"id": reserva_id},
                include={
                    "hospedagem": True,
                    "pagamentos": True
                }
            )
        
        # Buscar pagamento (usar o primeiro CONFIRMADO/PAGO/APROVADO)
        pagamento_pago = next(
            (p for p in reserva.pagamentos if p.statusPagamento in ("CONFIRMADO", "PAGO", "APROVADO")),
            None
        )
        
        if not pagamento_pago:
            raise ValueError("Nenhum pagamento aprovado encontrado")
        
        # VALIDAÇÃO CRÍTICA: Verificar se pode fazer check-in
        status_pagamento_raw = pagamento_pago.statusPagamento
        status_pagamento = status_pagamento_raw
        if status_pagamento_raw in ("PAGO", "APROVADO", "APPROVED", "CONFIRMADO", "CAPTURED", "AUTHORIZED"):
            status_pagamento = "CONFIRMADO"
        
        pode, motivo = StateValidator.validar_acao_checkin(
            reserva.statusReserva,
            status_pagamento,
            reserva.hospedagem.statusHospedagem
        )
        
        if not pode:
            raise ValueError(motivo)
        
        # Atualizar hospedagem
        hospedagem_atualizada = await self.db.hospedagem.update(
            where={"reservaId": reserva_id},
            data={
                "statusHospedagem": "CHECKIN_REALIZADO",
                "checkinRealizadoEm": now_utc(),
                "checkinRealizadoPor": funcionario_id,
                "numHospedes": num_hospedes,
                "numCriancas": num_criancas,
                "placaVeiculo": placa_veiculo,
                "observacoes": observacoes,
                "assinaturaCheckin": assinatura_checkin,
                "checkinDados": checkin_dados
            }
        )
        
        # Atualizar quarto para OCUPADO
        quarto_numero = (reserva.quartoNumero or "").strip()
        await self.db.quarto.update(
            where={"numero": quarto_numero},
            data={"status": "OCUPADO"}
        )
        
        # Atualizar campos legacy da reserva (manter sincronizado)
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "checkinReal": now_utc(),
                "statusReserva": "HOSPEDADO"
            }
        )
        
        # Criar notificação
        from app.services.notification_service import NotificationService
        await NotificationService.notificar_checkin_realizado(self.db, reserva)
        
        # Registrar auditoria
        if funcionario_id:
            try:
                from app.services.auditoria_service import AuditoriaService
                await AuditoriaService.registrar_checkin(
                    funcionario_id=funcionario_id,
                    reserva_id=reserva_id
                )
            except Exception as e:
                print(f"[AUDITORIA] Erro ao registrar auditoria check-in (não crítico): {e}")
        
        try:
            from app.services.indicacao_service import IndicacaoService
            await IndicacaoService(self.db).registrar_checkin_realizado(
                reserva_id=reserva_id,
                checkin_datetime=hospedagem_atualizada.checkinRealizadoEm,
            )
        except Exception as e:
            print(f"[CONVITE REAL] Erro ao registrar check-in da indicacao: {e}")

        return self._serialize(hospedagem_atualizada)
    
    async def checkout(
        self,
        reserva_id: int,
        consumo_frigobar: float = 0,
        servicos_extras: float = 0,
        avaliacao: Optional[int] = None,
        comentario_avaliacao: Optional[str] = None,
        assinatura_checkout: Optional[str] = None,
        checkout_dados: Optional[Dict[str, Any]] = None,
        funcionario_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Realizar checkout
        
        VALIDAÇÃO CRÍTICA:
        - Hospedagem deve estar CHECKIN_REALIZADO
        - ⚠️ NÃO depende de pagamento (já foi pago antes)
        """
        # Buscar dados completos
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True, "pagamentos": True}
        )
        
        if not reserva:
            raise ValueError(f"Reserva {reserva_id} não encontrada")
        
        if not reserva.hospedagem:
            raise ValueError(f"Hospedagem não encontrada para reserva {reserva_id}")
        
        # VALIDAÇÃO CRÍTICA: Verificar se pode fazer checkout
        pode, motivo = StateValidator.validar_acao_checkout(
            reserva.hospedagem.statusHospedagem
        )
        
        if not pode:
            raise ValueError(motivo)
        
        total_extras = float(consumo_frigobar or 0) + float(servicos_extras or 0)
        if total_extras > 0:
            valor_hospedagem = (
                float(reserva.valorTotal)
                if getattr(reserva, "valorTotal", None) is not None
                else float(reserva.valorDiaria or 0) * int(reserva.numDiarias or 0)
            )
            total_pago = sum(
                float(p.valor or 0)
                for p in (reserva.pagamentos or [])
                if p.statusPagamento in STATUS_PAGAMENTO_APROVADO
            )
            saldo_pendente = (valor_hospedagem + total_extras) - total_pago
            if saldo_pendente > 0.01:
                raise ValueError(
                    f"Check-out bloqueado: saldo pendente de R$ {saldo_pendente:.2f} "
                    f"incluindo R$ {total_extras:.2f} de extras."
                )

        checkout_timestamp = now_utc()
        
        # Atualizar hospedagem
        hospedagem_atualizada = await self.db.hospedagem.update(
            where={"reservaId": reserva_id},
            data={
                "statusHospedagem": "CHECKOUT_REALIZADO",
                "checkoutRealizadoEm": checkout_timestamp,
                "checkoutRealizadoPor": funcionario_id,
                "assinaturaCheckout": assinatura_checkout,
                "checkoutDados": checkout_dados
            }
        )
        
        # Atualizar quarto para LIVRE
        quarto_numero = (reserva.quartoNumero or "").strip()
        await self.db.quarto.update(
            where={"numero": quarto_numero},
            data={"status": "LIVRE"}
        )
        
        # Atualizar campos legacy da reserva (manter sincronizado)
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "checkoutReal": checkout_timestamp,
                "statusReserva": "CHECKOUT_REALIZADO"
            }
        )
        
        # Creditar pontos de fidelidade
        resultado_pontos_checkout = await self._creditar_pontos_checkout(
            reserva_id=reserva_id,
            funcionario_id=funcionario_id,
            checkout_datetime=checkout_timestamp,
        )

        try:
            from app.services.indicacao_service import IndicacaoService
            resultado_indicacao = await IndicacaoService(self.db).processar_credito_indicacao_apos_checkout(
                reserva_id=reserva_id,
                funcionario_id=funcionario_id,
            )
            if resultado_indicacao.get("creditado"):
                print(f"[CONVITE REAL] +{resultado_indicacao.get('pontos', 0)} pontos creditados por indicacao")
            elif resultado_indicacao.get("motivo"):
                print(f"[CONVITE REAL] Sem credito de indicacao: {resultado_indicacao.get('motivo')}")
        except Exception as e:
            print(f"[CONVITE REAL] Erro ao processar credito de indicacao: {e}")

        # Criar notificação
        from app.services.notification_service import NotificationService
        await NotificationService.notificar_checkout_realizado(self.db, reserva)

        try:
            reserva_cliente = await self.db.reserva.find_unique(
                where={"id": reserva_id},
                include={"cliente": True},
            )
            cliente_id = getattr(reserva_cliente, "clienteId", None) if reserva_cliente else None
            if cliente_id:
                await NotificationService.notificar_premio_proximo(
                    self.db,
                    cliente_id=cliente_id,
                    reserva_id=reserva_id,
                )

                from app.services.programa_pontos_service import ProgramaPontosService
                from app.services.whatsapp_service import get_whatsapp_service

                programa = await ProgramaPontosService(self.db).obter_programa_cliente(cliente_id)
                proximo_premio = programa.get("proximo_premio") or {}
                cliente = getattr(reserva_cliente, "cliente", None)
                await get_whatsapp_service().enviar_pontos_pos_checkout(
                    cliente_nome=getattr(cliente, "nomeCompleto", None) or getattr(reserva_cliente, "clienteNome", "Cliente"),
                    cliente_telefone=getattr(cliente, "telefone", None),
                    documento=getattr(cliente, "documento", None),
                    codigo_reserva=getattr(reserva_cliente, "codigoReserva", None) or str(reserva_id),
                    saldo_atual=int(programa.get("saldo_atual") or 0),
                    pontos_ganhos_checkout=int((resultado_pontos_checkout or {}).get("pontos_checkout", 0) or 0),
                    faltam_pontos_para_proximo_premio=programa.get("faltam_pontos_para_proximo_premio"),
                    proximo_premio_nome=proximo_premio.get("nome"),
                )
        except Exception as e:
            print(f"[POS CHECKOUT] Erro ao enviar avisos de pontos: {e}")

        return self._serialize(hospedagem_atualizada)
    
    async def _creditar_pontos_checkout(
        self,
        reserva_id: int,
        funcionario_id: Optional[int] = None,
        checkout_datetime: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Creditar pontos RP após checkout (Nova lógica baseada em tipo de suíte + diárias)
        
        REGRAS RP:
        - Suíte Luxo: 3 RP a cada 2 diárias
        - Suíte Master: 4 RP a cada 2 diárias  
        - Suíte Real: 5 RP a cada 2 diárias
        - Diárias excedentes são acumuladas para próximas reservas
        """
        from app.services.pontos_checkout_service import (
            creditar_bonus_cupom_no_checkout,
            creditar_rp_no_checkout,
        )

        try:
            result = await creditar_rp_no_checkout(
                self.db,
                reserva_id=reserva_id,
                funcionario_id=funcionario_id,
                checkout_datetime=checkout_datetime,
            )

            if not result.get("success"):
                print(f"[CHECKOUT RP] Erro ao creditar pontos: {result.get('error')}")
                return {"success": False, "error": result.get("error")}

            if not result.get("creditado"):
                motivo = result.get("motivo")
                if motivo:
                    print(f"[CHECKOUT RP] Sem crédito de pontos: {motivo}")
            else:
                if result.get("status") == "pendente":
                    print(
                        f"[CHECKOUT RP] Pontos pendentes: {result.get('pontos', 0)} "
                        f"liberar_em={result.get('liberar_em')}"
                    )
                else:
                    print(f"[CHECKOUT RP] Pontos creditados: {result.get('pontos', 0)}")

            bonus_result = await creditar_bonus_cupom_no_checkout(
                self.db,
                reserva_id=reserva_id,
                funcionario_id=funcionario_id,
            )
            if bonus_result.get("creditado"):
                print(f"[CHECKOUT CUPOM] Bônus creditado: {bonus_result.get('pontos', 0)}")
            elif bonus_result.get("motivo"):
                print(f"[CHECKOUT CUPOM] Sem bônus: {bonus_result.get('motivo')}")
            return {
                "success": True,
                "pontos_checkout": int(result.get("pontos", 0) or 0) if result.get("creditado") else 0,
                "pontos_status": result.get("status"),
                "pontos_liberar_em": result.get("liberar_em"),
                "pontos_bonus_cupom": int(bonus_result.get("pontos", 0) or 0) if bonus_result.get("creditado") else 0,
                "checkout": result,
                "cupom": bonus_result,
            }
        except Exception as e:
            print(f"[CHECKOUT RP] Erro ao creditar pontos: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _serialize(self, hospedagem) -> Dict[str, Any]:
        """Serializar hospedagem para response"""
        return {
            "id": hospedagem.id,
            "reserva_id": hospedagem.reservaId,
            "status_hospedagem": hospedagem.statusHospedagem,
            "checkin_realizado_em": hospedagem.checkinRealizadoEm.isoformat() if hospedagem.checkinRealizadoEm else None,
            "checkin_realizado_por": hospedagem.checkinRealizadoPor,
            "checkout_realizado_em": hospedagem.checkoutRealizadoEm.isoformat() if hospedagem.checkoutRealizadoEm else None,
            "checkout_realizado_por": hospedagem.checkoutRealizadoPor,
            "num_hospedes": hospedagem.numHospedes,
            "num_criancas": hospedagem.numCriancas,
            "placa_veiculo": hospedagem.placaVeiculo,
            "observacoes": hospedagem.observacoes,
            "assinatura_checkin": getattr(hospedagem, "assinaturaCheckin", None),
            "assinatura_checkout": getattr(hospedagem, "assinaturaCheckout", None),
            "checkin_dados": getattr(hospedagem, "checkinDados", None),
            "checkout_dados": getattr(hospedagem, "checkoutDados", None),
            "created_at": hospedagem.createdAt.isoformat() if hospedagem.createdAt else None,
            "updated_at": hospedagem.updatedAt.isoformat() if hospedagem.updatedAt else None
        }
