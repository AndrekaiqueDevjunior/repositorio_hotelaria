"""
Versão integrada do ReservaRepository com transições automáticas
Mostra como aplicar StateTransitionService na criação e confirmação
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from prisma import Client
from app.schemas.reserva_schema import ReservaCreate
from app.utils.datetime_utils import now_utc
from app.services.notification_service import NotificationService
from app.core.state_transition_service import StateTransitionService
from app.schemas.status_enums import StatusReserva
import secrets
import re


class ReservaRepositoryIntegrated:
    """
    ReservaRepository com transições automáticas de estado integradas
    """
    
    def __init__(self, db: Client):
        self.db = db
        self.state_service = StateTransitionService(db)
    
    async def create(self, reserva: ReservaCreate) -> Dict[str, Any]:
        """
        Criar nova reserva COM transições automáticas
        
        NOVO FLUXO:
        1. Validações (cliente, quarto, disponibilidade)
        2. Criar reserva com status PENDENTE_PAGAMENTO
        3. ⭐ NOVO: Criar hospedagem automaticamente
        4. Notificações
        """
        # 1. Validações (mesma lógica original)
        cliente = await self.db.cliente.find_unique(where={"id": reserva.cliente_id})
        if not cliente:
            raise ValueError("Cliente não encontrado")
        
        # Validar reservas ativas do cliente
        reservas_ativas = await self.db.reserva.find_many(
            where={
                "clienteId": reserva.cliente_id,
                "statusReserva": {"in": ["PENDENTE", "CONFIRMADA", "HOSPEDADO"]}
            }
        )
        
        if reservas_ativas:
            for reserva_ativa in reservas_ativas:
                if (reserva.checkin_previsto.date() <= reserva_ativa.checkoutPrevisto.date() and 
                    reserva.checkout_previsto.date() >= reserva_ativa.checkinPrevisto.date()):
                    
                    msg_erro = f"❌ CLIENTE JÁ POSSUI RESERVA ATIVA!"
                    msg_erro += f"\n\n📋 Reserva existente: {reserva_ativa.codigoReserva}"
                    msg_erro += f"\n  • Quarto: {reserva_ativa.quartoNumero}"
                    msg_erro += f"\n  • Check-in: {reserva_ativa.checkinPrevisto.strftime('%d/%m/%Y')}"
                    msg_erro += f"\n  • Check-out: {reserva_ativa.checkoutPrevisto.strftime('%d/%m/%Y')}"
                    msg_erro += f"\n  • Status: {reserva_ativa.statusReserva}"
                    raise ValueError(msg_erro)
        
        # Validar quarto
        quarto = await self.db.quarto.find_unique(where={"numero": reserva.quarto_numero})
        if not quarto:
            raise ValueError("Quarto não encontrado")
        
        if quarto.status in ("BLOQUEADO", "MANUTENCAO"):
            raise ValueError(f"❌ Quarto {reserva.quarto_numero} está {quarto.status.lower()}")
        
        # Validar disponibilidade
        from app.services.disponibilidade_service import DisponibilidadeService
        disponibilidade_service = DisponibilidadeService(self.db)
        
        resultado = await disponibilidade_service.verificar_disponibilidade(
            reserva.quarto_numero,
            reserva.checkin_previsto,
            reserva.checkout_previsto
        )
        
        if not resultado["disponivel"]:
            msg_erro = f"❌ QUARTO INDISPONÍVEL! {resultado['motivo']}"
            raise ValueError(msg_erro)
        
        # 2. Criar reserva com status correto
        valor_diaria = await self._obter_tarifa_diaria(reserva.tipo_suite, reserva.checkin_previsto)
        
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
                        # ⭐ CORREÇÃO: Usar status correto do enum
                        "statusReserva": StatusReserva.PENDENTE_PAGAMENTO.value
                    }
                )
                break
            except Exception:
                nova_reserva = None
        
        if not nova_reserva:
            raise ValueError("Não foi possível gerar código único")
        
        # 3. ⭐ NOVO: Criar hospedagem automaticamente
        hospedagem = await self.db.hospedagem.create(
            data={
                "reservaId": nova_reserva.id,
                "statusHospedagem": "NAO_INICIADA"
            }
        )
        
        print(f"✅ Hospedagem criada automaticamente para reserva {nova_reserva.id}")
        
        # 4. Notificações
        await NotificationService.notificar_nova_reserva(self.db, nova_reserva)
        
        return self._serialize_reserva(nova_reserva, hospedagem)
    
    async def confirmar(self, reserva_id: int) -> Dict[str, Any]:
        """
        Confirmar reserva COM transições automáticas
        
        NOVO FLUXO:
        1. Validações
        2. ⭐ NOVO: Usar StateTransitionService para transição
        3. Gerar voucher
        4. Notificações
        """
        # Buscar reserva
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"pagamentos": True}
        )
        
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        # Validar se pode confirmar
        if not reserva.pagamentos:
            raise ValueError("Reserva não possui pagamentos")
        
        # Encontrar pagamento aprovado
        pagamento_aprovado = None
        for p in reserva.pagamentos:
            if p.statusPagamento in ["CONFIRMADO", "APROVADO", "PAGO"]:
                pagamento_aprovado = p
                break
        
        if not pagamento_aprovado:
            raise ValueError("Reserva não possui pagamento aprovado")
        
        # ⭐ NOVO: Usar serviço de transição
        transicao_result = await self.state_service.transicao_apos_aprovacao_pagamento(
            pagamento_aprovado.id, usuario_id=1  # Admin system
        )
        
        if not transicao_result["success"]:
            raise ValueError(f"Erro na transição: {transicao_result.get('error')}")
        
        print(f"[TRANSICAO] {transicao_result['transicao']} - Reserva {reserva_id}")
        
        # Gerar voucher
        try:
            from app.services.voucher_service import gerar_voucher
            voucher = await gerar_voucher(reserva_id)
            print(f"✅ Voucher gerado: {voucher.get('codigo')}")
        except Exception as e:
            print(f"⚠️ Erro ao gerar voucher: {e}")
        
        # Buscar reserva atualizada
        reserva_atualizada = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
        
        return self._serialize_reserva(reserva_atualizada, reserva_atualizada.hospedagem)
    
    async def checkin(self, reserva_id: int) -> Dict[str, Any]:
        """
        Check-in COM transições automáticas
        
        NOVO FLUXO:
        1. Validações
        2. ⭐ NOVO: Usar StateTransitionService para transição
        3. Atualizar quarto
        4. Notificações
        """
        # Buscar reserva completa
        reserva = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"pagamentos": True, "hospedagem": True}
        )
        
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        # Validar status
        if reserva.statusReserva != StatusReserva.CONFIRMADA.value:
            raise ValueError(f"Check-in requer status CONFIRMADA (atual: {reserva.statusReserva})")
        
        # Validar pagamento
        pagamentos_aprovados = [
            p for p in reserva.pagamentos
            if p.statusPagamento in ("APROVADO", "PAGO", "CONFIRMADO", "CAPTURED", "AUTHORIZED")
        ]
        
        if not pagamentos_aprovados:
            raise ValueError("Check-in requer pagamento aprovado")
        
        # Validar quarto
        quarto = await self.db.quarto.find_unique(where={"numero": reserva.quartoNumero})
        if quarto and quarto.status != "LIVRE":
            raise ValueError(f"Quarto {reserva.quartoNumero} não está disponível (status: {quarto.status})")
        
        # ⭐ NOVO: Usar serviço de transição
        transicao_result = await self.state_service.transicao_apos_checkin(
            reserva_id, usuario_id=1  # Admin system
        )
        
        if not transicao_result["success"]:
            raise ValueError(f"Erro na transição: {transicao_result.get('error')}")
        
        print(f"[TRANSICAO] {transicao_result['transicao']} - Reserva {reserva_id}")
        
        # Atualizar quarto para OCUPADO
        quarto_numero_raw = (reserva.quartoNumero or "").strip()
        match = re.search(r"\d+", quarto_numero_raw)
        quarto_numero = match.group(0) if match else quarto_numero_raw
        await self.db.quarto.update(
            where={"numero": quarto_numero},
            data={"status": "OCUPADO"}
        )
        
        # Buscar reserva atualizada
        reserva_atualizada = await self.db.reserva.find_unique(
            where={"id": reserva_id},
            include={"hospedagem": True}
        )
        
        # Notificações
        await NotificationService.notificar_checkin_realizado(self.db, reserva_atualizada)
        
        return self._serialize_reserva(reserva_atualizada, reserva_atualizada.hospedagem)
    
    def _serialize_reserva(self, reserva, hospedagem=None) -> Dict[str, Any]:
        """Serializar reserva com dados de hospedagem"""
        valor_total = float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0.0
        
        # Serializar pagamentos
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
        
        # Serializar hospedagem
        hospedagem_data = None
        if hospedagem:
            hospedagem_data = {
                "id": hospedagem.id,
                "status_hospedagem": hospedagem.statusHospedagem,
                "data_checkin": hospedagem.checkinRealizadoEm,
                "data_checkout": hospedagem.checkoutRealizadoEm,
                "created_at": hospedagem.createdAt
            }
        
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
            "status": reserva.statusReserva,  # Usar valor real do banco
            "pagamentos": pagamentos,
            "hospedagem": hospedagem_data,
            "created_at": reserva.createdAt.isoformat() if reserva.createdAt else None,
            "updated_at": reserva.updatedAt.isoformat() if hasattr(reserva, 'updatedAt') and reserva.updatedAt else None
        }
    
    async def _obter_tarifa_diaria(self, tipo_suite: str, data: datetime) -> float:
        """Obter tarifa diária (implementação simulada)"""
        # Simulação - buscar de tabela de tarifas
        tarifas = {
            "DUPLA": 150.0,
            "LUXO": 200.0,
            "LUXO 2º": 250.0,
            "LUXO 3º": 300.0,
            "LUXO 4º EC": 350.0,
            "MASTER": 400.0,
            "REAL": 500.0
        }
        return tarifas.get(tipo_suite, 200.0)


# ==================== EXEMPLO DE INTEGRAÇÃO ====================

"""
Para usar o novo repositório integrado:

1. Substituir a importação no reserva_routes.py:

DE:
from app.repositories.reserva_repo import ReservaRepository

PARA:
from app.repositories.reserva_repo_integrated import ReservaRepositoryIntegrated

2. Atualizar a injeção de dependência:

DE:
reserva_repo = ReservaRepository(db)

PARA:
reserva_repo = ReservaRepositoryIntegrated(db)

3. O fluxo completo funcionará automaticamente:
   - Criação: status PENDENTE_PAGAMENTO + hospedagem criada
   - Pagamento: transições automáticas via StateTransitionService
   - Confirmação: status CONFIRMADA
   - Check-in: status HOSPEDADO

Benefícios:
- ✅ Hospedagem criada automaticamente
- ✅ Status correto desde o início (PENDENTE_PAGAMENTO)
- ✅ Transições automáticas consistentes
- ✅ Check-in habilitado corretamente
- ✅ Fluxo completo funcional
"""
