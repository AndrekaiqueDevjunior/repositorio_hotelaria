"""
Servico de notificacao via WhatsApp usando Twilio.
"""

import json
import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import quote

try:
    from twilio.base.exceptions import TwilioRestException
    from twilio.rest import Client
except ImportError:
    class TwilioRestException(Exception):
        pass

    Client = None

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

    Templates aprovados na Meta (Twilio Content Template Builder), usados para
    mensagens business-initiated fora da janela de 24h (texto livre nao e
    entregue nesse caso, ver erro Twilio 63016).
    """

    TEMPLATE_OTP_VERIFICACAO = "HX5224e5dd334ce1e04727b0506dc4a2f1"
    TEMPLATE_RESERVA_CONFIRMADA = "HXf7faf468de05d8b6687daa8d70089706"
    TEMPLATE_CHECKOUT_REALIZADO = "HX16be141501348ff38bb8ea9a2a3ec205"
    TEMPLATE_PONTOS_LIBERADOS = "HX2591833437a282a67ee2b028c7a6131f"
    TEMPLATE_PREMIO_PROXIMO = "HXa31198da96e972a3d6918d942a135007"
    TEMPLATE_RESGATE_CONFIRMADO = "HXe3eaeffda34a120a36b37f10baf54c2f"

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        # Aceita um ou varios numeros separados por virgula (todos recebem as
        # notificacoes internas do hotel: nova reserva, checkout, etc.)
        _raw_numeros = os.getenv("WHATSAPP_NOTIFICACAO_NUMERO", "+5511968029600")
        self.notification_numbers = [n.strip() for n in _raw_numeros.split(",") if n.strip()]
        # Numero principal (compatibilidade com codigo existente)
        self.notification_number = self.notification_numbers[0] if self.notification_numbers else ""
        self.enabled = os.getenv("TWILIO_WHATSAPP_ENABLED", "true").lower() == "true"
        self.frontend_base_url = (os.getenv("FRONTEND_BASE_URL") or "").strip().rstrip("/")

        if not self.enabled:
            logger.warning("Twilio WhatsApp desabilitado por configuracao")
            self.client = None
        elif Client is None:
            logger.warning("Twilio nao instalado. WhatsApp desabilitado.")
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
        digits = "".join(filter(str.isdigit, phone))
        if not phone.startswith("+") and not phone.startswith("whatsapp:") and len(digits) in (10, 11):
            phone = f"+55{digits}"
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
            parts.append(f"{quote(str(key))}={quote(str(value))}")
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

    async def _send_notification(self, mensagem: str) -> Dict[str, Any]:
        """Envia a mensagem para TODOS os numeros de notificacao configurados.

        Retorna o resultado do primeiro envio (compatibilidade) e a lista
        completa de resultados em `resultados`.
        """
        numeros = self.notification_numbers or ([self.notification_number] if self.notification_number else [])
        if not numeros:
            return {"success": False, "error": "Nenhum numero de notificacao configurado"}

        resultados = []
        for numero in numeros:
            resultados.append(await self._send_message(numero, mensagem))

        principal = resultados[0]
        principal["resultados"] = resultados
        principal["success"] = any(r.get("success") for r in resultados)
        return principal

    async def _send_template(
        self,
        to_number: str,
        content_sid: str,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.client:
            return {
                "success": False,
                "error": "Servico WhatsApp nao configurado",
            }

        try:
            to_formatted = self._format_phone_number(to_number)
            message = self.client.messages.create(
                from_=self.whatsapp_from,
                to=to_formatted,
                content_sid=content_sid,
                content_variables=json.dumps({str(k): str(v) for k, v in variables.items()}),
            )
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_formatted,
            }
        except TwilioRestException as exc:
            logger.error("Erro Twilio ao enviar template WhatsApp: %s - %s", exc.code, exc.msg)
            return {
                "success": False,
                "error": f"Erro Twilio: {exc.msg}",
                "error_code": exc.code,
            }
        except Exception as exc:
            logger.error("Erro ao enviar template WhatsApp: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }

    async def enviar_mensagem_customizada(self, to_number: str, mensagem: str) -> Dict[str, Any]:
        return await self._send_message(to_number, mensagem)

    def montar_link_convite_real(self, codigo: str) -> str:
        return self._build_link("/reservar", {"cupom": codigo, "origem": "convite_real"})

    def montar_mensagem_convite_real(self, link: str) -> str:
        return (
            "Tô na Jornada Real do Hotel Real 😮\n"
            "Se você reservar por esse link, a gente ganha benefícios\n"
            f"👉 {link}\n"
            "Depois me conta 🔥"
        )

    def montar_whatsapp_share_url(self, mensagem: str) -> str:
        return f"https://wa.me/?text={quote(mensagem)}"

    async def enviar_convite_real(
        self,
        telefone_destino: str,
        codigo: str,
        link: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not telefone_destino:
            return {"success": False, "error": "Telefone de destino nao informado"}
        link_final = link or self.montar_link_convite_real(codigo)
        mensagem = self.montar_mensagem_convite_real(link_final)
        return await self._send_message(telefone_destino, mensagem)

    async def enviar_otp_verificacao(self, telefone_destino: str, codigo: str) -> Dict[str, Any]:
        if not telefone_destino:
            return {"success": False, "error": "Telefone de destino nao informado"}
        return await self._send_template(
            telefone_destino,
            self.TEMPLATE_OTP_VERIFICACAO,
            {"1": codigo},
        )

    async def enviar_aviso_premio_proximo(
        self,
        cliente_telefone: Optional[str],
        documento: Optional[str],
        cliente_nome: Optional[str] = None,
        premio_nome: Optional[str] = None,
        saldo_atual: Optional[int] = None,
        pontos_faltantes: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not cliente_telefone:
            return {"success": False, "error": "Cliente sem telefone"}

        return await self._send_template(
            cliente_telefone,
            self.TEMPLATE_PREMIO_PROXIMO,
            {
                "1": str(int(pontos_faltantes or 0)),
                "2": premio_nome or "seu próximo prêmio",
                "3": str(int(saldo_atual or 0)),
                "4": (documento or "").strip(),
            },
        )

    async def enviar_confirmacao_checkin_dinheiro(
        self,
        codigo_reserva: str,
        cliente_nome: str,
        valor: float,
        comprovante_id: Optional[int] = None,
        reserva_id: Optional[int] = None,
        approval_code: Optional[str] = None,
        approval_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        link_reserva = self._build_link(f"/reservas/{reserva_id}") if reserva_id else self._build_link("/reservas")
        link_comprovante = self._build_link("/comprovantes", {"comprovanteId": comprovante_id})
        link_aprovacao = approval_url or self._build_link("/checkin-approvals", {"code": approval_code})
        linhas = [
            "Pagamento em dinheiro aguardando liberação de check-in",
            "",
            f"Reserva: {codigo_reserva}",
            f"Cliente: {cliente_nome}",
            f"Valor: R$ {float(valor or 0):.2f}",
            "Ação: conferir comprovante e liberar check-in no sistema.",
        ]
        if approval_code:
            linhas.append(f"Codigo: {approval_code}")
        if link_reserva:
            linhas.append(f"Reserva: {link_reserva}")
        if link_comprovante:
            linhas.append(f"Comprovante: {link_comprovante}")
        if link_aprovacao:
            linhas.append(f"Confirmar: {link_aprovacao}")
        return await self._send_notification("\n".join(linhas))

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
        return await self._send_notification(mensagem)

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
        return await self._send_notification(mensagem)

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
        return await self._send_notification(mensagem)

    async def enviar_notificacao_nova_reserva_admin(
        self,
        codigo_reserva: str,
        cliente_nome: str,
        quarto_numero: str,
        tipo_suite: Optional[str],
        checkin_previsto: str,
        checkout_previsto: str,
        valor_total: float,
    ) -> Dict[str, Any]:
        """Alerta interno de nova reserva para os numeros de notificacao do hotel.

        Mensagem de texto livre business-initiated fora da janela de 24h cai em
        undelivered (erro Twilio 63016) no WhatsApp Business real -- confirmado
        via Twilio API que todos os alertas recentes para o numero do hotel
        estavam nesse estado. Reaproveita o Content Template ja aprovado pela
        Meta 'reserva_confirmada' (TEMPLATE_RESERVA_CONFIRMADA), que so tem 5
        variaveis fixas (codigo/checkin/checkout/suite/valor) -- nome do
        cliente e numero do quarto sao combinados nos slots existentes.
        """
        numeros = self.notification_numbers or ([self.notification_number] if self.notification_number else [])
        if not numeros:
            return {"success": False, "error": "Nenhum numero de notificacao configurado"}

        variables = {
            "1": f"{codigo_reserva} - {cliente_nome}",
            "2": checkin_previsto,
            "3": checkout_previsto,
            "4": f"{tipo_suite or '-'} (Quarto {quarto_numero or '-'})",
            "5": f"{float(valor_total or 0):.2f}",
        }
        resultados = [
            await self._send_template(numero, self.TEMPLATE_RESERVA_CONFIRMADA, variables)
            for numero in numeros
        ]
        principal = resultados[0]
        principal["resultados"] = resultados
        principal["success"] = any(r.get("success") for r in resultados)
        return principal

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
        cliente_telefone: Optional[str] = None,
        cliente_email: Optional[str] = None,
        cliente_documento: Optional[str] = None,
        responsavel_nome: Optional[str] = None,
        tipo_suite: Optional[str] = None,
        num_diarias: Optional[int] = None,
        valor_diaria: Optional[float] = None,
        origem: Optional[str] = None,
        forma_pagamento: Optional[str] = None,
        observacoes: Optional[str] = None,
        cliente_id: Optional[int] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        criado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        if evento == "criada":
            return await self.enviar_notificacao_nova_reserva_admin(
                codigo_reserva=codigo_reserva,
                cliente_nome=cliente_nome,
                quarto_numero=quarto_numero,
                tipo_suite=tipo_suite,
                checkin_previsto=checkin_previsto,
                checkout_previsto=checkout_previsto,
                valor_total=valor_total,
            )

        linhas = [
            f"Reserva {evento}",
            "",
            f"Código: {codigo_reserva}",
            f"Cliente: {cliente_nome}",
            f"Tipo Suíte: {tipo_suite or '-'}",
            f"Check-in: {checkin_previsto}",
            f"Check-out: {checkout_previsto}",
            f"Valor: R$ {float(valor_total or 0):.2f}",
            f"Status: {status}",
            "",
            "👤 Informações do Cliente",
            f"Nome: {cliente_nome}",
        ]
        if cliente_id is not None:
            linhas.append(f"ID Cliente: {cliente_id}")

        linhas.extend([
            "",
            "🏠 Informações do Quarto",
            f"Quarto: {quarto_numero}",
            f"Tipo Suíte: {tipo_suite or '-'}",
            f"Diárias: {num_diarias if num_diarias is not None else '-'}",
            "",
            "📅 Datas da Reserva",
            "Check-in Previsto:",
            checkin_previsto,
            "Check-out Previsto:",
            checkout_previsto,
            "",
            "💰 Detalhes Financeiros",
        ])
        if valor_diaria is not None:
            linhas.append(f"Valor Diária: R$ {float(valor_diaria or 0):.2f}")
        linhas.extend([
            f"Nº Diárias: {num_diarias if num_diarias is not None else '-'}",
            f"Valor Total: R$ {float(valor_total or 0):.2f}",
            "",
            "⚙️ Informações de Sistema",
            f"ID Reserva: {reserva_id if reserva_id is not None else '-'}",
            f"Criado em: {created_at or '-'}",
            f"Atualizado em: {updated_at or '-'}",
            f"Criado por: {criado_por or '-'}",
        ])
        if detalhe:
            linhas.extend(["", f"Detalhe: {detalhe}"])
        link_reservas = (
            self._build_link(f"/reservas/{reserva_id}") if reserva_id else self._build_link("/reservas")
        )
        if link_reservas:
            linhas.extend(["", f"Acessar: {link_reservas}"])
        mensagem = "\n".join(linhas)
        return await self._send_notification(mensagem)

    async def enviar_pontos_pos_checkout(
        self,
        cliente_nome: str,
        cliente_telefone: Optional[str],
        documento: Optional[str],
        codigo_reserva: str,
        saldo_atual: int,
        pontos_ganhos_checkout: int = 0,
        faltam_pontos_para_proximo_premio: Optional[int] = None,
        proximo_premio_nome: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not cliente_telefone:
            return {"success": False, "error": "Cliente sem telefone"}

        # pontos_ganhos_checkout ja e o total de Pontos R creditados na
        # transacao (pontuacao-base * multiplicador do nivel), nao soma bonus
        # separado por cima para evitar contar o multiplicador em dobro.
        pontos_total_liberados = int(pontos_ganhos_checkout or 0)
        faltam = int(faltam_pontos_para_proximo_premio) if faltam_pontos_para_proximo_premio is not None else 0
        premio_nome = proximo_premio_nome or "seu próximo prêmio"

        return await self._send_template(
            cliente_telefone,
            self.TEMPLATE_PONTOS_LIBERADOS,
            {
                "1": codigo_reserva,
                "2": str(pontos_total_liberados),
                "3": str(int(saldo_atual or 0)),
                "4": str(max(0, faltam)),
                "5": premio_nome,
            },
        )


    async def enviar_notificacao_checkin_realizado(
        self,
        codigo_reserva: str,
        cliente_nome: str,
        quarto_numero: str,
        num_hospedes: Optional[int] = None,
        num_criancas: Optional[int] = None,
        placa_veiculo: Optional[str] = None,
        observacoes: Optional[str] = None,
        reserva_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        link_reserva = (
            self._build_link(f"/reservas/{reserva_id}") if reserva_id else self._build_link("/reservas")
        )
        linhas = [
            "Check-in realizado ✅",
            "",
            f"Reserva: {codigo_reserva}",
            f"Cliente: {cliente_nome}",
            f"Quarto: {quarto_numero}",
        ]
        if num_hospedes is not None:
            linhas.append(f"Hospedes: {num_hospedes}")
        if num_criancas:
            linhas.append(f"Criancas: {num_criancas}")
        if placa_veiculo:
            linhas.append(f"Placa: {placa_veiculo}")
        if observacoes:
            linhas.append(f"Observacoes: {observacoes}")
        if link_reserva:
            linhas.extend(["", f"Acessar: {link_reserva}"])
        return await self._send_notification("\n".join(linhas))

    async def enviar_confirmacao_resgate_cliente(
        self,
        cliente_telefone: Optional[str],
        premio_nome: str,
        codigo_resgate: str,
        pontos_usados: int,
        valido_ate: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not cliente_telefone:
            return {"success": False, "error": "Cliente sem telefone"}

        valido_ate_fmt = valido_ate or "-"
        if valido_ate:
            try:
                from datetime import datetime
                valido_ate_fmt = datetime.fromisoformat(valido_ate).strftime("%d/%m/%Y")
            except Exception:
                valido_ate_fmt = valido_ate

        return await self._send_template(
            cliente_telefone,
            self.TEMPLATE_RESGATE_CONFIRMADO,
            {
                "1": premio_nome,
                "2": codigo_resgate,
                "3": valido_ate_fmt,
            },
        )

    async def enviar_confirmacao_checkout_cliente(
        self,
        cliente_telefone: Optional[str],
        codigo_reserva: str,
        pontos_pendentes: int = 0,
    ) -> Dict[str, Any]:
        if not cliente_telefone:
            return {"success": False, "error": "Cliente sem telefone"}
        return await self._send_template(
            cliente_telefone,
            self.TEMPLATE_CHECKOUT_REALIZADO,
            {
                "1": codigo_reserva,
                "2": str(int(pontos_pendentes or 0)),
            },
        )

    async def enviar_confirmacao_reserva_cliente(
        self,
        cliente_telefone: Optional[str],
        codigo_reserva: str,
        checkin: str,
        checkout: str,
        tipo_suite: Optional[str] = None,
        valor_total: float = 0,
    ) -> Dict[str, Any]:
        if not cliente_telefone:
            return {"success": False, "error": "Cliente sem telefone"}
        return await self._send_template(
            cliente_telefone,
            self.TEMPLATE_RESERVA_CONFIRMADA,
            {
                "1": codigo_reserva,
                "2": checkin,
                "3": checkout,
                "4": tipo_suite or "-",
                "5": f"{float(valor_total or 0):.2f}",
            },
        )


_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
