from fastapi import APIRouter, Depends, HTTPException, Request, Header
from app.schemas.pagamento_schema import PagamentoCreate, PagamentoResponse, CieloWebhook
from app.services.pagamento_service import PagamentoService
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.repositories.pagamento_repo import PagamentoRepository
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.core.config import settings
from app.middleware.idempotency import check_idempotency, store_idempotency_result
from typing import List, Optional
from starlette.responses import JSONResponse
import os
import ipaddress

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])

# IPs autorizados da Cielo para webhooks (produÃ§Ã£o)
# Fonte: DocumentaÃ§Ã£o Cielo E-commerce
CIELO_ALLOWED_IPS = [
    "200.155.86.0/24",
    "200.155.87.0/24",
    "200.229.32.0/24",
]

JUSTIFICATIVA_REQUIRED_FUNCTIONS: set[int] = set()


def _only_digits(value: object) -> str:
    return ''.join(ch for ch in str(value or '') if ch.isdigit())


def _normalize_tef_fiscal_payload(payload: dict) -> tuple[str | None, str | None, str | None]:
    cupom_fiscal = str(payload.get('cupom_fiscal') or '').strip() or None
    data_fiscal = _only_digits(payload.get('data_fiscal')) or None
    hora_fiscal = _only_digits(payload.get('hora_fiscal')) or None

    if payload.get('enforce_fiscal_document'):
        if not cupom_fiscal:
            raise HTTPException(status_code=400, detail='Cupom Fiscal obrigatorio para abrir esta sequencia TEF.')
        if len(cupom_fiscal) > 20:
            raise HTTPException(status_code=400, detail='Cupom Fiscal deve ter no maximo 20 caracteres, conforme a documentacao da CliSiTef.')
        if not data_fiscal or len(data_fiscal) != 8:
            raise HTTPException(status_code=400, detail='Data Fiscal obrigatoria no formato AAAAMMDD para abrir esta sequencia TEF.')
        if not hora_fiscal or len(hora_fiscal) != 6:
            raise HTTPException(status_code=400, detail='Hora Fiscal obrigatoria no formato HHMMSS para abrir esta sequencia TEF.')

    return cupom_fiscal, data_fiscal, hora_fiscal


def _normalize_tef_original_reference_payload(payload: dict) -> dict | None:
    reference = payload.get('original_transaction_reference')
    if not isinstance(reference, dict):
        return None

    normalized: dict[str, object] = {}
    string_fields = (
        'cupom_fiscal',
        'nsu_host',
        'nsu_sitef',
        'rede_autorizadora',
        'bandeira',
        'autorizacao',
        'codigo_estabelecimento',
        'store_id',
        'terminal_id',
        'data_hora_transacao',
        'campo_146_valor',
        'campo_146_valor_bruto',
        'campo_515_valor',
        'campo_515_valor_ddmm',
        'campo_516_valor',
    )
    digit_fields = ('data_fiscal', 'hora_fiscal')

    for field in string_fields:
        value = str(reference.get(field) or '').strip()
        if value:
            normalized[field] = value

    for field in digit_fields:
        value = _only_digits(reference.get(field))
        if value:
            normalized[field] = value

    return normalized or None


def _wrap_tef_param_fragment(value: object, prefix: str | None = None) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if prefix and not raw.startswith(prefix) and not raw.startswith("{"):
        raw = f"{prefix}{raw}"
    if raw.startswith("{") and raw.endswith("}"):
        return raw
    return "{" + raw + "}"

def is_cielo_ip_allowed(client_ip: str) -> bool:
    """Verificar se IP do cliente estÃ¡ na lista de IPs autorizados da Cielo"""
    # Em desenvolvimento/sandbox, permitir qualquer IP
    if os.getenv("CIELO_MODE", "sandbox") == "sandbox":
        return True
    
    try:
        ip = ipaddress.ip_address(client_ip)
        for network in CIELO_ALLOWED_IPS:
            if ip in ipaddress.ip_network(network):
                return True
        return False
    except ValueError:
        return False

# Dependency injection
async def get_pagamento_service() -> PagamentoService:
    from app.repositories.reserva_repo import ReservaRepository
    db = get_db()
    return PagamentoService(
        PagamentoRepository(db),
        ReservaRepository(db)
    )

@router.get("", response_model=dict)
async def listar_pagamentos(
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Listar todos os pagamentos - Requer autenticaÃ§Ã£o"""
    return await service.list_all()

@router.post("", response_model=PagamentoResponse)
async def criar_pagamento(
    pagamento: PagamentoCreate,
    request: Request,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Criar novo pagamento com proteÃ§Ã£o de idempotÃªncia - P0-003
    
    Headers:
        Idempotency-Key: UUID Ãºnico (OBRIGATÃ“RIO para evitar pagamentos duplicados)
    
    Retorna:
        201 Created com dados do pagamento
    """
    
    # P0-003: CAMADA 1 - Verificar idempotÃªncia (CRÃTICO para pagamentos)
    if idempotency_key:
        cached = await check_idempotency(f"pag:{idempotency_key}")
        if cached:
            return JSONResponse(
                content=cached["body"],
                status_code=cached["status_code"]
            )
    
    # P0-003: CAMADA 2 - Criar pagamento
    try:
        resultado = await service.create(pagamento)
        
        # P0-003: CAMADA 3 - Cachear resultado da idempotÃªncia
        if idempotency_key:
            await store_idempotency_result(
                f"pag:{idempotency_key}", 
                resultado, 
                status_code=201
            )
        
        return JSONResponse(content=resultado, status_code=201)
        
    except Exception as e:
        # Mesmo em caso de erro, cachear para evitar retry infinito
        if idempotency_key:
            error_result = {"error": str(e), "success": False}
            await store_idempotency_result(
                f"pag:{idempotency_key}", 
                error_result, 
                status_code=400
            )
        raise

@router.post("/tef/iniciar", response_model=dict)
async def iniciar_fluxo_tef(
    payload: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    reserva_id = payload.get("reserva_id")
    valor = payload.get("valor")
    function_id = payload.get("function_id", 0)
    if not reserva_id or valor is None:
        raise HTTPException(status_code=400, detail="reserva_id e valor sao obrigatorios")
    try:
        function_id_value = int(function_id)
    except Exception:
        raise HTTPException(status_code=400, detail="function_id invalido")
    if function_id_value not in {0, 2, 3}:
        raise HTTPException(status_code=400, detail="function_id invalido para /tef/iniciar. Use 0, 2 ou 3")

    cupom_fiscal, data_fiscal, hora_fiscal = _normalize_tef_fiscal_payload(payload)

    return await service.iniciar_fluxo_tef(
        reserva_id=int(reserva_id),
        valor=float(valor),
        function_id=function_id_value,
        cupom_fiscal=cupom_fiscal,
        data_fiscal=data_fiscal,
        hora_fiscal=hora_fiscal,
        trn_additional_parameters=payload.get("trn_additional_parameters"),
        trn_init_parameters=payload.get("trn_init_parameters"),
        session_parameters=payload.get("session_parameters"),
    )

@router.post("/tef/iniciar-funcao", response_model=dict)
async def iniciar_funcao_tef(
    payload: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    function_id = payload.get("function_id")
    if function_id is None:
        raise HTTPException(status_code=400, detail="function_id e obrigatorio")

    justificativa = (payload.get("justificativa") or "").strip()
    if int(function_id) in JUSTIFICATIVA_REQUIRED_FUNCTIONS and not justificativa:
        raise HTTPException(status_code=400, detail="justificativa obrigatoria para a funcao solicitada")

    valor = payload.get("valor")
    valor_float = float(valor) if valor is not None else None
    cupom_fiscal, data_fiscal, hora_fiscal = _normalize_tef_fiscal_payload(payload)
    original_transaction_reference = _normalize_tef_original_reference_payload(payload)

    return await service.iniciar_fluxo_tef_funcao(
        function_id=int(function_id),
        valor=valor_float,
        cupom_fiscal=cupom_fiscal,
        data_fiscal=data_fiscal,
        hora_fiscal=hora_fiscal,
        trn_additional_parameters=payload.get("trn_additional_parameters"),
        trn_init_parameters=payload.get("trn_init_parameters"),
        session_parameters=payload.get("session_parameters"),
        cashier_operator=payload.get("cashier_operator"),
        sitef_ip=payload.get("sitef_ip"),
        store_id=payload.get("store_id"),
        terminal_id=payload.get("terminal_id"),
        justificativa=justificativa or None,
        original_transaction_reference=original_transaction_reference,
    )

@router.post("/tef/continuar", response_model=dict)
async def continuar_fluxo_tef(
    payload: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id e obrigatorio")
    return await service.continuar_fluxo_tef(
        session_id=str(session_id),
        continue_flag=int(payload.get("continue_flag", 0)),
        data=str(payload.get("data", "")),
    )

@router.post("/tef/finalizar", response_model=dict)
async def finalizar_fluxo_tef(
    payload: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    session_id = payload.get("session_id")
    reserva_id = payload.get("reserva_id")
    valor = payload.get("valor")
    function_id = payload.get("function_id", 0)
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id e obrigatorio")

    reserva_id_value = None
    if reserva_id is not None:
        try:
            reserva_id_value = int(reserva_id)
            if reserva_id_value <= 0:
                reserva_id_value = None
        except Exception:
            reserva_id_value = None

    valor_value = None
    if valor is not None:
        try:
            valor_value = float(valor)
        except Exception:
            valor_value = None
    param_fragments: list[str] = []

    param_adic_base = payload.get("param_adic")
    param_adic_base_str = str(param_adic_base or "")
    if param_adic_base:
        wrapped = _wrap_tef_param_fragment(param_adic_base)
        if wrapped:
            param_fragments.append(wrapped)

    nfpag_raw = payload.get("nfpag_raw")
    numero_pagamento_nfpag = payload.get("numero_pagamento_nfpag")
    nfpag_raw_str = str(nfpag_raw or "")

    if nfpag_raw and "NFPAG=" not in param_adic_base_str:
        if numero_pagamento_nfpag not in (None, "") and "NumeroPagamentoNFPAG=" not in param_adic_base_str and "NumeroPagamentoNFPAG=" not in nfpag_raw_str:
            wrapped_numero = _wrap_tef_param_fragment(numero_pagamento_nfpag, "NumeroPagamentoNFPAG=")
            if wrapped_numero:
                param_fragments.append(wrapped_numero)
        wrapped_nfpag = _wrap_tef_param_fragment(nfpag_raw, "NFPAG=")
        if wrapped_nfpag:
            param_fragments.append(wrapped_nfpag)

    param_adic = "".join(param_fragments) or None
    return await service.finalizar_fluxo_tef(
        reserva_id=reserva_id_value,
        valor=valor_value,
        session_id=str(session_id),
        confirm=bool(payload.get("confirm", True)),
        param_adic=str(param_adic) if param_adic else None,
    )

@router.post("/tef/cancelar", response_model=dict)
async def cancelar_fluxo_tef(
    payload: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id e obrigatorio")
    return await service.cancelar_fluxo_tef(session_id=str(session_id))

@router.delete("/tef/sessao", response_model=dict)
async def limpar_sessao_tef(
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    return await service.limpar_sessao_tef()

@router.post("/tef/cancelar-nsu", response_model=dict)
async def cancelar_pagamento_tef_nsu(
    payload: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    nsu = payload.get("nsu") or payload.get("cielo_payment_id")
    if not nsu:
        raise HTTPException(status_code=400, detail="nsu e obrigatorio")
    justificativa = (payload.get("justificativa") or "").strip()
    if not justificativa:
        raise HTTPException(status_code=400, detail="justificativa obrigatoria para cancelamento")
    print(f"[TEF] Justificativa cancelamento NSU {nsu}: {justificativa}")
    return await service.cancelar_pagamento_tef_nsu(str(nsu))

@router.post("/tef/pendencias", response_model=dict)
async def resolver_pendencias_tef(
    payload: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    confirmar_payload = payload.get("confirmar")
    if confirmar_payload is None:
        confirmar = settings.TEF_AUTO_RESOLVE_PENDING_CONFIRM
    else:
        confirmar = bool(confirmar_payload)
    return await service.resolver_pendencias_tef(confirmar=confirmar)

@router.get("/tef/pendencias/status", response_model=dict)
async def status_pendencias_tef(
    clear: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    from app.services.tef_service import get_pending_status

    status = get_pending_status(clear=clear)
    default_action = "confirm" if settings.TEF_AUTO_RESOLVE_PENDING_CONFIRM else "undo"
    return {"success": True, "default_action": default_action, **status}

@router.post("/tef/enviar-comprovante", response_model=dict)
async def enviar_comprovante_tef(
    payload: dict,
    current_user: User = Depends(get_current_active_user)
):
    email = (payload.get("email") or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="email e obrigatorio")

    cupom_cliente = payload.get("cupom_cliente") or ""
    cupom_estabelecimento = payload.get("cupom_estabelecimento") or ""
    nsu = payload.get("nsu")
    autorizacao = payload.get("autorizacao")

    email_service = EmailService()
    enviado = await email_service.enviar_comprovante_tef(
        email=email,
        cupom_cliente=cupom_cliente,
        cupom_estabelecimento=cupom_estabelecimento,
        nsu=nsu,
        autorizacao=autorizacao,
    )
    if not enviado:
        raise HTTPException(status_code=400, detail="Falha ao enviar comprovante TEF")

    return {"success": True}

@router.post("/tef/enviar-sms", response_model=dict)
async def enviar_comprovante_tef_sms(
    payload: dict,
    current_user: User = Depends(get_current_active_user)
):
    telefone = (payload.get("telefone") or "").strip()
    if not telefone:
        raise HTTPException(status_code=400, detail="telefone e obrigatorio")

    cupom_cliente = payload.get("cupom_cliente") or ""
    cupom_estabelecimento = payload.get("cupom_estabelecimento") or ""
    nsu = payload.get("nsu")
    autorizacao = payload.get("autorizacao")

    sms_service = SMSService()
    envio = sms_service.enviar_comprovante_tef(
        telefone=telefone,
        cupom_cliente=cupom_cliente,
        cupom_estabelecimento=cupom_estabelecimento,
        nsu=nsu,
        autorizacao=autorizacao,
    )
    if not envio.get("success"):
        raise HTTPException(status_code=400, detail=envio.get("error") or "Falha ao enviar SMS")

    return {"success": True, "detail": envio}

@router.get("/{pagamento_id}", response_model=PagamentoResponse)
async def obter_pagamento(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Obter pagamento por ID - Requer autenticaÃ§Ã£o"""
    return await service.get_by_id(pagamento_id)

@router.get("/cielo/{payment_id}", response_model=PagamentoResponse)
async def obter_pagamento_por_cielo_id(
    payment_id: str,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Obter pagamento pelo ID da Cielo - Requer autenticaÃ§Ã£o"""
    return await service.get_by_payment_id(payment_id)

@router.get("/reserva/{reserva_id}", response_model=List[PagamentoResponse])
async def listar_pagamentos_reserva(
    reserva_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Listar pagamentos de uma reserva - Requer autenticaÃ§Ã£o"""
    return await service.list_by_reserva(reserva_id)

@router.post("/{pagamento_id}/cancelar", response_model=PagamentoResponse, deprecated=True)
async def cancelar_pagamento_legacy(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """[DEPRECATED] Use PATCH /{pagamento_id} com status='CANCELADO'"""
    return await service.cancelar_pagamento(pagamento_id)

@router.get("/{pagamento_id}/status", response_model=dict)
async def verificar_status_pagamento(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Verificar status de pagamento PIX - Requer autenticaÃ§Ã£o"""
    return await service.verificar_status_pix(pagamento_id)

@router.post("/{pagamento_id}/confirmar-pix", response_model=dict)
async def confirmar_pix_manual(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """Confirmar pagamento PIX manualmente (sandbox/testes) - Requer ADMIN ou GERENTE"""
    return await service.confirmar_pix_manual(pagamento_id)

@router.patch("/{pagamento_id}", response_model=PagamentoResponse)
async def atualizar_pagamento_parcial(
    pagamento_id: int,
    pagamento_data: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Atualizar pagamento parcialmente (REST-compliant)
    
    OperaÃ§Ãµes suportadas:
    - {"status": "CANCELADO"} - Cancelar pagamento
    - {"status": "APROVADO"} - Aprovar pagamento e creditar pontos
    """
    if "status" in pagamento_data:
        status = pagamento_data["status"]
        if status == "CANCELADO":
            return await service.cancelar_pagamento(pagamento_id)
        elif status == "APROVADO":
            return await service.aprovar_pagamento(pagamento_id)
    
    raise HTTPException(status_code=400, detail="OperaÃ§Ã£o nÃ£o suportada. Use status='APROVADO' ou status='CANCELADO'")


@router.post("/{pagamento_id}/aprovar", response_model=PagamentoResponse)
async def aprovar_pagamento(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Aprovar pagamento manualmente e creditar pontos automaticamente.
    
    Este endpoint:
    1. Atualiza o status do pagamento para APROVADO
    2. Confirma a reserva associada
    3. Credita pontos de fidelidade ao cliente (1 ponto por R$ 10)
    4. Gera voucher automaticamente
    
    Requer: ADMIN ou GERENTE
    """
    return await service.aprovar_pagamento(pagamento_id)

# Webhook da Cielo
@router.post("/webhook/cielo", response_model=PagamentoResponse)
async def cielo_webhook(
    request: Request,
    webhook_data: CieloWebhook,
    service: PagamentoService = Depends(get_pagamento_service)
):
    """
    Processar webhook da Cielo
    
    SEGURANÃ‡A: Em produÃ§Ã£o, valida se a requisiÃ§Ã£o vem de IPs autorizados da Cielo.
    Em sandbox, permite qualquer IP para facilitar testes.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    if not is_cielo_ip_allowed(client_ip):
        raise HTTPException(
            status_code=403, 
            detail=f"IP {client_ip} nÃ£o autorizado para webhooks Cielo"
        )
    
    return await service.process_webhook(webhook_data)





