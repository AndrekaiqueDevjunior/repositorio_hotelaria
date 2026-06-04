from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import Response


router = APIRouter(prefix="/twilio/whatsapp", tags=["twilio-whatsapp"])


async def _read_twilio_form(request: Request) -> dict:
    body = await request.body()
    parsed = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


@router.post("/incoming")
async def whatsapp_incoming(request: Request):
    payload = await _read_twilio_form(request)
    print(
        "[TWILIO WHATSAPP INCOMING] "
        f"from={payload.get('From')} "
        f"to={payload.get('To')} "
        f"sid={payload.get('MessageSid')} "
        f"body={payload.get('Body')}"
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Message>Recebemos sua mensagem. As notificacoes do Hotel Real Cabo Frio estao ativas.</Message>"
        "</Response>"
    )
    return Response(content=xml, media_type="application/xml")


@router.post("/status")
async def whatsapp_status_callback(request: Request):
    payload = await _read_twilio_form(request)
    print(
        "[TWILIO WHATSAPP STATUS] "
        f"sid={payload.get('MessageSid')} "
        f"status={payload.get('MessageStatus') or payload.get('SmsStatus')} "
        f"error_code={payload.get('ErrorCode')} "
        f"error_message={payload.get('ErrorMessage')} "
        f"to={payload.get('To')}"
    )
    return {"success": True}
