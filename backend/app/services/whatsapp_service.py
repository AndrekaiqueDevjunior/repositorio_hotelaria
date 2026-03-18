"""
Servico de notificacao via WhatsApp usando Twilio.
"""

import logging
import os
from typing import Any, Dict, Optional

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Servico para envio de mensagens via WhatsApp usando Twilio.

    Variaveis de ambiente esperadas:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_WHATSAPP_FROM
    - WHATSAPP_NOTIFICACAO_NUMERO
    - TWILIO_WHATSAPP_ENABLED
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self.notification_number = os.getenv("WHATSAPP_NOTIFICACAO_NUMERO", "+5511968029600")
        self.enabled = os.getenv("TWILIO_WHATSAPP_ENABLED", "true").lower() == "true"
        self.frontend_base_url = (os.getenv("FRONTEND_BASE_URL") or "").strip().rstrip("/")

        if not self.enabled:
            logger.warning("Twilio WhatsApp desabilitado por configuracao")
            self.client = None
        elif not self.account_sid or not self.auth_token:
            logger.warning("Twilio nao configurado. Defina TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN.")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("WhatsApp Service inicializado com sucesso")
            except Exception as exc:
                logger.error("Erro ao inicializar Twilio Client: %s", exc)
                self.client = None

    def _format_phone_number(self, phone: str) -> str:
        phone = (phone or "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not phone.startswith("+") and not phone.startswith("whatsapp:"):
            phone = f"+{phone}"
        if not phone.startswith("whatsapp:"):
            phone = f"whatsapp:{phone}"
        return phone

    def _build_link(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        if not self.frontend_base_url:
            return ""
        path = path or ""
        if not path.startswith("/"):
            path = f"/{path}"
        base = f"{self.frontend_base_url}{path}"
        if not params:
            return base
        parts = []
        for key, value in params.items():
            if value is None or value == "":
                continue
            parts.append(f"{key}={value}")
        if not parts:
            return base
        return f"{base}?{'&'.join(parts)}"

    async def _send_message(self, to_number: str, mensagem: str) -> Dict[str, Any]:
        if not self.client:
            return {
                "success": False,
                "error": "Servico WhatsApp nao configurado",
            }

        try:
            to_formatted = self._format_phone_number(to_number)
            message = self.client.messages.create(
                body=mensagem,
                from_=self.whatsapp_from,
                to=to_formatted,
            )
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_formatted,
            }
        except TwilioRestException as exc:
            logger.error("Erro Twilio ao enviar WhatsApp: %s - %s", exc.code, exc.msg)
            return {
                "success": False,
                "error": f"Erro Twilio: {exc.msg}",
                "error_code": exc.code,
            }
        except Exception as exc:
            logger.error("Erro ao enviar WhatsApp: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }

    async def enviar_mensagem_customizada(self, to_number: str, mensagem: str) -> Dict[str, Any]:
        return await self._send_message(to_number, mensagem)

    async def enviar_notificacao_resgate_premio(
        self,
        cliente_nome: str,
        cliente_telefone: Optional[str],
        cliente_endereco: Optional[str],
        premio_nome: str,
        pontos_usados: int,
        codigo_resgate: str,
    ) -> Dict[str, Any]:
        endereco_texto = cliente_endereco or "Endereco nao informado"
        telefone_texto = cliente_telefone or "Telefone nao informado"
        mensagem = (
            "Novo resgate de premio\n\n"
            f"Cliente: {cliente_nome}\n"
            f"Telefone: {telefone_texto}\n"
            f"Endereco: {endereco_texto}\n"
            f"Premio: {premio_nome}\n"
            f"Pontos usados: {pontos_usados}\n"
            f"Codigo do resgate: {codigo_resgate}"
        )
        return await self._send_message(self.notification_number, mensagem)

    async def enviar_notificacao_nova_reserva(
        self,
        cliente_nome: str,
        codigo_reserva: str,
        quarto_numero: str,
        checkin_previsto: str,
        checkout_previsto: str,
        valor_total: float,
        status: str,
        reserva_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        link_reservas = (
            self._build_link(f"/reservas/{reserva_id}") if reserva_id else self._build_link("/reservas")
        )
        mensagem = (
            "Nova reserva recebida\n\n"
            f"Codigo: {codigo_reserva}\n"
            f"Cliente: {cliente_nome}\n"
            f"Quarto: {quarto_numero}\n"
            f"Check-in: {checkin_previsto}\n"
            f"Check-out: {checkout_previsto}\n"
            f"Valor: R$ {float(valor_total or 0):.2f}\n"
            f"Status: {status}"
        )
        if link_reservas:
            mensagem += f"\n\nAcessar: {link_reservas}"
        return await self._send_message(self.notification_number, mensagem)

    async def enviar_notificacao_pagamento(
        self,
        evento: str,
        codigo_reserva: str,
        cliente_nome: str,
        valor: float,
        metodo: Optional[str] = None,
        status: Optional[str] = None,
        nsu: Optional[str] = None,
        reserva_id: Optional[int] = None,
        pagamento_id: Optional[int] = None,
        tef_nsu: Optional[str] = None,
        tef_autorizacao: Optional[str] = None,
        tef_cupom_cliente_arquivo: Optional[str] = None,
        tef_cupom_estabelecimento_arquivo: Optional[str] = None,
    ) -> Dict[str, Any]:
        linhas = [
            f"Pagamento {evento}",
            "",
            f"Reserva: {codigo_reserva}",
            f"Cliente: {cliente_nome}",
            f"Valor: R$ {float(valor or 0):.2f}",
        ]
        if metodo:
            linhas.append(f"Metodo: {metodo}")
        if status:
            linhas.append(f"Status: {status}")
        if nsu:
            linhas.append(f"NSU: {nsu}")
        if (metodo or "").lower() == "tef" or tef_nsu or tef_autorizacao:
            if tef_nsu:
                linhas.append(f"TEF NSU: {tef_nsu}")
            if tef_autorizacao:
                linhas.append(f"TEF Autorizacao: {tef_autorizacao}")
            if tef_cupom_cliente_arquivo:
                linhas.append("Cupom Cliente: disponivel")
            if tef_cupom_estabelecimento_arquivo:
                linhas.append("Cupom Estabelecimento: disponivel")
        link_pagamentos = (
            self._build_link(f"/reservas/{reserva_id}") if reserva_id else self._build_link("/pagamentos")
        )
        link_comprovantes = self._build_link("/comprovantes", {"pagamentoId": pagamento_id})
        if link_pagamentos:
            linhas.append(f"Acessar reserva: {link_pagamentos}")
        if link_comprovantes:
            linhas.append(f"Acessar comprovantes: {link_comprovantes}")
        mensagem = "\n".join(linhas)
        return await self._send_message(self.notification_number, mensagem)

    async def enviar_notificacao_evento_reserva(
        self,
        evento: str,
        codigo_reserva: str,
        cliente_nome: str,
        quarto_numero: str,
        checkin_previsto: str,
        checkout_previsto: str,
        valor_total: float,
        status: str,
        detalhe: Optional[str] = None,
        reserva_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        linhas = [
            f"Reserva {evento}",
            "",
            f"Codigo: {codigo_reserva}",
            f"Cliente: {cliente_nome}",
            f"Quarto: {quarto_numero}",
            f"Check-in: {checkin_previsto}",
            f"Check-out: {checkout_previsto}",
            f"Valor: R$ {float(valor_total or 0):.2f}",
            f"Status: {status}",
        ]
        if detalhe:
            linhas.extend(["", f"Detalhe: {detalhe}"])
        link_reservas = (
            self._build_link(f"/reservas/{reserva_id}") if reserva_id else self._build_link("/reservas")
        )
        if link_reservas:
            linhas.extend(["", f"Acessar: {link_reservas}"])
        mensagem = "\n".join(linhas)
        return await self._send_message(self.notification_number, mensagem)


_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
