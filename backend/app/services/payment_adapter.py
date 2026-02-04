"""
PAYMENT ADAPTER - Adaptador para integrar PaymentOrchestrator com sistema existente
Mantém compatibilidade com PagamentoService atual enquanto migra para nova arquitetura

Padrão: Adapter Pattern
- Permite migração gradual
- Mantém interface existente
- Adiciona funcionalidades do orchestrator
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException

from app.services.payment_orchestrator import (
    PaymentOrchestrator, 
    PaymentRequest, 
    PaymentResult, 
    PaymentMethod, 
    PaymentStatus
)
from app.services.fraud_detection_orchestrator import FraudDetectionOrchestrator
from app.schemas.pagamento_schema import PagamentoCreate, CieloWebhook
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.reserva_repo import ReservaRepository


class PaymentAdapter:
    """
    ADAPTADOR PARA SISTEMA DE PAGAMENTOS
    
    Responsabilidades:
    1. Manter compatibilidade com PagamentoService
    2. Integrar PaymentOrchestrator gradualmente
    3. Converter entre formatos antigo/novo
    4. Facilitar migração sem breaking changes
    """
    
    def __init__(
        self, 
        pagamento_repo: PagamentoRepository, 
        reserva_repo: ReservaRepository = None,
        enable_fraud_detection: bool = True
    ):
        self.pagamento_repo = pagamento_repo
        self.reserva_repo = reserva_repo
        self.enable_fraud_detection = enable_fraud_detection
        
        # Instanciar o novo orquestrador
        self.orchestrator = PaymentOrchestrator(
            pagamento_repo=pagamento_repo,
            reserva_repo=reserva_repo
        )
        
        # Instanciar orquestrador anti-fraude se habilitado
        if enable_fraud_detection:
            self.fraud_orchestrator = FraudDetectionOrchestrator(
                payment_orchestrator=self.orchestrator,
                pagamento_repo=pagamento_repo,
                reserva_repo=reserva_repo
            )
        else:
            self.fraud_orchestrator = None
    
    async def create(self, dados: PagamentoCreate) -> Dict[str, Any]:
        """
        MÉTODO PRINCIPAL: Criar pagamento (compatível com PagamentoService)
        
        Converte PagamentoCreate -> PaymentRequest -> PaymentResult -> Dict
        """
        try:
            # 1. CONVERTER PARA NOVO FORMATO
            payment_request = self._convert_to_payment_request(dados)
            
            # 2. PROCESSAR COM VERIFICAÇÃO ANTI-FRAUDE (SE HABILITADA)
            if self.enable_fraud_detection and self.fraud_orchestrator:
                result = await self.fraud_orchestrator.process_payment_with_fraud_check(payment_request)
            else:
                # Processar sem anti-fraude
                result = await self.orchestrator.process_payment(payment_request)
            
            # 3. CONVERTER RESULTADO PARA FORMATO ANTIGO
            return self._convert_payment_result_to_dict(result, dados)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")
    
    def _convert_to_payment_request(self, dados: PagamentoCreate) -> PaymentRequest:
        """Converter PagamentoCreate para PaymentRequest"""
        # Mapear método de pagamento
        metodo_map = {
            "credit_card": PaymentMethod.CREDIT_CARD,
            "debit_card": PaymentMethod.DEBIT_CARD,
            "pix": PaymentMethod.PIX,
            "cash": PaymentMethod.CASH,
            "bank_transfer": PaymentMethod.BANK_TRANSFER
        }
        
        metodo = metodo_map.get(dados.metodo, PaymentMethod.CREDIT_CARD)
        
        return PaymentRequest(
            reserva_id=dados.reserva_id,
            valor=dados.valor,
            metodo=metodo,
            parcelas=dados.parcelas,
            cartao_numero=dados.cartao_numero,
            cartao_validade=dados.cartao_validade,
            cartao_cvv=dados.cartao_cvv,
            cartao_nome=dados.cartao_nome,
            idempotency_key=getattr(dados, 'idempotency_key', None)
        )
    
    def _convert_payment_result_to_dict(self, result: PaymentResult, original_dados: PagamentoCreate) -> Dict[str, Any]:
        """Converter PaymentResult para formato Dict compatível"""
        response = {
            "id": result.payment_id,
            "reserva_id": original_dados.reserva_id,
            "valor": original_dados.valor,
            "metodo": original_dados.metodo,
            "status": result.status.value,
            "cielo_payment_id": result.cielo_payment_id,
            "success": result.success,
            "message": result.message,
            "processed_at": result.processed_at.isoformat() if result.processed_at else None
        }
        
        # Adicionar dados específicos por método
        if result.pix_qr_code:
            response.update({
                "qr_code": result.pix_qr_code,
                "qr_code_base64": result.pix_qr_code_base64
            })
        
        if result.authorization_code:
            response["authorization_code"] = result.authorization_code
        
        return response
    
    async def get_by_id(self, pagamento_id: int) -> Dict[str, Any]:
        """Obter pagamento por ID (compatível)"""
        try:
            return await self.pagamento_repo.get_by_id(pagamento_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Pagamento com ID {pagamento_id} não encontrado"
            )
    
    async def get_by_payment_id(self, cielo_payment_id: str) -> Dict[str, Any]:
        """Obter pagamento pelo ID da Cielo (compatível)"""
        try:
            return await self.pagamento_repo.get_by_payment_id(cielo_payment_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Pagamento com ID Cielo {cielo_payment_id} não encontrado"
            )
    
    async def process_webhook(self, webhook_data: CieloWebhook) -> Dict[str, Any]:
        """Processar webhook da Cielo (usando orquestrador)"""
        try:
            # Converter webhook para formato do orquestrador
            webhook_dict = {
                "status": webhook_data.status,
                "authorization_code": webhook_data.authorization_code,
                "response_code": webhook_data.response_code,
                "response_message": webhook_data.response_message
            }
            
            # Processar com orquestrador
            result = await self.orchestrator.process_webhook(
                webhook_data.payment_id, 
                webhook_dict
            )
            
            # Converter resultado
            return {
                "id": result.payment_id,
                "cielo_payment_id": result.cielo_payment_id,
                "status": result.status.value,
                "success": result.success,
                "message": result.message
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    async def list_by_reserva(self, reserva_id: int) -> List[Dict[str, Any]]:
        """Listar pagamentos de uma reserva (compatível)"""
        return await self.pagamento_repo.list_by_reserva(reserva_id)
    
    async def list_all(self) -> Dict[str, Any]:
        """Listar todos os pagamentos (compatível)"""
        registros = await self.pagamento_repo.list_all()
        return {
            "total": len(registros),
            "pagamentos": registros
        }
    
    async def verificar_status_pix(self, pagamento_id: int) -> Dict[str, Any]:
        """Verificar status de pagamento PIX (compatível)"""
        try:
            pagamento = await self.pagamento_repo.get_by_id(pagamento_id)
            
            if pagamento["metodo"] != "pix":
                raise HTTPException(status_code=400, detail="Pagamento não é PIX")
            
            # Usar lógica existente por enquanto
            # TODO: Migrar para orquestrador quando necessário
            return {
                "pagamento_id": pagamento_id,
                "status": pagamento["status"],
                "paid": pagamento["status"] == "APROVADO"
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Pagamento com ID {pagamento_id} não encontrado"
            )
    
    async def confirmar_pix_manual(self, pagamento_id: int) -> Dict[str, Any]:
        """Confirmar pagamento PIX manualmente (compatível)"""
        try:
            pagamento = await self.pagamento_repo.get_by_id(pagamento_id)
            
            if pagamento["metodo"] != "pix":
                raise HTTPException(status_code=400, detail="Pagamento não é PIX")
            
            if pagamento["status"] != "AGUARDANDO_PAGAMENTO":
                raise HTTPException(status_code=400, detail="Pagamento não está aguardando")
            
            # Atualizar para APROVADO
            pagamento_atualizado = await self.pagamento_repo.update_status(
                pagamento_id,
                "APROVADO"
            )
            
            # Confirmar reserva usando orquestrador
            if self.reserva_repo:
                try:
                    await self.orchestrator._confirm_reservation_if_approved(pagamento["reserva_id"])
                except Exception as e:
                    print(f"⚠️ Erro ao confirmar reserva via orquestrador: {e}")
            
            return {
                **pagamento_atualizado,
                "success": True,
                "message": "PIX confirmado com sucesso"
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Pagamento com ID {pagamento_id} não encontrado"
            )
    
    async def cancelar_pagamento(self, pagamento_id: int) -> Dict[str, Any]:
        """Cancelar pagamento (usando orquestrador)"""
        try:
            # Usar orquestrador para cancelamento
            result = await self.orchestrator.cancel_payment(pagamento_id)
            
            # Converter resultado
            return {
                "id": result.payment_id,
                "cielo_payment_id": result.cielo_payment_id,
                "status": result.status.value,
                "success": result.success,
                "message": result.message
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))


# FACTORY FUNCTION para criar instância do adapter
def create_payment_adapter() -> PaymentAdapter:
    """Factory para criar instância do adapter"""
    from app.repositories.pagamento_repo import PagamentoRepository
    from app.repositories.reserva_repo import ReservaRepository
    from app.db.database import get_db
    
    # Em produção, usar dependency injection
    db = get_db()
    pagamento_repo = PagamentoRepository(db)
    reserva_repo = ReservaRepository(db)
    
    return PaymentAdapter(pagamento_repo, reserva_repo)


# BACKWARD COMPATIBILITY: Alias para PagamentoService
class PagamentoServiceV2(PaymentAdapter):
    """
    VERSÃO 2 DO PAGAMENTO SERVICE
    
    Mantém interface idêntica ao PagamentoService original
    mas usa PaymentOrchestrator internamente
    
    Permite migração transparente:
    - Trocar PagamentoService por PagamentoServiceV2
    - Sem alterar código cliente
    - Benefícios da nova arquitetura
    """
    pass
