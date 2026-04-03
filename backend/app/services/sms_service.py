import requests
from typing import Any, Dict

from app.core.config import settings


class SMSService:
    def __init__(self) -> None:
        self.account_sid = settings.SMS_TWILIO_ACCOUNT_SID
        self.auth_token = settings.SMS_TWILIO_AUTH_TOKEN
        self.from_number = settings.SMS_TWILIO_FROM_NUMBER

    @property
    def enabled(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    def enviar_comprovante_tef(
        self,
        telefone: str,
        cupom_cliente: str | None = None,
        cupom_estabelecimento: str | None = None,
        nsu: str | None = None,
        autorizacao: str | None = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "success": False,
                "error": "SMS nao configurado (Twilio)",
            }

        body_parts = ["Comprovante TEF"]
        if nsu:
            body_parts.append(f"NSU {nsu}")
        if autorizacao:
            body_parts.append(f"AUT {autorizacao}")

        cupom = (cupom_cliente or cupom_estabelecimento or "").strip()
        if cupom:
            cupom_linhas = " ".join(line.strip() for line in cupom.splitlines() if line.strip())
            if len(cupom_linhas) > 120:
                cupom_linhas = cupom_linhas[:117] + "..."
            body_parts.append(cupom_linhas)

        body = " | ".join(body_parts)

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        data = {
            "From": self.from_number,
            "To": telefone,
            "Body": body,
        }
        try:
            response = requests.post(url, data=data, auth=(self.account_sid, self.auth_token), timeout=30)
            response.raise_for_status()
            payload = response.json()
            return {
                "success": True,
                "sid": payload.get("sid"),
                "status": payload.get("status"),
            }
        except requests.RequestException as exc:
            return {
                "success": False,
                "error": f"Falha ao enviar SMS: {exc}",
            }
