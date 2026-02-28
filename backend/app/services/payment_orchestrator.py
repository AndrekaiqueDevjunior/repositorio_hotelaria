"""
PAYMENT ORCHESTRATOR - Centralizador de Pagamentos
Unifica Cielo + Pagamentos + Reservas em uma única camada

Arquitetura: Domain-Driven Design (DDD)
- Aggregate Root: PaymentTransaction
- Value Objects: PaymentMethod, PaymentStatus
- Domain Services: PaymentProcessor, ReservationConfirmer
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from fastapi import HTTPException

from app.services.cielo_service import CieloAPI
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.schemas.pagamento_schema import PagamentoCreate
from app.utils.datetime_utils import now_utc


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PIX = "pix"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(Enum):
    PENDING = "PENDENTE"
    PROCESSING = "PROCESSANDO"
    APPROVED = "APROVADO"
    DENIED = "RECUSADO"
    CANCELLED = "CANCELADO"
    REFUNDED = "ESTORNADO"
    WAITING_PIX = "AGUARDANDO_PAGAMENTO"


@dataclass
class PaymentRequest:
    """Value Object para requisição de pagamento"""
    reserva_id: int
    valor: float
    metodo: PaymentMethod
    parcelas: Optional[int] = 1
    
    # Dados do cartão (se aplicável)
    cartao_numero: Optional[str] = None
    cartao_validade: Optional[str] = None
    cartao_cvv: Optional[str] = None
    cartao_nome: Optional[str] = None
    
    # Metadados
    idempotency_key: Optional[str] = None
    user_ip: Optional[str] = None


@dataclass
class PaymentResult:
    """Value Object para resultado de pagamento"""
    success: bool
    payment_id: int
    cielo_payment_id: Optional[str]
    status: PaymentStatus
    message: str
    
    # Dados específicos por método
    pix_qr_code: Optional[str] = None
    pix_qr_code_base64: Optional[str] = None
    authorization_code: Optional[str] = None
    
    # Metadados
    processed_at: datetime = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = now_utc()


class PaymentOrchestrator:
    """
    ORQUESTRADOR CENTRAL DE PAGAMENTOS
    
    Responsabilidades:
    1. Coordenar fluxo completo de pagamento
    2. Garantir consistência entre Cielo, Pagamento e Reserva
    3. Implementar padrões de retry e idempotência
    4. Centralizar regras de negócio
    """
    
    def __init__(
        self,
        pagamento_repo: PagamentoRepository,
        reserva_repo: ReservaRepository,
        cielo_api: Optional[CieloAPI] = None
    ):
        self.pagamento_repo = pagamento_repo
        self.reserva_repo = reserva_repo
        self.cielo_api = cielo_api or CieloAPI()
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResult:
        """
        MÉTODO PRINCIPAL: Processar pagamento completo
        
        Fluxo unificado:
        1. Validar reserva e dados
        2. Criar registro de pagamento
        3. Processar com gateway (Cielo)
        4. Atualizar status baseado na resposta
        5. Confirmar reserva se aprovado
        6. Retornar resultado padronizado
        """
        try:
            # 1. VALIDAÇÕES PRÉ-PROCESSAMENTO
            await self._validate_payment_request(request)
            
            # 2. VERIFICAR IDEMPOTÊNCIA
            if request.idempotency_key:
                existing_payment = await self._check_idempotency(request.idempotency_key)
                if existing_payment:
                    return await self._build_result_from_existing(existing_payment)
            
            # 3. CRIAR REGISTRO DE PAGAMENTO (PENDENTE)
            pagamento_data = PagamentoCreate(
                reserva_id=request.reserva_id,
                valor=request.valor,
                metodo=request.metodo.value,
                parcelas=request.parcelas,
                cartao_numero=request.cartao_numero,
                cartao_validade=request.cartao_validade,
                cartao_cvv=request.cartao_cvv,
                cartao_nome=request.cartao_nome,
                idempotency_key=request.idempotency_key
            )
            
            pagamento = await self.pagamento_repo.create(pagamento_data)
            
            # 4. PROCESSAR COM GATEWAY APROPRIADO
            gateway_result = await self._process_with_gateway(request, pagamento["id"])
            
            # 5. ATUALIZAR STATUS BASEADO NA RESPOSTA
            updated_payment = await self._update_payment_status(
                pagamento["id"], 
                gateway_result
            )
            
            # 6. CONFIRMAR RESERVA SE APROVADO
            if gateway_result.get("status") in ["AUTHORIZED", "CAPTURED"]:
                await self._confirm_reservation_if_approved(request.reserva_id)
            
            # 7. CONSTRUIR RESULTADO PADRONIZADO
            return PaymentResult(
                success=gateway_result.get("success", True),
                payment_id=pagamento["id"],
                cielo_payment_id=gateway_result.get("payment_id"),
                status=PaymentStatus.APPROVED if gateway_result.get("status") in ["AUTHORIZED", "CAPTURED"] else PaymentStatus.PROCESSING,
                message=gateway_result.get("return_message", "Pagamento processado"),
                pix_qr_code=gateway_result.get("qr_code"),
                pix_qr_code_base64=gateway_result.get("qr_code_base64"),
                authorization_code=gateway_result.get("authorization_code")
            )
            
        except Exception as e:
            # ROLLBACK: Marcar pagamento como falhou se foi criado
            if 'pagamento' in locals():
                await self.pagamento_repo.update_status(
                    pagamento["id"], 
                    PaymentStatus.DENIED.value
                )
            
            return PaymentResult(
                success=False,
                payment_id=0,
                cielo_payment_id=None,
                status=PaymentStatus.DENIED,
                message=f"Erro ao processar pagamento: {str(e)}"
            )
    
    async def _validate_payment_request(self, request: PaymentRequest):
        """Validar dados da requisição de pagamento"""
        # Verificar se reserva existe e está em status válido
        try:
            reserva = await self.reserva_repo.get_by_id(request.reserva_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")
        
        if reserva["status"] not in ["PENDENTE", "CONFIRMADA"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Reserva em status {reserva['status']} não pode receber pagamento"
            )
        
        # Validar valor
        if request.valor <= 0:
            raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
        
        # Validar dados do cartão se necessário
        if request.metodo in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
            if not all([request.cartao_numero, request.cartao_validade, request.cartao_cvv, request.cartao_nome]):
                raise HTTPException(status_code=400, detail="Dados do cartão incompletos")
    
    async def _check_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Verificar se já existe pagamento com esta chave de idempotência"""
        try:
            return await self.pagamento_repo.get_by_idempotency_key(idempotency_key)
        except ValueError:
            return None
    
    async def _process_with_gateway(self, request: PaymentRequest, payment_id: int) -> Dict[str, Any]:
        """Processar pagamento com gateway apropriado"""
        if request.metodo in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
            return await self.cielo_api.criar_pagamento_cartao(
                valor=request.valor,
                cartao_numero=request.cartao_numero,
                cartao_validade=request.cartao_validade,
                cartao_cvv=request.cartao_cvv,
                cartao_nome=request.cartao_nome,
                parcelas=request.parcelas or 1
            )
        
        elif request.metodo == PaymentMethod.PIX:
            return await self.cielo_api.gerar_pix(
                valor=request.valor,
                descricao=f"Pagamento reserva #{request.reserva_id}"
            )
        
        elif request.metodo == PaymentMethod.CASH:
            # Pagamento em dinheiro - aprovação manual
            return {
                "success": True,
                "payment_id": f"CASH_{now_utc().strftime('%Y%m%d%H%M%S')}",
                "status": "AUTHORIZED",
                "return_message": "Pagamento em dinheiro - aprovação manual necessária"
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Método {request.metodo.value} não suportado")
    
    async def _update_payment_status(self, payment_id: int, gateway_result: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar status do pagamento baseado na resposta do gateway"""
        if gateway_result.get("success") == False:
            status = PaymentStatus.DENIED.value
        elif gateway_result.get("status") in ["AUTHORIZED", "CAPTURED"]:
            status = PaymentStatus.APPROVED.value
        else:
            status = PaymentStatus.PROCESSING.value
        
        return await self.pagamento_repo.update_status(
            payment_id,
            status,
            cielo_payment_id=gateway_result.get("payment_id"),
            url_pagamento=gateway_result.get("url") or gateway_result.get("qr_code")
        )
    
    async def _confirm_reservation_if_approved(self, reserva_id: int):
        """Confirmar reserva se pagamento foi aprovado"""
        try:
            await self.reserva_repo.confirmar(reserva_id)
            
            # Gerar voucher automaticamente
            from app.services.voucher_service import gerar_voucher
            voucher = await gerar_voucher(reserva_id)
            print(f"✅ [ORCHESTRATOR] Voucher gerado: {voucher['codigo']}")
            
        except Exception as e:
            print(f"⚠️ [ORCHESTRATOR] Erro ao confirmar reserva: {e}")
            # Não falhar o pagamento por erro na confirmação
    
    async def _build_result_from_existing(self, existing_payment: Dict[str, Any]) -> PaymentResult:
        """Construir resultado a partir de pagamento existente (idempotência)"""
        return PaymentResult(
            success=existing_payment["status"] == "APROVADO",
            payment_id=existing_payment["id"],
            cielo_payment_id=existing_payment.get("cielo_payment_id"),
            status=PaymentStatus(existing_payment["status"]),
            message="Pagamento já processado (idempotência)",
            processed_at=existing_payment["created_at"]
        )
    
    async def cancel_payment(self, payment_id: int) -> PaymentResult:
        """Cancelar pagamento"""
        try:
            pagamento = await self.pagamento_repo.get_by_id(payment_id)
            
            if pagamento["status"] not in ["PENDENTE", "PROCESSANDO"]:
                raise HTTPException(
                    status_code=400, 
                    detail="Pagamento não pode ser cancelado"
                )
            
            # Cancelar na Cielo se tiver payment_id
            if pagamento["cielo_payment_id"]:
                await self.cielo_api.cancelar_pagamento(pagamento["cielo_payment_id"])
            
            # Atualizar status
            updated_payment = await self.pagamento_repo.update_status(
                payment_id,
                PaymentStatus.CANCELLED.value
            )
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                cielo_payment_id=pagamento["cielo_payment_id"],
                status=PaymentStatus.CANCELLED,
                message="Pagamento cancelado com sucesso"
            )
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    async def process_webhook(self, cielo_payment_id: str, webhook_data: Dict[str, Any]) -> PaymentResult:
        """Processar webhook da Cielo"""
        try:
            pagamento = await self.pagamento_repo.get_by_payment_id(cielo_payment_id)
            
            # Mapear status do webhook
            novo_status = PaymentStatus.APPROVED.value if webhook_data.get("status") == "APPROVED" else PaymentStatus.DENIED.value
            
            # Atualizar pagamento
            updated_payment = await self.pagamento_repo.update_status(
                pagamento["id"],
                novo_status
            )
            
            # Confirmar reserva se aprovado
            if novo_status == PaymentStatus.APPROVED.value:
                await self._confirm_reservation_if_approved(pagamento["reserva_id"])
            
            return PaymentResult(
                success=True,
                payment_id=pagamento["id"],
                cielo_payment_id=cielo_payment_id,
                status=PaymentStatus(novo_status),
                message="Webhook processado com sucesso"
            )
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))


# FACTORY PATTERN para instanciar o orquestrador
def create_payment_orchestrator() -> PaymentOrchestrator:
    """Factory para criar instância do orquestrador"""
    from app.repositories.pagamento_repo import PagamentoRepository
    from app.repositories.reserva_repo import ReservaRepository
    from app.db.database import get_db
    
    # Em produção, usar dependency injection
    db = get_db()
    pagamento_repo = PagamentoRepository(db)
    reserva_repo = ReservaRepository(db)
    
    return PaymentOrchestrator(pagamento_repo, reserva_repo)
