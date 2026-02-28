"""
Rotas para registrar pagamento manual da maquininha
Usado quando cliente paga fora do sistema e recepcionista precisa registrar
"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.pagamento_schema import PagamentoCreate
from app.services.pagamento_service import PagamentoService
from app.services.cielo_service import CieloAPI
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.pagamento_repo import PagamentoRepository
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from typing import Dict, Any

router = APIRouter(prefix="/pagamentos", tags=["pagamentos-manuais"])

# Dependency injection
async def get_pagamento_service() -> PagamentoService:
    from app.repositories.reserva_repo import ReservaRepository
    db = get_db()
    return PagamentoService(
        PagamentoRepository(db),
        ReservaRepository(db)
    )

async def get_cielo_service() -> CieloAPI:
    return CieloAPI()

@router.post("/registrar-manual-maquininha")
async def registrar_pagamento_manual(
    reserva_id: int,
    codigo_autorizacao: str,  # Código que a maquininha exibe
    valor: float,
    metodo: str = "credit_card",
    current_user: User = Depends(get_current_active_user)
):
    """
    Registrar pagamento feito na maquininha com validação do código
    """
    try:
        # 1) Validar reserva
        db = get_db()
        reserva_repo = ReservaRepository(db)
        reserva = await reserva_repo.get_by_id(reserva_id)
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")
        
        # 2) Consultar na Cielo (produção)
        cielo_service = get_cielo_service()
        
        # Tentar encontrar por AuthorizationCode nas vendas recentes
        # NOTA: Cielo não tem busca direta por AuthorizationCode
        # Precisamos pedir o PaymentId ou TID do comprovante
        
        if len(codigo_autorizacao) == 6 and codigo_autorizacao.isdigit():
            # Provavelmente é AuthorizationCode - não podemos buscar direto
            # Pedir ao recepcionista o PaymentId ou TID
            raise HTTPException(
                status_code=400,
                detail="Use o PaymentId ou TID do comprovante. AuthorizationCode não pode ser consultado diretamente."
            )
        
        # Tentar como PaymentId
        if "-" in codigo_autorizacao:  # Formato UUID
            resultado = cielo_service.consultar_pagamento(codigo_autorizacao)
        else:
            # Tentar como TID
            resultado = cielo_service.consultar_por_tid(codigo_autorizacao)
        
        if not resultado.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"Código não encontrado ou pagamento não aprovado: {resultado.get('error')}"
            )
        
        pagamento_cielo = resultado.get("data", {})
        
        # Verificar se está aprovado
        if pagamento_cielo.get("Status") != 2:  # 2 = Aprovado
            raise HTTPException(
                status_code=400,
                detail="Pagamento não está aprovado na Cielo"
            )
        
        # 3) Criar pagamento no sistema
        pagamento_repo = PagamentoRepository(db)
        pagamento = await pagamento_repo.create_manual({
            "reserva_id": reserva_id,
            "valor": valor,
            "metodo": metodo,
            "status": "APROVADO",
            "cielo_payment_id": pagamento_cielo.get("PaymentId"),
            "authorization_code": pagamento_cielo.get("AuthorizationCode"),
            "tid": pagamento_cielo.get("Tid"),
            "proof_of_sale": pagamento_cielo.get("ProofOfSale")
        })
        
        # 4) Confirmar reserva automaticamente
        await reserva_repo.confirmar(reserva_id)
        
        # 5) Gerar voucher
        from app.services.voucher_service import gerar_voucher
        voucher = await gerar_voucher(reserva_id)
        
        return {
            "success": True,
            "message": "Pagamento registrado e confirmado",
            "pagamento_id": pagamento["id"],
            "voucher": voucher,
            "comprovantes": {
                "payment_id": pagamento_cielo.get("PaymentId"),
                "authorization_code": pagamento_cielo.get("AuthorizationCode"),
                "tid": pagamento_cielo.get("Tid"),
                "proof_of_sale": pagamento_cielo.get("ProofOfSale"),
                "status": pagamento_cielo.get("Status"),
                "amount": pagamento_cielo.get("Amount")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consultar-comprovante")
async def consultar_comprovante(
    payment_id: str = None,
    tid: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Consultar comprovante na Cielo
    Usado para validar pagamento antes de registrar
    """
    try:
        cielo_service = get_cielo_service()
        
        if payment_id:
            resultado = cielo_service.consultar_pagamento(payment_id)
        elif tid:
            resultado = cielo_service.consultar_por_tid(tid)
        else:
            raise HTTPException(
                status_code=400,
                detail="Informe payment_id ou tid"
            )
        
        if not resultado.get("success"):
            return {
                "found": False,
                "error": resultado.get("error")
            }
        
        pagamento_cielo = resultado.get("data", {})
        
        return {
            "found": True,
            "payment_id": pagamento_cielo.get("PaymentId"),
            "authorization_code": pagamento_cielo.get("AuthorizationCode"),
            "tid": pagamento_cielo.get("Tid"),
            "proof_of_sale": pagamento_cielo.get("ProofOfSale"),
            "status": pagamento_cielo.get("Status"),
            "status_text": "Aprovado" if pagamento_cielo.get("Status") == 2 else "Pendente",
            "amount": pagamento_cielo.get("Amount"),
            "captured_amount": pagamento_cielo.get("CapturedAmount"),
            "merchant_order_id": pagamento_cielo.get("MerchantOrderId"),
            "captured_date": pagamento_cielo.get("CapturedDate")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ajuda-codigos")
async def ajuda_codigos():
    """
    Ajuda sobre quais códigos usar do comprovante
    """
    return {
        "titulo": "Como registrar pagamento da maquininha",
        "passos": [
            "1. Cliente paga na maquininha",
            "2. Pegue o comprovante da maquininha",
            "3. Use um destes códigos:",
            "   - PaymentId: UUID (ex: 24bc8366-fc31-4d6c-8555-17049a836a07)",
            "   - TID: Número da transação (ex: 0223103744208)",
            "   - AuthorizationCode: NÃO pode ser consultado",
            "4. Digite o código no sistema",
            "5. Sistema valida na Cielo e registra"
        ],
        "exemplos": {
            "payment_id": "24bc8366-fc31-4d6c-8555-17049a836a07",
            "tid": "0223103744208",
            "authorization_code": "123456 (apenas exibição, não consulta)"
        },
        "comprovantes": {
            "payment_id": "ID único na Cielo",
            "authorization_code": "Código de 6 dígitos da maquininha",
            "tid": "ID da transação na maquininha",
            "proof_of_sale": "NSU do comprovante"
        }
    }
