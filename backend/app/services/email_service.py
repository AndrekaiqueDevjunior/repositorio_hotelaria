import os
from typing import Any, Dict, Optional

import httpx


class EmailService:
    """Envio simples de emails transacionais via SendGrid."""

    SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self) -> None:
        self.api_key = (os.getenv("SENDGRID_API_KEY") or "").strip()
        self.from_email = (os.getenv("SENDGRID_FROM_EMAIL") or "").strip()
        self.from_name = (os.getenv("SENDGRID_FROM_NAME") or "Hotel Real Cabo Frio").strip()
        self.reservas_to_email = (os.getenv("SENDGRID_RESERVAS_TO_EMAIL") or "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.from_email and self.reservas_to_email)

    async def enviar_notificacao_nova_reserva(
        self,
        reserva: Dict[str, Any],
        cliente: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not self.enabled:
            print("[EMAIL] SendGrid desabilitado: variaveis de ambiente ausentes")
            return False

        codigo = reserva.get("codigo_reserva") or f"RES-{reserva.get('id')}"
        status = reserva.get("status") or "PENDENTE"
        quarto = reserva.get("quarto_numero") or "N/A"
        suite = reserva.get("tipo_suite") or "N/A"
        checkin = reserva.get("checkin_previsto") or "-"
        checkout = reserva.get("checkout_previsto") or "-"
        valor_total = reserva.get("valor_total") or 0
        cliente_nome = (
            (cliente or {}).get("nome_completo")
            or reserva.get("cliente_nome")
            or "Cliente nao identificado"
        )
        cliente_email = (cliente or {}).get("email") or "-"
        cliente_telefone = (cliente or {}).get("telefone") or "-"
        cliente_documento = (cliente or {}).get("documento") or "-"

        subject = f"Nova reserva recebida - {codigo}"
        text_content = (
            "Ola Hotel Real Cabo Frio,\n\n"
            "Uma nova reserva foi recebida.\n\n"
            f"Codigo: {codigo}\n"
            f"Status: {status}\n"
            f"Quarto: {quarto}\n"
            f"Suite: {suite}\n"
            f"Check-in: {checkin}\n"
            f"Check-out: {checkout}\n"
            f"Valor total: R$ {valor_total:.2f}\n\n"
            f"Cliente: {cliente_nome}\n"
            f"Documento: {cliente_documento}\n"
            f"Email: {cliente_email}\n"
            f"Telefone: {cliente_telefone}\n"
        )
        html_content = f"""
        <div style="font-family:Arial,sans-serif;line-height:1.5;color:#1f2937">
          <h2 style="margin-bottom:8px">Nova reserva recebida</h2>
          <p><strong>Codigo:</strong> {codigo}</p>
          <p><strong>Status:</strong> {status}</p>
          <p><strong>Quarto:</strong> {quarto}</p>
          <p><strong>Suite:</strong> {suite}</p>
          <p><strong>Check-in:</strong> {checkin}</p>
          <p><strong>Check-out:</strong> {checkout}</p>
          <p><strong>Valor total:</strong> R$ {float(valor_total):.2f}</p>
          <hr style="margin:16px 0" />
          <p><strong>Cliente:</strong> {cliente_nome}</p>
          <p><strong>Documento:</strong> {cliente_documento}</p>
          <p><strong>Email:</strong> {cliente_email}</p>
          <p><strong>Telefone:</strong> {cliente_telefone}</p>
        </div>
        """

        payload = {
            "personalizations": [
                {
                    "to": [{"email": self.reservas_to_email}],
                    "subject": subject,
                }
            ],
            "from": {
                "email": self.from_email,
                "name": self.from_name,
            },
            "content": [
                {"type": "text/plain", "value": text_content},
                {"type": "text/html", "value": html_content},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.SENDGRID_URL, headers=headers, json=payload)

            if response.status_code >= 400:
                print(f"[EMAIL] Erro SendGrid {response.status_code}: {response.text[:500]}")
                return False

            print(f"[EMAIL] Notificacao de nova reserva enviada para {self.reservas_to_email}")
            return True
        except Exception as exc:
            print(f"[EMAIL] Falha ao enviar email de reserva: {exc}")
            return False
