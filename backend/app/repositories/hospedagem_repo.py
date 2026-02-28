"""
Repository para Hospedagem (Estado Operacional)
Gerencia check-in, checkout e estado da hospedagem
"""
from typing import Dict, Any, Optional
from datetime import datetime
import re
from prisma import Client
from app.core.state_validators import StateValidator
from app.utils.datetime_utils import now_utc


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
                "observacoes": observacoes
            }
        )
        
        # Atualizar quarto para OCUPADO
        quarto_numero_raw = (reserva.quartoNumero or "").strip()
        match = re.search(r"\d+", quarto_numero_raw)
        quarto_numero = match.group(0) if match else quarto_numero_raw
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
        
        return self._serialize(hospedagem_atualizada)
    
    async def checkout(
        self,
        reserva_id: int,
        consumo_frigobar: float = 0,
        servicos_extras: float = 0,
        avaliacao: Optional[int] = None,
        comentario_avaliacao: Optional[str] = None,
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
            include={"hospedagem": True}
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
        
        # Validar saldo devedor (se houver consumo extra)
        if consumo_frigobar > 0 or servicos_extras > 0:
            # Verificar se extras foram pagos
            # TODO: Implementar lógica de pagamento de extras
            pass

        checkout_timestamp = now_utc()
        
        # Atualizar hospedagem
        hospedagem_atualizada = await self.db.hospedagem.update(
            where={"reservaId": reserva_id},
            data={
                "statusHospedagem": "CHECKOUT_REALIZADO",
                "checkoutRealizadoEm": checkout_timestamp,
                "checkoutRealizadoPor": funcionario_id
            }
        )
        
        # Atualizar quarto para LIVRE
        quarto_numero_raw = (reserva.quartoNumero or "").strip()
        match = re.search(r"\d+", quarto_numero_raw)
        quarto_numero = match.group(0) if match else quarto_numero_raw
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
        await self._creditar_pontos_checkout(
            reserva_id=reserva_id,
            funcionario_id=funcionario_id,
            checkout_datetime=checkout_timestamp,
        )
        
        # Criar notificação
        from app.services.notification_service import NotificationService
        await NotificationService.notificar_checkout_realizado(self.db, reserva)
        
        return self._serialize(hospedagem_atualizada)
    
    async def _creditar_pontos_checkout(
        self,
        reserva_id: int,
        funcionario_id: Optional[int] = None,
        checkout_datetime: Optional[datetime] = None,
    ) -> None:
        """
        Creditar pontos RP após checkout (Nova lógica baseada em tipo de suíte + diárias)
        
        REGRAS RP:
        - Suíte Luxo: 3 RP a cada 2 diárias
        - Suíte Master: 4 RP a cada 2 diárias  
        - Suíte Real: 5 RP a cada 2 diárias
        - Diárias excedentes são acumuladas para próximas reservas
        """
        from app.services.pontos_checkout_service import creditar_rp_no_checkout

        try:
            result = await creditar_rp_no_checkout(
                self.db,
                reserva_id=reserva_id,
                funcionario_id=funcionario_id,
                checkout_datetime=checkout_datetime,
            )

            if not result.get("success"):
                print(f"[CHECKOUT RP] Erro ao creditar pontos: {result.get('error')}")
                return

            if not result.get("creditado"):
                motivo = result.get("motivo")
                if motivo:
                    print(f"[CHECKOUT RP] Sem crédito de pontos: {motivo}")
                return

            print(f"[CHECKOUT RP] Pontos creditados: {result.get('pontos', 0)}")
        except Exception as e:
            print(f"[CHECKOUT RP] Erro ao creditar pontos: {str(e)}")
            return
    
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
            "created_at": hospedagem.createdAt.isoformat() if hospedagem.createdAt else None,
            "updated_at": hospedagem.updatedAt.isoformat() if hospedagem.updatedAt else None
        }
