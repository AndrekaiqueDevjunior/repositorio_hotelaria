import requests
from datetime import datetime
from typing import Any, Dict

from app.core.config import settings


TEF_INTERACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
INPUT_COMMANDS = {20, 21, 30, 31, 32, 33, 34, 35, 38}
AUTO_ADVANCE_COMMANDS = {0, 1, 2, 22, 23}


def _now_fiscal_date() -> str:
    now = datetime.now()
    return now.strftime("%Y%m%d")


def _now_fiscal_time() -> str:
    now = datetime.now()
    return now.strftime("%H%M%S")


class TefService:
    """
    Serviço de integração com CliSiTef para pagamentos TEF.
    """

    def __init__(self):
        self.agente_url = settings.TEF_AGENTE_URL.rstrip("/")
        self.timeout = settings.TEF_TIMEOUT

    def _request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        response = requests.request(
            method=method,
            url=f"{self.agente_url}{path}",
            json=payload or {},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _cleanup_remote_session(self) -> None:
        try:
            self._request("DELETE", "/session")
        except Exception:
            pass

    def _reset_local_interactive_sessions(self) -> None:
        TEF_INTERACTIVE_SESSIONS.clear()

    def _start_transaction(self, valor_centavos: int, tax_invoice_number: str, tax_invoice_date: str, tax_invoice_time: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/startTransaction",
            {
                "functionId": 3,
                "trnAmount": valor_centavos,
                "taxInvoiceNumber": tax_invoice_number,
                "taxInvoiceDate": tax_invoice_date,
                "taxInvoiceTime": tax_invoice_time,
            },
        )

    def _default_input_value(self, response: Dict[str, Any]) -> str:
        command_id = int(response.get("commandId") or 0)
        texto = str(response.get("data") or "").lower()

        if command_id == 20:
            return "0"
        if "vencimento" in texto or "mmaa" in texto:
            return "1228"
        if "seguranca" in texto or "cvv" in texto:
            return "123"
        if "forma de pagamento" in texto:
            return "1"
        if "numero do cartao" in texto:
            return "5385913424769600"
        return ""

    def _register_response(self, session_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        session = TEF_INTERACTIVE_SESSIONS[session_id]
        command_id = int(response.get("commandId") or 0)
        field_id = int(response.get("fieldId") or 0)
        data = response.get("data")

        session["last_response"] = response

        if command_id == 0 and field_id > 0:
            session["tipo_campos"].append(
                {
                    "TipoCampo": str(field_id),
                    "Valor": "" if data is None else str(data),
                }
            )

        if command_id == 0 and field_id == 121:
            session["cupom_estabelecimento"] = "" if data is None else str(data)
        elif command_id == 0 and field_id == 122:
            session["cupom_cliente"] = "" if data is None else str(data)
        elif field_id == 131 and data:
            session["nsu"] = str(data)
        elif field_id == 132 and data:
            session["autorizacao"] = str(data)

        return session

    def _build_interactive_payload(self, session_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        session = TEF_INTERACTIVE_SESSIONS[session_id]
        command_id = int(response.get("commandId") or 0)
        clisitef_status = int(response.get("clisitefStatus") or 0)
        prompt = str(response.get("data") or "")
        finish_required = clisitef_status != 10000
        aprovado = clisitef_status == 0

        return {
            "success": True,
            "session_id": session_id,
            "clisitef_status": clisitef_status,
            "service_status": int(response.get("serviceStatus") or 0),
            "requires_input": clisitef_status == 10000 and command_id in INPUT_COMMANDS,
            "finish_required": finish_required,
            "aprovado": aprovado,
            "command_id": command_id,
            "field_id": int(response.get("fieldId") or 0),
            "field_min_length": int(response.get("fieldMinLength") or 0),
            "field_max_length": int(response.get("fieldMaxLength") or 0),
            "prompt": prompt,
            "default_value": self._default_input_value(response),
            "message": prompt or ("Transacao Aprovada" if aprovado else "Transacao finalizada"),
            "nsu": session.get("nsu"),
            "autorizacao": session.get("autorizacao"),
            "cupom_cliente": session.get("cupom_cliente"),
            "cupom_estabelecimento": session.get("cupom_estabelecimento"),
            "tipo_campos": session.get("tipo_campos", []),
        }

    async def iniciar_pagamento(self, valor: float, reserva_id: int) -> Dict[str, Any]:
        """
        Fluxo legado headless, mantido para compatibilidade.
        """
        try:
            valor_centavos = int(valor * 100)
            response = self._request(
                "POST",
                "/pagamento",
                {
                    "valor": valor_centavos,
                    "reserva_id": reserva_id,
                    "tipo": "venda",
                },
            )

            return {
                "success": bool(response.get("success")),
                "status": "APROVADO" if response.get("aprovado") else "RECUSADO",
                "autorizacao": response.get("autorizacao"),
                "nsu": response.get("nsu"),
                "cupom_estabelecimento": response.get("cupom_estabelecimento"),
                "cupom_cliente": response.get("cupom_cliente"),
                "message": response.get("mensagem", "Pagamento processado"),
                "error": response.get("error"),
            }
        except requests.RequestException:
            return {
                "success": False,
                "status": "RECUSADO",
                "error": "Servico TEF indisponivel",
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Erro ao processar pagamento TEF: {exc}",
            }

    async def iniciar_fluxo_interativo(self, valor: float, reserva_id: int) -> Dict[str, Any]:
        valor_centavos = int(round(valor * 100))
        tax_invoice_number = str(int(datetime.now().timestamp()))
        tax_invoice_date = _now_fiscal_date()
        tax_invoice_time = _now_fiscal_time()

        try:
            start = self._start_transaction(
                valor_centavos=valor_centavos,
                tax_invoice_number=tax_invoice_number,
                tax_invoice_date=tax_invoice_date,
                tax_invoice_time=tax_invoice_time,
            )
        except requests.RequestException as exc:
            return {
                "success": False,
                "error": f"Falha ao iniciar TEF: {exc}",
            }

        if int(start.get("serviceStatus") or 0) == 98:
            self._cleanup_remote_session()
            self._reset_local_interactive_sessions()
            try:
                start = self._start_transaction(
                    valor_centavos=valor_centavos,
                    tax_invoice_number=tax_invoice_number,
                    tax_invoice_date=tax_invoice_date,
                    tax_invoice_time=tax_invoice_time,
                )
            except requests.RequestException as exc:
                return {
                    "success": False,
                    "error": f"Falha ao reiniciar TEF apos sessao ocupada: {exc}",
                }

        if int(start.get("serviceStatus") or 0) != 0:
            return {
                "success": False,
                "error": f"Agente retornou serviceStatus={start.get('serviceStatus')}",
                "detail": start,
            }

        if int(start.get("clisitefStatus") or 0) != 10000:
            return {
                "success": False,
                "error": f"CliSiTef nao iniciou fluxo interativo (status {start.get('clisitefStatus')})",
                "detail": start,
            }

        session_id = start.get("sessionId")
        if not session_id:
            return {
                "success": False,
                "error": "Agente nao retornou sessionId no startTransaction",
                "detail": start,
            }

        TEF_INTERACTIVE_SESSIONS[session_id] = {
            "session_id": session_id,
            "reserva_id": reserva_id,
            "valor": valor,
            "valor_centavos": valor_centavos,
            "tax_invoice_number": tax_invoice_number,
            "tax_invoice_date": tax_invoice_date,
            "tax_invoice_time": tax_invoice_time,
            "cupom_cliente": "",
            "cupom_estabelecimento": "",
            "nsu": None,
            "autorizacao": None,
            "tipo_campos": [],
            "last_response": None,
        }

        return await self.continuar_fluxo_interativo(session_id, continue_flag=0, data="")

    async def continuar_fluxo_interativo(
        self,
        session_id: str,
        continue_flag: int = 0,
        data: str = "",
    ) -> Dict[str, Any]:
        session = TEF_INTERACTIVE_SESSIONS.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Sessao TEF nao encontrada ou expirada",
            }

        next_continue = continue_flag
        next_data = "" if data is None else str(data)

        for _ in range(60):
            try:
                response = self._request(
                    "POST",
                    "/continueTransaction",
                    {
                        "sessionId": session_id,
                        "continue": next_continue,
                        "data": next_data,
                    },
                )
            except requests.RequestException as exc:
                return {
                    "success": False,
                    "error": f"Falha no continueTransaction: {exc}",
                }

            if int(response.get("serviceStatus") or 0) != 0:
                return {
                    "success": False,
                    "error": f"Erro no continueTransaction (serviceStatus={response.get('serviceStatus')})",
                    "detail": response,
                }

            session = self._register_response(session_id, response)
            clisitef_status = int(response.get("clisitefStatus") or 0)
            command_id = int(response.get("commandId") or 0)
            field_id = int(response.get("fieldId") or 0)

            if clisitef_status != 10000:
                session["aprovado_pre_finish"] = clisitef_status == 0
                return self._build_interactive_payload(session_id, response)

            if command_id in INPUT_COMMANDS:
                return self._build_interactive_payload(session_id, response)

            if command_id in AUTO_ADVANCE_COMMANDS:
                next_continue = 0
                next_data = ""
                continue

            if command_id == 0 and field_id > 0:
                next_continue = 0
                next_data = ""
                continue

            return self._build_interactive_payload(session_id, response)

        return {
            "success": False,
            "error": "Fluxo TEF excedeu o limite de iteracoes",
        }

    async def finalizar_fluxo_interativo(self, session_id: str, confirm: bool) -> Dict[str, Any]:
        session = TEF_INTERACTIVE_SESSIONS.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Sessao TEF nao encontrada ou expirada",
            }

        try:
            finish = self._request(
                "POST",
                "/finishTransaction",
                {
                    "sessionId": session_id,
                    "confirm": 1 if confirm else 0,
                    "taxInvoiceNumber": session["tax_invoice_number"],
                    "taxInvoiceDate": session["tax_invoice_date"],
                    "taxInvoiceTime": session["tax_invoice_time"],
                },
            )
        except requests.RequestException as exc:
            return {
                "success": False,
                "error": f"Falha ao finalizar TEF: {exc}",
            }

        nsu = finish.get("nsu") or session.get("nsu")
        autorizacao = finish.get("autorizacao") or session.get("autorizacao")
        cupom_cliente = finish.get("cupom_cliente") or session.get("cupom_cliente")
        cupom_estabelecimento = finish.get("cupom_estabelecimento") or session.get("cupom_estabelecimento")
        aprovado = bool(confirm and session.get("aprovado_pre_finish"))

        TEF_INTERACTIVE_SESSIONS.pop(session_id, None)

        return {
            "success": aprovado,
            "finalizado": True,
            "aprovado": aprovado,
            "status": "APROVADO" if aprovado else "RECUSADO",
            "nsu": nsu,
            "autorizacao": autorizacao,
            "cupom_cliente": cupom_cliente,
            "cupom_estabelecimento": cupom_estabelecimento,
            "tipo_campos": session.get("tipo_campos", []),
            "message": finish.get("serviceMessage") or ("Transacao aprovada" if aprovado else "Transacao nao aprovada"),
            "detail": finish,
        }

    async def cancelar_fluxo_interativo(self, session_id: str) -> Dict[str, Any]:
        session = TEF_INTERACTIVE_SESSIONS.get(session_id)
        if not session:
            return {
                "success": True,
                "message": "Sessao TEF ja encerrada",
            }

        resultado = await self.finalizar_fluxo_interativo(session_id, confirm=False)
        return {
            "success": True,
            "message": "Sessao TEF cancelada",
            "detail": resultado,
        }

    async def consultar_status(self, nsu: str) -> Dict[str, Any]:
        try:
            data = self._request("GET", f"/consulta/{nsu}")
            return {
                "success": True,
                "status": data.get("status", "DESCONHECIDO"),
                "autorizacao": data.get("autorizacao"),
                "message": data.get("mensagem"),
            }
        except requests.RequestException:
            return {
                "success": False,
                "error": "Servico de consulta TEF indisponivel",
            }

    async def cancelar_pagamento(self, nsu: str) -> Dict[str, Any]:
        try:
            data = self._request("POST", f"/cancelamento/{nsu}")
            return {
                "success": True,
                "message": data.get("mensagem", "Cancelamento realizado"),
            }
        except requests.RequestException:
            return {
                "success": False,
                "error": "Servico de cancelamento TEF indisponivel",
            }
