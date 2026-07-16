import logging
import os
import re
from typing import Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.core.database import get_db
from app.services.checkin_cash_approval_service import CheckinCashApprovalService
from app.services.whatsapp_service import get_whatsapp_service

try:
    from twilio.request_validator import RequestValidator
except ImportError:
    RequestValidator = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio/whatsapp", tags=["twilio-whatsapp"])

# ButtonPayload dos botoes do template TEMPLATE_CHECKIN_DINHEIRO_GERENTE.
# Meta nao permite variavel em botao, entao os ids sao fixos (chk_aprovar /
# chk_recusar) e o codigo CHK e resolvido pelo OriginalRepliedMessageSid.
# O sufixo _CHK-XXXX opcional cobre resposta digitada manualmente.
_CHK_ACTION_RE = re.compile(r"^chk_(aprovar|recusar)(?:_(CHK-[A-Z0-9]+))?$", re.IGNORECASE)


async def _read_twilio_form(request: Request) -> dict:
    body = await request.body()
    parsed = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def _twiml(mensagem: str) -> Response:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{mensagem}</Message></Response>"
    )
    return Response(content=xml, media_type="application/xml")


def _twilio_signature_valida(request: Request, params: dict) -> bool:
    """Valida X-Twilio-Signature. Sem o auth token (ou sem a lib) nao ha como
    validar — retorna False e as acoes CHK nao sao executadas."""
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not auth_token or RequestValidator is None:
        return False
    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        return False
    validator = RequestValidator(auth_token)
    # Atras do proxy a URL vista pelo Twilio e a publica; reconstruimos as
    # candidatas a partir dos headers forwarded e validamos contra todas.
    candidatas = {str(request.url)}
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if host:
        query = f"?{request.url.query}" if request.url.query else ""
        candidatas.add(f"{proto}://{host}{request.url.path}{query}")
        candidatas.add(f"https://{host}{request.url.path}{query}")
    return any(validator.validate(url, params, signature) for url in candidatas)


def _numero_e_gerente(from_number: str) -> bool:
    digits = "".join(filter(str.isdigit, from_number or ""))
    if not digits:
        return False
    for numero in get_whatsapp_service().gerente_numbers:
        if "".join(filter(str.isdigit, numero)) == digits:
            return True
    return False


def _extrair_acao_chk(payload: dict) -> Optional[tuple]:
    """Retorna (acao, codigo|None) se a mensagem for resposta dos botoes de
    aprovacao de check-in em dinheiro."""
    for campo in (payload.get("ButtonPayload"), payload.get("Body")):
        match = _CHK_ACTION_RE.match((campo or "").strip())
        if match:
            codigo = match.group(2)
            return match.group(1).lower(), codigo.upper() if codigo else None
    return None


async def _resolver_codigo_chk(service: CheckinCashApprovalService, payload: dict) -> Optional[str]:
    codigo = await service.encontrar_codigo_por_message_sid(
        payload.get("OriginalRepliedMessageSid", "")
    )
    if codigo:
        return codigo
    return await service.codigo_pendente_unico()


async def _processar_acao_gerente(acao: str, codigo: str) -> str:
    service = CheckinCashApprovalService(get_db())
    try:
        if acao == "aprovar":
            resultado = await service.aprovar(codigo)
            return (
                f"✅ Check-in {resultado['approval_code']} APROVADO. "
                "A recepcao ja pode concluir o check-in em dinheiro."
            )
        resultado = await service.recusar(codigo, motivo="recusado pelo gerente via WhatsApp")
        return (
            f"❌ Check-in {resultado['approval_code']} RECUSADO. "
            "A recepcao sera orientada a nao aceitar o pagamento em dinheiro."
        )
    except HTTPException as exc:
        return f"⚠️ Nao foi possivel processar {codigo}: {exc.detail}"
    except Exception:
        logger.exception("Erro ao processar acao CHK do gerente")
        return f"⚠️ Erro interno ao processar {codigo}. Use o painel de aprovacoes."


@router.post("/incoming")
async def whatsapp_incoming(request: Request):
    payload = await _read_twilio_form(request)
    logger.info(
        "[TWILIO WHATSAPP INCOMING] from=%s to=%s sid=%s button=%s body=%s",
        payload.get("From"),
        payload.get("To"),
        payload.get("MessageSid"),
        payload.get("ButtonPayload"),
        payload.get("Body"),
    )

    acao_chk = _extrair_acao_chk(payload)
    if acao_chk:
        if not _twilio_signature_valida(request, payload):
            logger.warning("Acao CHK ignorada: assinatura Twilio invalida ou ausente")
            return _twiml("Nao foi possivel validar a origem da mensagem.")
        if not _numero_e_gerente(payload.get("From", "")):
            logger.warning("Acao CHK ignorada: remetente %s nao e gerente", payload.get("From"))
            return _twiml("Este numero nao tem permissao para aprovar check-ins.")
        acao, codigo = acao_chk
        if not codigo:
            codigo = await _resolver_codigo_chk(CheckinCashApprovalService(get_db()), payload)
        if not codigo:
            return _twiml(
                "Nao consegui identificar qual check-in essa resposta aprova. "
                "Responda tocando no botao da mensagem original ou use o painel de aprovacoes."
            )
        return _twiml(await _processar_acao_gerente(acao, codigo))

    return _twiml("Recebemos sua mensagem. As notificacoes do Hotel Real Cabo Frio estao ativas.")


@router.post("/status")
async def whatsapp_status_callback(request: Request):
    payload = await _read_twilio_form(request)
    logger.info(
        "[TWILIO WHATSAPP STATUS] sid=%s status=%s error_code=%s error_message=%s to=%s",
        payload.get("MessageSid"),
        payload.get("MessageStatus") or payload.get("SmsStatus"),
        payload.get("ErrorCode"),
        payload.get("ErrorMessage"),
        payload.get("To"),
    )
    return {"success": True}
