import requests
from datetime import datetime, timedelta
from typing import Any, Dict
from urllib.parse import quote_plus

from app.core.config import settings
from app.core.cache import cache


TEF_INTERACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
INPUT_COMMANDS = {20, 21, 22, 23, 30, 31, 32, 33, 34, 35, 38, 41, 42}
AUTO_ADVANCE_COMMANDS = {0, 1, 2, 3, 4, 11, 12, 13, 14, 15, 16}
TEF_PENDING_STATUS: Dict[str, Any] = {"message": None, "detail": None, "created_at": None}
INTERACTIVE_CONTINUE_MAX_ITERATIONS = 400
PENDING_CONTINUE_MAX_ITERATIONS = 200
TEF_SESSION_CACHE_PREFIX = "tef:interactive:session:"
TEF_REPRINT_REFERENCE_CACHE_PREFIX = "tef:reprint:reference:"
TEF_REPRINT_REFERENCE_GLOBAL_KEY = f"{TEF_REPRINT_REFERENCE_CACHE_PREFIX}global"
TEF_REPRINT_REFERENCE_TTL_SECONDS = 60 * 60 * 24 * 7
TEF_REPRINT_REFERENCE_HISTORY_LIMIT = 12
TEF_REPRINT_REFERENCE_MEMORY: Dict[str, list[Dict[str, Any]]] = {}
REPRINT_LOOKUP_FIELD_IDS = {146, 515, 516, 601}
REPRINT_FLOW_FUNCTION_IDS = {110, 112, 113, 114}
APPROVED_REFERENCE_FUNCTION_IDS = {0, 2, 3}

TEF_EVENT_LABELS: Dict[int, str] = {
    5000: "Aguardando leitura de cartao",
    5001: "Aguardando digitacao da senha pelo usuario",
    5002: "Aguardando confirmacao positiva pelo usuario",
    5003: "Aguardando leitura do bilhete unico",
    5004: "Aguardando remocao do bilhete unico",
    5005: "Transacao finalizada",
    5006: "Confirma dados do favorecido",
    5007: "SiTef conectado",
    5008: "SiTef conectando",
    5009: "Consulta OK",
    5010: "Colher assinatura",
    5011: "Coleta de novo produto",
    5012: "Confirma operacao",
    5013: "Confirma cancelamento",
    5014: "Confirma valor total",
    5015: "Conclusao de recarga de bilhete unico",
    5016: "Reservado",
    5017: "Aguardando leitura de cartao",
    5018: "Aguardando digitacao da senha no PinPad",
    5019: "Aguardando processamento do chip",
    5020: "Aguardando remocao do cartao",
    5021: "Aguardando confirmacao da operacao",
    5027: "Leitura do cartao cancelada",
    5028: "Digitacao da senha cancelada",
    5029: "Processamento do cartao com chip cancelado",
    5030: "Remocao do cartao cancelada",
    5031: "Confirmacao da operacao cancelada",
    5036: "Antes da leitura do cartao magnetico",
    5037: "Antes da leitura do cartao com chip",
    5038: "Antes da remocao do cartao com chip",
    5039: "Antes da coleta da senha no pinpad",
    5040: "Antes de abrir a comunicacao com o PinPad",
    5041: "Antes de fechar a comunicacao com o PinPad",
    5042: "Bloquear recursos do PinPad",
    5043: "Liberar recursos do PinPad",
    5044: "Depois de abrir a comunicacao com o PinPad",
    5049: "Timeout com o SiTef",
    5050: "Atualizacao de tabelas para transacoes offline",
    5051: "Senha coletada no pinpad",
    5052: "Cartao com chip processado",
    5053: "Cartao com chip removido",
    5054: "Entrega de dados sensiveis",
    5055: "Atualizando tabelas no pinpad",
    5056: "Enviando arquivos para o SiTef",
    5057: "Inicio do envio de dados sensiveis",
    5058: "Fim do envio de dados sensiveis",
    5059: "Aguardando leitura de cartao (modalidade 29)",
    5060: "Reservado",
    5061: "Reservado",
    5062: "Inicio do envio de campos de produtos",
    5063: "Fim do envio de campos de produtos",
    5064: "Inicio do envio de campos de recarga TEF",
    5065: "Fim do envio de campos de recarga TEF",
    5066: "Antes do envio de campos de conecta SiTef",
    5067: "Depois do envio de campos de conecta SiTef",
    5068: "Antes do envio de campos de desconecta SiTef",
    5069: "Depois do envio de campos de desconecta SiTef",
    5070: "Antes do envio de campos de envia SiTef",
    5071: "Depois do envio de campos de envia SiTef",
    5072: "Antes do envio de campos de recebe SiTef",
    5073: "Depois do envio de campos de recebe SiTef",
    5074: "Assinatura em papel obrigatoria",
    5084: "Mensagem vinda do SiTef ou do autorizador",
}
TEF_FIELD_LABELS: Dict[int, str] = {
    105: "Data/hora da transacao",
    121: "Cupom Cliente",
    122: "Cupom Estabelecimento",
    131: "Rede autorizadora",
    132: "Bandeira",
    133: "NSU SiTef",
    134: "NSU Host",
    135: "Codigo de autorizacao",
    146: "Valor da transacao original",
    157: "Codigo de estabelecimento",
    4125: "Cupom Cliente disponivel para reimpressao",
    4126: "Cupom Estabelecimento disponivel para reimpressao",
    4127: "Prazo de disponibilidade na base do SiTef",
    515: "Data da transacao a ser cancelada ou re-impressa (DDMMAAAA)",
    516: "Numero do documento a ser cancelado ou re-impresso",
}
TEF_FIELD_HINTS: Dict[int, str] = {
    146: "Use o valor da transacao original quando o SiTef solicitar o Campo 146.",
    515: "Use a data da transacao original no formato DDMMAAAA para cancelar ou reimprimir.",
    516: "Campo 516 = numero do documento da transacao original. No roteiro de homologacao desta automacao, use o NSU Host.",
}
NFPAG_TYPE_LABELS: Dict[str, str] = {
    "00": "Dinheiro",
    "01": "Cheque",
    "02": "TEF Debito",
    "03": "TEF Credito",
    "04": "Cartao Presente Carrefour",
    "05": "Cartao Bonus Carrefour",
    "06": "Cartao Carrefour",
    "07": "Saque para pagamento",
    "08": "Saque",
    "09": "DCC Carrefour",
    "10": "Ticket Eletronico",
    "11": "Ticket Papel",
    "12": "Carteira Digital",
    "13": "Pix",
    "50": "TEF Cartao",
    "77": "Reservado",
    "98": "Sem Pagamento",
    "99": "Outras Formas",
}
NFPAG_COLLECTION_LABELS: Dict[str, str] = {
    "00": "Campo reservado",
    "01": "Tipo de entrada do cheque",
    "02": "Dados do cheque",
    "03": "Rede destino",
    "04": "NSU do SiTef",
    "05": "Data do SiTef (nao utilizado)",
    "06": "Codigo da empresa",
    "07": "NSU do Host",
    "08": "Data do Host",
    "09": "Codigo de origem",
    "10": "Servico Z",
    "11": "Codigo de autorizacao",
    "12": "Valor do cheque",
    "13": "Redes permitidas para Rede Destino",
    "14": "Bandeira do cartao",
    "15": "Tipo de pagamento",
    "16": "Id da carteira digital",
}


def _normalize_sitef_flag(value: Any) -> bool:
    raw = str(value or "").strip().upper()
    return raw not in {"", "0", "N", "NAO", "FALSE"}


def _build_event_payload(field_id: int, data: Any) -> Dict[str, Any]:
    return {
        "codigo": field_id,
        "descricao": TEF_EVENT_LABELS.get(field_id, f"Evento {field_id}"),
        "valor": "" if data is None else str(data),
    }


def _sanitize_tef_log_data(field_id: int, data: Any) -> str:
    if field_id == 500:
        return "<masked>"
    raw = "" if data is None else str(data)
    normalized = " ".join(raw.split())
    if len(normalized) > 160:
        return f"{normalized[:157]}..."
    return normalized
def _log_tef_response(stage: str, function_id: int | None, response: Dict[str, Any], session_id: str | None = None) -> None:
    command_id = int(response.get("commandId") or 0)
    field_id = int(response.get("fieldId") or 0)
    service_status = int(response.get("serviceStatus") or 0)
    clisitef_status = int(response.get("clisitefStatus") or 0)
    data_preview = _sanitize_tef_log_data(field_id, response.get("data"))
    session_part = f" session={session_id}" if session_id else ""
    function_part = f"{function_id}" if function_id is not None else "?"
    data_part = f" data='{data_preview}'" if data_preview else ""
    print(
        f"[TEF][{stage}] funcao={function_part}{session_part} service={service_status} "
        f"clisitef={clisitef_status} command={command_id} field={field_id}{data_part}"
    )
def _log_tef_input(
    function_id: int | None,
    session_id: str,
    continue_flag: int,
    expected_command_id: int,
    expected_field_id: int,
    data: Any,
) -> None:
    data_preview = _sanitize_tef_log_data(expected_field_id, data)
    data_part = f" data='{data_preview}'" if data_preview else ""
    function_part = f"{function_id}" if function_id is not None else "?"
    print(
        f"[TEF][input] funcao={function_part} session={session_id} continue={continue_flag} "
        f"expected_command={expected_command_id} expected_field={expected_field_id}{data_part}"
    )


def _resolve_final_message(prompt: str, session: Dict[str, Any], clisitef_status: int, aprovado: bool) -> str:
    if str(prompt or "").strip():
        return str(prompt)

    last_prompt = str(session.get("last_non_empty_prompt") or "").strip()
    if last_prompt:
        return last_prompt

    if aprovado:
        return "Transacao Aprovada"

    return f"Transacao finalizada com status {clisitef_status}"


def _build_nfpag_type_detail(code: str) -> Dict[str, Any]:
    normalized = str(code or "").strip().zfill(2)
    return {
        "codigo": normalized,
        "descricao": NFPAG_TYPE_LABELS.get(normalized, "Forma nao mapeada"),
        "coletas": [],
        "coletas_detalhes": [],
    }


def _build_nfpag_collection_detail(code: str) -> Dict[str, Any]:
    normalized = str(code or "").strip().zfill(2)
    return {
        "codigo": normalized,
        "descricao": NFPAG_COLLECTION_LABELS.get(normalized, "Coleta nao mapeada"),
    }


def _sanitize_nfpag(nfpag: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(nfpag, dict):
        return {}

    cleaned: Dict[str, Any] = {}
    for key, value in nfpag.items():
        if str(key).startswith("_"):
            continue
        if key == "tipos_habilitados_detalhes" and isinstance(value, list):
            cleaned[key] = [
                {
                    "codigo": item.get("codigo"),
                    "descricao": item.get("descricao"),
                    "coletas": item.get("coletas", []),
                    "coletas_detalhes": item.get("coletas_detalhes", []),
                }
                for item in value
                if isinstance(item, dict)
            ]
            continue
        cleaned[key] = value
    return cleaned


def _format_date_ddmmyyyy(value: Any) -> str:
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(raw) < 8:
        return ""
    if len(raw) >= 14:
        raw = raw[:8]
    elif len(raw) > 8:
        raw = raw[:8]
    return f"{raw[6:8]}{raw[4:6]}{raw[0:4]}"


def _format_date_mmdd(value: Any) -> str:
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(raw) < 8:
        return ""
    if len(raw) >= 14:
        raw = raw[:8]
    elif len(raw) > 8:
        raw = raw[:8]
    return f"{raw[4:6]}{raw[6:8]}"


def _format_value_from_centavos(value_centavos: Any) -> str:
    try:
        centavos = int(value_centavos)
    except Exception:
        return ""
    return f"{centavos / 100:.2f}".replace(".", ",")


def _extract_sitef_date(value: Any) -> str:
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(raw) >= 8:
        return raw[:8]
    return ""


def _extract_sitef_time(value: Any) -> str:
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(raw) >= 14:
        return raw[8:14]
    if len(raw) == 6:
        return raw
    return ""

def _format_sitef_datetime_display(value: Any) -> str:
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(raw) >= 14:
        return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]} {raw[8:10]}:{raw[10:12]}:{raw[12:14]}"
    return str(value or "").strip()


def _build_pending_resolution_message(confirmar: bool, success: bool, data_hora_transacao: Any = None, nsu_host: Any = None) -> str:
    if not success:
        return "Falha ao tratar automaticamente a transacao T.E.F. pendente."

    action_text = "confirmada" if confirmar else "desfeita"
    parts = [f"Transacao T.E.F. pendente {action_text} automaticamente com sucesso."]

    formatted_datetime = _format_sitef_datetime_display(data_hora_transacao)
    if formatted_datetime:
        parts.append(f"Data/hora: {formatted_datetime}.")

    nsu_host_text = str(nsu_host or "").strip()
    if nsu_host_text:
        parts.append(f"NSU Host: {nsu_host_text}.")

    if confirmar:
        parts.append("Para reimpressao, favor solicitar o ultimo cupom.")

    return " ".join(parts)




def _split_transport_input(command_id: int, data: Any) -> tuple[str | None, str]:
    raw = "" if data is None else str(data)
    if command_id in (31, 35):
        if len(raw) >= 2 and raw[1] == ":" and raw[0] in {"0", "1", "2"}:
            return raw[0], raw[2:]
    return None, raw


def _normalize_lookup_transport_value(field_id: int, value: str, session: Dict[str, Any] | None = None) -> str:
    normalized_field_id = int(field_id or 0)
    if normalized_field_id not in {515, 601}:
        return value

    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    normalized = digits or str(value or "").strip()
    if not normalized:
        return normalized

    reference_source = session.get("original_transaction_reference") if isinstance(session, dict) else None
    if not isinstance(reference_source, dict) and isinstance(session, dict):
        reference_source = _build_transaction_reference(session)

    if normalized_field_id == 601:
        raw_reference = "".join(ch for ch in str((reference_source or {}).get("valor_centavos_raw") or "") if ch.isdigit())
        if not raw_reference or normalized == raw_reference:
            return normalized

        if raw_reference.endswith("00"):
            whole_reais_reference = str(int(raw_reference[:-2] or "0"))
            if normalized == whole_reais_reference:
                return raw_reference

        return normalized

    if not _is_rede_specific_reprint_session(session):
        return normalized

    reference_mmdd = "".join(ch for ch in str((reference_source or {}).get("campo_515_mmdd") or "") if ch.isdigit())
    if not reference_mmdd:
        return normalized

    if normalized == reference_mmdd:
        return normalized

    reference_ddmm = "".join(ch for ch in str((reference_source or {}).get("campo_515_ddmm") or "") if ch.isdigit())
    reference_ddmmaaaa = "".join(ch for ch in str((reference_source or {}).get("campo_515_ddmmaaaa") or "") if ch.isdigit())
    if normalized in {reference_ddmm, reference_ddmmaaaa}:
        return reference_mmdd

    return normalized


def _is_rede_specific_reprint_session(session: Dict[str, Any] | None) -> bool:
    if not isinstance(session, dict):
        return False

    if int(session.get("function_id") or 0) != 113:
        return False

    if str(session.get("reprint_receipt_type") or "").strip().lower() == "rede":
        return True

    for item in session.get("tipo_campos", []):
        if not isinstance(item, dict):
            continue
        tipo_campo = "".join(ch for ch in str(item.get("TipoCampo") or item.get("codigo") or "") if ch.isdigit())
        if tipo_campo == "3006":
            return True

    reference_source = session.get("original_transaction_reference")
    raw_network = str((reference_source or {}).get("rede_autorizadora") or session.get("rede_autorizadora") or "").strip()
    network_code = "".join(ch for ch in raw_network if ch.isdigit()).lstrip("0")
    return network_code == "229"


def _build_transaction_reference(session: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(session, dict):
        return None

    cupom_fiscal = str(session.get("tax_invoice_number") or session.get("cupom_fiscal") or "").strip()
    data_hora_transacao = str(session.get("data_hora_transacao") or "").strip()
    data_fiscal = _extract_sitef_date(data_hora_transacao) or str(session.get("tax_invoice_date") or session.get("data_fiscal") or "").strip()
    hora_fiscal = _extract_sitef_time(data_hora_transacao) or str(session.get("tax_invoice_time") or session.get("hora_fiscal") or "").strip()
    campo_515_ddmmaaaa = _format_date_ddmmyyyy(data_hora_transacao or data_fiscal)
    campo_515_ddmm = campo_515_ddmmaaaa[:4] if campo_515_ddmmaaaa else ""
    campo_515_mmdd = _format_date_mmdd(data_hora_transacao or data_fiscal)
    nsu_host = str(session.get("nsu_host") or session.get("nsu") or "").strip()
    nsu_sitef = str(session.get("nsu_sitef") or "").strip()
    codigo_estabelecimento = str(session.get("codigo_estabelecimento") or "").strip()
    rede_autorizadora = str(session.get("rede_autorizadora") or "").strip()
    bandeira = str(session.get("bandeira") or "").strip()
    autorizacao = str(session.get("autorizacao") or "").strip()
    store_id = str(session.get("store_id") or "").strip()
    terminal_id = str(session.get("terminal_id") or "").strip()
    valor_centavos = session.get("valor_centavos")
    if not isinstance(valor_centavos, int):
        valor_original = session.get("valor")
        if isinstance(valor_original, (int, float)):
            valor_centavos = int(round(float(valor_original) * 100))
        else:
            valor_centavos = None
    valor_formatado = _format_value_from_centavos(valor_centavos) if valor_centavos is not None else ""
    created_at = session.get("created_at")
    created_at_iso = created_at.isoformat() if isinstance(created_at, datetime) else str(created_at or "").strip()

    if not any([cupom_fiscal, data_fiscal, hora_fiscal, campo_515_ddmmaaaa, nsu_host, nsu_sitef, valor_formatado]):
        return None

    return {
        "cupom_fiscal": cupom_fiscal or None,
        "data_fiscal": data_fiscal or None,
        "hora_fiscal": hora_fiscal or None,
        "data_hora_transacao": data_hora_transacao or None,
        "campo_515_ddmmaaaa": campo_515_ddmmaaaa or None,
        "campo_515_ddmm": campo_515_ddmm or None,
        "campo_515_mmdd": campo_515_mmdd or None,
        "nsu_host": nsu_host or None,
        "nsu_sitef": nsu_sitef or None,
        "codigo_estabelecimento": codigo_estabelecimento or None,
        "rede_autorizadora": rede_autorizadora or None,
        "bandeira": bandeira or None,
        "autorizacao": autorizacao or None,
        "store_id": store_id or None,
        "terminal_id": terminal_id or None,
        "valor_centavos": valor_centavos,
        "valor_centavos_raw": str(valor_centavos) if valor_centavos is not None else None,
        "valor_formatado": valor_formatado or None,
        "function_id": session.get("function_id"),
        "created_at": created_at_iso or None,
    }


def _build_tipo_campo_entry(field_id: int, valor: str) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "TipoCampo": str(field_id),
        "Valor": valor,
    }
    descricao = TEF_FIELD_LABELS.get(field_id)
    if descricao:
        entry["Descricao"] = descricao
    dica = TEF_FIELD_HINTS.get(field_id)
    if dica:
        entry["Dica"] = dica
    return entry


def _build_reimpressao_reference(session: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(session, dict):
        return None

    source_reference = session.get("current_transaction_reference")
    if not isinstance(source_reference, dict):
        source_reference = session.get("original_transaction_reference")
    if not isinstance(source_reference, dict):
        source_reference = _build_transaction_reference(session)

    cupom_fiscal = str((source_reference or {}).get("cupom_fiscal") or "").strip()
    data_hora_transacao = str((source_reference or {}).get("data_hora_transacao") or "").strip()
    data_fiscal = _extract_sitef_date(data_hora_transacao) or str((source_reference or {}).get("data_fiscal") or "").strip()
    hora_fiscal = _extract_sitef_time(data_hora_transacao) or str((source_reference or {}).get("hora_fiscal") or "").strip()
    campo_515 = str((source_reference or {}).get("campo_515_ddmmaaaa") or _format_date_ddmmyyyy(data_hora_transacao or data_fiscal)).strip()
    campo_515_ddmm = str((source_reference or {}).get("campo_515_ddmm") or (campo_515[:4] if campo_515 else "")).strip()
    campo_515_mmdd = str((source_reference or {}).get("campo_515_mmdd") or _format_date_mmdd(data_hora_transacao or data_fiscal)).strip()
    nsu_host = str((source_reference or {}).get("nsu_host") or "").strip()
    nsu_sitef = str((source_reference or {}).get("nsu_sitef") or "").strip()
    codigo_estabelecimento = str((source_reference or {}).get("codigo_estabelecimento") or "").strip()
    rede_autorizadora = str((source_reference or {}).get("rede_autorizadora") or "").strip()
    bandeira = str((source_reference or {}).get("bandeira") or "").strip()
    valor_formatado = str((source_reference or {}).get("valor_formatado") or "").strip()
    valor_centavos_raw = str((source_reference or {}).get("valor_centavos_raw") or "").strip()
    campo_146_informado = str(session.get("reprint_value_input") or "").strip()
    campo_516_informado = str(session.get("reprint_document_input") or "").strip()
    campo_515_informado = "".join(ch for ch in str(session.get("reprint_date_input") or "") if ch.isdigit())
    origem_referencia = "transacao_original_aprovada" if isinstance(session.get("original_transaction_reference"), dict) else "sessao_atual"
    rede_specific_reprint = _is_rede_specific_reprint_session(session)

    if not any(
        [
            cupom_fiscal,
            campo_515,
            nsu_host,
            nsu_sitef,
            codigo_estabelecimento,
            valor_formatado,
            valor_centavos_raw,
            campo_146_informado,
            campo_516_informado,
            campo_515_informado,
        ]
    ):
        return None

    return {
        "campo_146_label": "Campo 146 - Valor da transacao original",
        "campo_146_valor": valor_formatado or campo_146_informado or None,
        "campo_146_valor_bruto": valor_centavos_raw or None,
        "campo_146_orientacao": "No cancelamento, o SiTef pode pedir o valor da transacao original.",
        "campo_146_informado": campo_146_informado or None,
        "campo_516_label": "Campo 516 - Numero do documento da transacao original",
        "campo_516_valor": nsu_host or cupom_fiscal or campo_516_informado or None,
        "campo_516_orientacao": "Quando o SiTef pedir o documento da transacao original, use primeiro o NSU Host da venda homologada.",
        "campo_516_informado": campo_516_informado or None,
        "campo_515_label": "Campo 515 - Data da transacao original",
        "campo_515_valor": campo_515 or campo_515_informado or None,
        "campo_515_valor_ddmm": campo_515_ddmm or None,
        "campo_515_valor_mmdd": campo_515_mmdd or None,
        "campo_515_orientacao": (
            "Na reimpressao especifica da Rede, use a data da transacao original no formato MMDD. Ex.: 8 de abril = 0408."
            if rede_specific_reprint
            else "Use esta data no formato DDMMAAAA quando o SiTef pedir a data para cancelar ou reimprimir."
        ),
        "campo_515_informado": campo_515_informado or None,
        "cupom_fiscal": cupom_fiscal or None,
        "data_fiscal": data_fiscal or None,
        "hora_fiscal": hora_fiscal or None,
        "data_hora_transacao": data_hora_transacao or None,
        "nsu_host": nsu_host or None,
        "nsu_sitef": nsu_sitef or None,
        "codigo_estabelecimento": codigo_estabelecimento or None,
        "rede_autorizadora": rede_autorizadora or None,
        "bandeira": bandeira or None,
        "origem_referencia": origem_referencia,
    }


def _now_fiscal_date() -> str:
    now = datetime.now()
    return now.strftime("%Y%m%d")


def _now_fiscal_time() -> str:
    now = datetime.now()
    return now.strftime("%H%M%S")


def _encode_agent_form_payload(payload: Dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""

    safe_value_chars = ",:{}[];=/"
    parts: list[str] = []
    for key, value in payload.items():
        if value is None:
            continue
        encoded_key = quote_plus(str(key))
        encoded_value = quote_plus(str(value), safe=safe_value_chars)
        parts.append(f"{encoded_key}={encoded_value}")
    return "&".join(parts)


def _set_pending_status(message: str, detail: Dict[str, Any] | None = None) -> None:
    TEF_PENDING_STATUS["message"] = message
    TEF_PENDING_STATUS["detail"] = detail
    TEF_PENDING_STATUS["created_at"] = datetime.now()


def get_pending_status(clear: bool = False) -> Dict[str, Any]:
    payload = {
        "message": TEF_PENDING_STATUS.get("message"),
        "detail": TEF_PENDING_STATUS.get("detail"),
        "created_at": TEF_PENDING_STATUS.get("created_at"),
    }
    if clear:
        TEF_PENDING_STATUS["message"] = None
        TEF_PENDING_STATUS["detail"] = None
        TEF_PENDING_STATUS["created_at"] = None
    return payload


class TefService:
    """
    ServiÃƒÆ’Ã‚Â§o de integraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o com CliSiTef para pagamentos TEF.
    """

    def __init__(self):
        self.agente_url = settings.TEF_AGENTE_URL.rstrip("/")
        self.timeout = settings.TEF_TIMEOUT
        self.session_timeout = settings.TEF_SESSION_TIMEOUT
        self.agente_mode = (settings.TEF_AGENTE_MODE or "mock").lower()
        self.verify_ssl = settings.TEF_AGENTE_VERIFY_SSL

    def _session_cache_key(self, session_id: str) -> str:
        return f"{TEF_SESSION_CACHE_PREFIX}{session_id}"

    def _session_cache_ttl(self) -> int:
        return max(int(self.session_timeout) * 3, 300)

    def _serialize_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for key, value in (session or {}).items():
            if isinstance(value, datetime):
                payload[key] = value.isoformat()
            else:
                payload[key] = value
        return payload

    def _deserialize_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = dict(payload or {})
        for field in ("created_at", "last_activity_at"):
            raw = session.get(field)
            if isinstance(raw, str):
                try:
                    session[field] = datetime.fromisoformat(raw)
                except Exception:
                    session[field] = datetime.now()
        return session

    async def _persist_session(self, session_id: str) -> None:
        session = TEF_INTERACTIVE_SESSIONS.get(session_id)
        if not session:
            return
        try:
            await cache.set(
                self._session_cache_key(session_id),
                self._serialize_session(session),
                ttl=self._session_cache_ttl(),
            )
        except Exception:
            pass

    async def _get_interactive_session(self, session_id: str) -> Dict[str, Any] | None:
        session = TEF_INTERACTIVE_SESSIONS.get(session_id)
        if session:
            return session

        try:
            cached = await cache.get(self._session_cache_key(session_id))
        except Exception:
            cached = None

        if isinstance(cached, dict):
            restored = self._deserialize_session(cached)
            TEF_INTERACTIVE_SESSIONS[session_id] = restored
            return restored

        return None

    async def _drop_session(self, session_id: str) -> None:
        TEF_INTERACTIVE_SESSIONS.pop(session_id, None)
        try:
            await cache.delete(self._session_cache_key(session_id))
        except Exception:
            pass

    async def _clear_cached_sessions(self) -> None:
        try:
            await cache.delete_pattern(f"{TEF_SESSION_CACHE_PREFIX}*")
        except Exception:
            pass

    def _reprint_reference_cache_key(self, store_id: str | None, terminal_id: str | None) -> str:
        store = str(store_id or "").strip() or "default-store"
        terminal = str(terminal_id or "").strip() or "default-terminal"
        return f"{TEF_REPRINT_REFERENCE_CACHE_PREFIX}{store}:{terminal}"

    async def _get_cached_reprint_history(self, cache_key: str) -> list[Dict[str, Any]]:
        in_memory = TEF_REPRINT_REFERENCE_MEMORY.get(cache_key)
        if isinstance(in_memory, list):
            return [dict(item) for item in in_memory if isinstance(item, dict)]

        try:
            cached = await cache.get(cache_key)
        except Exception:
            cached = None

        if isinstance(cached, list):
            history = [dict(item) for item in cached if isinstance(item, dict)]
            TEF_REPRINT_REFERENCE_MEMORY[cache_key] = history
            return [dict(item) for item in history]

        return []

    async def _set_cached_reprint_history(self, cache_key: str, history: list[Dict[str, Any]]) -> None:
        normalized = [dict(item) for item in history if isinstance(item, dict)]
        TEF_REPRINT_REFERENCE_MEMORY[cache_key] = normalized
        try:
            await cache.set(cache_key, normalized, ttl=TEF_REPRINT_REFERENCE_TTL_SECONDS)
        except Exception:
            pass

    def _reference_signature(self, reference: Dict[str, Any]) -> str:
        return "|".join(
            [
                str(reference.get("cupom_fiscal") or ""),
                str(reference.get("nsu_host") or ""),
                str(reference.get("nsu_sitef") or ""),
                str(reference.get("data_fiscal") or ""),
                str(reference.get("hora_fiscal") or ""),
                str(reference.get("valor_centavos_raw") or ""),
            ]
        )

    def _merge_reprint_reference_history(
        self,
        history: list[Dict[str, Any]],
        reference: Dict[str, Any],
    ) -> list[Dict[str, Any]]:
        merged: list[Dict[str, Any]] = [dict(reference)]
        seen = {self._reference_signature(reference)}
        for item in history:
            if not isinstance(item, dict):
                continue
            signature = self._reference_signature(item)
            if signature in seen:
                continue
            seen.add(signature)
            merged.append(dict(item))
            if len(merged) >= TEF_REPRINT_REFERENCE_HISTORY_LIMIT:
                break
        return merged

    def _score_reprint_reference(self, reference: Dict[str, Any], session: Dict[str, Any]) -> int:
        score = 0
        start_document = str(session.get("tax_invoice_number") or "").strip()
        start_date = str(session.get("tax_invoice_date") or "").strip()
        start_time = str(session.get("tax_invoice_time") or "").strip()
        session_store = str(session.get("store_id") or "").strip()
        session_terminal = str(session.get("terminal_id") or "").strip()

        if start_document:
            if start_document == str(reference.get("cupom_fiscal") or "").strip():
                score += 12
            if start_document == str(reference.get("nsu_host") or "").strip():
                score += 10
            if start_document == str(reference.get("nsu_sitef") or "").strip():
                score += 9
        if start_date and start_date == str(reference.get("data_fiscal") or "").strip():
            score += 4
        if start_time and start_time == str(reference.get("hora_fiscal") or "").strip():
            score += 3
        if session_store and session_store == str(reference.get("store_id") or "").strip():
            score += 2
        if session_terminal and session_terminal == str(reference.get("terminal_id") or "").strip():
            score += 2
        if reference.get("nsu_host") or reference.get("cupom_fiscal"):
            score += 1
        return score

    async def _resolve_original_transaction_reference(self, session: Dict[str, Any]) -> Dict[str, Any] | None:
        cache_keys = []
        store_id = str(session.get("store_id") or "").strip()
        terminal_id = str(session.get("terminal_id") or "").strip()
        if store_id or terminal_id:
            cache_keys.append(self._reprint_reference_cache_key(store_id, terminal_id))
        cache_keys.append(TEF_REPRINT_REFERENCE_GLOBAL_KEY)

        best_reference = None
        best_score = -1
        fallback_reference = None

        for cache_key in cache_keys:
            history = await self._get_cached_reprint_history(cache_key)
            if history and fallback_reference is None:
                fallback_reference = dict(history[0])
            for reference in history:
                score = self._score_reprint_reference(reference, session)
                if score > best_score:
                    best_score = score
                    best_reference = dict(reference)

        if best_reference and best_score > 0:
            return best_reference
        return fallback_reference

    async def _store_approved_transaction_reference(self, session: Dict[str, Any]) -> None:
        function_id = int(session.get("function_id") or 0)
        if function_id not in APPROVED_REFERENCE_FUNCTION_IDS:
            return

        reference = _build_transaction_reference(session)
        if not reference:
            return
        if not any([reference.get("cupom_fiscal"), reference.get("nsu_host"), reference.get("nsu_sitef")]):
            return

        cache_keys = [TEF_REPRINT_REFERENCE_GLOBAL_KEY]
        store_id = str(reference.get("store_id") or "").strip()
        terminal_id = str(reference.get("terminal_id") or "").strip()
        if store_id or terminal_id:
            cache_keys.insert(0, self._reprint_reference_cache_key(store_id, terminal_id))

        for cache_key in cache_keys:
            history = await self._get_cached_reprint_history(cache_key)
            merged = self._merge_reprint_reference_history(history, reference)
            await self._set_cached_reprint_history(cache_key, merged)

    def _capture_reprint_lookup_input(self, session: Dict[str, Any], field_id: int, value: Any) -> bool:
        normalized_input = str(value or "").strip()
        if not normalized_input:
            return False
        if field_id in {146, 601}:
            session["reprint_value_input"] = normalized_input
            return True
        if field_id == 515:
            session["reprint_date_input"] = "".join(ch for ch in normalized_input if ch.isdigit()) or normalized_input
            return True
        if field_id == 516:
            session["reprint_document_input"] = normalized_input
            return True
        return False

    def _parse_command_menu_options(self, data: Any) -> list[Dict[str, str]]:
        options: list[Dict[str, str]] = []
        for raw_part in str(data or "").split(";"):
            part = raw_part.strip()
            if not part or ":" not in part:
                continue
            index, text = part.split(":", 1)
            normalized_index = str(index or "").strip()
            normalized_text = str(text or "").strip()
            if not normalized_index or not normalized_text:
                continue
            options.append({"index": normalized_index, "text": normalized_text})
        return options

    def _infer_specific_reprint_menu_selection(self, session: Dict[str, Any], response: Dict[str, Any]) -> str | None:
        if int(session.get("function_id") or 0) != 113:
            return None
        if int(response.get("commandId") or 0) != 21:
            return None

        menu_title = str(session.get("menu_title") or "").strip().lower()
        if "tipo do comprovante" not in menu_title:
            return None

        options = self._parse_command_menu_options(response.get("data"))
        if not options:
            return None

        reference_source = session.get("original_transaction_reference")
        if not isinstance(reference_source, dict):
            reference_source = _build_transaction_reference(session)

        raw_network = str((reference_source or {}).get("rede_autorizadora") or session.get("rede_autorizadora") or "").strip()
        raw_brand = str((reference_source or {}).get("bandeira") or session.get("bandeira") or "").strip()
        network_code = "".join(ch for ch in raw_network if ch.isdigit()).lstrip("0")
        network_label = f"{raw_network} {raw_brand}".strip().lower()

        target_label = ""
        if network_code == "229" or any(token in network_label for token in ("rede", "redecard", "redeshop")):
            target_label = "rede"
        elif network_code in {"2", "5"} or any(token in network_label for token in ("cielo", "visanet")):
            target_label = "cielo"
        elif network_code or network_label:
            target_label = "outros"

        if not target_label:
            return None

        for option in options:
            option_text = str(option.get("text") or "").strip().lower()
            if target_label in option_text:
                selected_index = str(option.get("index") or "").strip()
                return selected_index or None

        return None

    def _generate_cupom_fiscal(self) -> str:
        now = datetime.now()
        return now.strftime("%Y%m%d%H%M%S%f")[:17]

    def _build_parametros_adicionais(self) -> str:
        if settings.TEF_PARAMETROS_ADICIONAIS:
            return settings.TEF_PARAMETROS_ADICIONAIS
        partes = []
        if settings.TEF_CNPJ_ESTAB:
            partes.append(f"1={settings.TEF_CNPJ_ESTAB}")
        if settings.TEF_CNPJ_AUTOMACAO:
            partes.append(f"2={settings.TEF_CNPJ_AUTOMACAO}")
        if not partes:
            return ""
        return f"{settings.TEF_PARMSCLIENT_PREFIX}{';'.join(partes)}"

    def _resolve_session_parameters(self, session_parameters: str | None) -> str | None:
        if session_parameters:
            return session_parameters
        if settings.TEF_SESSION_PARAMETERS:
            return settings.TEF_SESSION_PARAMETERS
        parametros_adicionais = self._build_parametros_adicionais()
        return parametros_adicionais or None

    def _resolve_trn_init_parameters(self, function_id: int, trn_init_parameters: str | None) -> str | None:
        if trn_init_parameters:
            return trn_init_parameters

        default_trn_init = settings.TEF_TRN_INIT_PARAMETERS or None
        if not default_trn_init:
            return None

        # Regra de homologacao: nao forcar TLS no fluxo de venda comum.
        # O TokenRegistro padrao so deve ser enviado apenas nas funcoes oficiais de registro TLS.
        if int(function_id) in {669, 699}:
            return default_trn_init

        return None

    def _request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.agente_url}{path}"
        data = payload or {}
        if self.agente_mode == "real":
            encoded_data = _encode_agent_form_payload(data)
            response = requests.request(
                method=method,
                url=url,
                data=encoded_data,
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        else:
            response = requests.request(
                method=method,
                url=url,
                json=data,
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

    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        last_activity = session.get("last_activity_at")
        if not last_activity:
            return False
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity)
            except Exception:
                return True
        return datetime.now() - last_activity > timedelta(seconds=self.session_timeout)

    def _start_transaction(
        self,
        *,
        function_id: int,
        valor_centavos: int | None,
        tax_invoice_number: str,
        tax_invoice_date: str,
        tax_invoice_time: str,
        sitef_ip: str | None = None,
        store_id: str | None = None,
        terminal_id: str | None = None,
        cashier_operator: str | None = None,
        trn_additional_parameters: str | None = None,
        trn_init_parameters: str | None = None,
        session_parameters: str | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "functionId": int(function_id),
            "taxInvoiceNumber": tax_invoice_number,
            "taxInvoiceDate": tax_invoice_date,
            "taxInvoiceTime": tax_invoice_time,
        }
        if valor_centavos is not None:
            if self.agente_mode == "real":
                payload["trnAmount"] = f"{valor_centavos / 100:.2f}".replace(".", ",")
            else:
                payload["trnAmount"] = int(valor_centavos)
        elif self.agente_mode == "real":
            # O Agente CliSiTef real valida a presenca de trnAmount mesmo em funcoes sem valor previo.
            payload["trnAmount"] = ""
        if sitef_ip:
            payload["sitefIp"] = sitef_ip
        if store_id:
            payload["storeId"] = store_id
        if terminal_id:
            payload["terminalId"] = terminal_id
        if cashier_operator:
            payload["cashierOperator"] = cashier_operator
        if trn_additional_parameters:
            payload["trnAdditionalParameters"] = trn_additional_parameters
        if trn_init_parameters:
            payload["trnInitParameters"] = trn_init_parameters
        if session_parameters:
            payload["sessionParameters"] = session_parameters

        return self._request("POST", "/startTransaction", payload)

    def _default_input_value(self, response: Dict[str, Any]) -> str:
        command_id = int(response.get("commandId") or 0)
        field_id = int(response.get("fieldId") or 0)
        texto = str(response.get("data") or "").lower()

        if command_id in (22, 41):
            return ""
        if field_id == 500:
            return ""
        if command_id == 20:
            return "0"
        if command_id == 29:
            return "0"
        if command_id in (31, 35):
            return "0:0"

        if self.agente_mode != "mock":
            return ""

        if "vencimento" in texto or "mmaa" in texto:
            return "1228"
        if "seguranca" in texto or "cvv" in texto:
            return "123"
        if "forma de pagamento" in texto:
            return "1"
        if "numero do cartao" in texto:
            return "5385913424769600"

        return ""

    def _should_auto_continue_input_command(self, response: Dict[str, Any]) -> bool:
        command_id = int(response.get("commandId") or 0)
        if command_id not in (31, 35):
            return False

        field_min_length = int(response.get("fieldMinLength") or 0)
        field_max_length = int(response.get("fieldMaxLength") or 0)
        if field_min_length <= 0 and field_max_length <= 0:
            return True

        prompt = str(response.get("data") or "").lower()
        if command_id == 35 and "aguarde" in prompt and "process" in prompt:
            return True

        return False

    def _register_response(self, session_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        session = TEF_INTERACTIVE_SESSIONS[session_id]
        command_id = int(response.get("commandId") or 0)
        field_id = int(response.get("fieldId") or 0)
        data = response.get("data")

        session["last_response"] = response

        if command_id != 0 and data is not None and str(data).strip():
            session["last_non_empty_prompt"] = str(data)

        if command_id in (1, 2, 3):
            mensagem = "" if data is None else str(data)
            session.setdefault("messages", {})[str(command_id)] = mensagem
        elif command_id == 0 and field_id <= 0 and data:
            session.setdefault("messages", {})["0"] = str(data)
        elif command_id == 11:
            session.setdefault("messages", {}).pop("1", None)
        elif command_id == 12:
            session.setdefault("messages", {}).pop("2", None)
        elif command_id == 13:
            session["messages"] = {}
        elif command_id == 4:
            session["menu_title"] = "" if data is None else str(data)
        elif command_id == 14:
            session["menu_title"] = ""
        elif command_id == 15:
            session["header"] = "" if data is None else str(data)
        elif command_id == 16:
            session["header"] = ""

        if command_id == 0 and field_id > 0:
            valor = "" if data is None else str(data)
            if field_id == 500:
                valor = "****"
            session["tipo_campos"].append(_build_tipo_campo_entry(field_id, valor))

        if command_id == 0 and 5000 <= field_id <= 5084:
            event_payload = _build_event_payload(field_id, data)
            session["evento_atual"] = event_payload
            session.setdefault("eventos", []).append(event_payload)

        if command_id == 0 and field_id == 2470:
            try:
                session["float_decimals"] = int(str(data).strip())
            except Exception:
                session["float_decimals"] = None

        if command_id == 0 and field_id == 161:
            session.setdefault("nfpag", {})["numero_pagamento"] = "" if data is None else str(data)
        elif command_id == 0 and field_id == 730:
            try:
                session.setdefault("nfpag", {})["max_formas"] = int(str(data).strip())
            except Exception:
                session.setdefault("nfpag", {})["max_formas"] = None
        elif command_id == 0 and field_id == 731:
            nfpag = session.setdefault("nfpag", {})
            codigo_tipo = "" if data is None else str(data).strip().zfill(2)
            if codigo_tipo:
                nfpag.setdefault("tipos_habilitados", []).append(codigo_tipo)
                detalhes = nfpag.setdefault("tipos_habilitados_detalhes", [])
                detalhes.append(_build_nfpag_type_detail(codigo_tipo))
                nfpag["_tipo_corrente_index"] = len(detalhes) - 1
        elif command_id == 0 and field_id == 732:
            nfpag = session.setdefault("nfpag", {})
            codigo_coleta = "" if data is None else str(data).strip().zfill(2)
            if codigo_coleta:
                nfpag.setdefault("dados_coleta", []).append(codigo_coleta)
                current_index = nfpag.get("_tipo_corrente_index")
                detalhes = nfpag.setdefault("tipos_habilitados_detalhes", [])
                if isinstance(current_index, int) and 0 <= current_index < len(detalhes):
                    detalhes[current_index].setdefault("coletas", []).append(codigo_coleta)
                    detalhes[current_index].setdefault("coletas_detalhes", []).append(
                        _build_nfpag_collection_detail(codigo_coleta)
                    )

        if command_id == 0 and field_id == 121:
            session["cupom_cliente"] = "" if data is None else str(data)
        elif command_id == 0 and field_id == 122:
            session["cupom_estabelecimento"] = "" if data is None else str(data)
        elif field_id == 105 and data:
            session["data_hora_transacao"] = str(data)
        elif field_id == 131 and data:
            session["rede_autorizadora"] = str(data)
        elif field_id == 132 and data:
            session["bandeira"] = str(data)
        elif field_id == 133 and data:
            session["nsu_sitef"] = str(data)
        elif field_id == 134 and data:
            session["nsu_host"] = str(data)
            session["nsu"] = str(data)
        elif field_id == 135 and data:
            session["autorizacao"] = str(data)
        elif field_id == 157 and data:
            session["codigo_estabelecimento"] = str(data)
        elif field_id == 3006:
            session["reprint_receipt_type"] = "rede"
        elif field_id == 4125:
            reimpressao = session.setdefault("reimpressao", {})
            reimpressao["cupom_cliente_disponivel"] = _normalize_sitef_flag(data)
            reimpressao["cupom_cliente_valor"] = "" if data is None else str(data)
        elif field_id == 4126:
            reimpressao = session.setdefault("reimpressao", {})
            reimpressao["cupom_estabelecimento_disponivel"] = _normalize_sitef_flag(data)
            reimpressao["cupom_estabelecimento_valor"] = "" if data is None else str(data)
        elif field_id == 4127:
            reimpressao = session.setdefault("reimpressao", {})
            raw_days = "" if data is None else str(data).strip()
            try:
                reimpressao["dias_disponiveis"] = int(raw_days)
            except Exception:
                reimpressao["dias_disponiveis"] = raw_days

        return session

    def _build_interactive_payload(self, session_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        session = TEF_INTERACTIVE_SESSIONS[session_id]
        command_id = int(response.get("commandId") or 0)
        clisitef_status = int(response.get("clisitefStatus") or 0)
        prompt = str(response.get("data") or "")
        finish_required = clisitef_status != 10000
        aprovado = clisitef_status == 0
        field_id = int(response.get("fieldId") or 0)
        messages_dict = session.get("messages") or {}
        messages = [
            {"target": int(key), "text": value}
            for key, value in messages_dict.items()
            if value
        ]
        messages.sort(key=lambda item: item["target"])
        receipt_required = command_id == 0 and field_id in (121, 122)
        receipt_kind = "cliente" if field_id == 121 else "estabelecimento" if field_id == 122 else ""
        field_label = TEF_FIELD_LABELS.get(field_id)
        field_hint = TEF_FIELD_HINTS.get(field_id)
        if field_id == 515:
            prompt_normalized = str(prompt or '').lower()
            if _is_rede_specific_reprint_session(session):
                field_hint = 'Na reimpressao especifica da Rede, informe a data da transacao original no formato MMDD. Ex.: 8 de abril = 0408.'
            elif 'ddmm' in prompt_normalized and 'ddmmaaaa' not in prompt_normalized:
                field_hint = 'Use a data da transacao original no formato DDMM para esta rede.'
        elif field_id == 601:
            field_label = 'Valor da Venda'
            field_hint = 'Informe exatamente o valor original da venda, sem virgula ou ponto, para localizar a transacao. Ex.: R$ 10,00 = 1000.'

        return {
            "success": True,
            "session_id": session_id,
            "clisitef_status": clisitef_status,
            "service_status": int(response.get("serviceStatus") or 0),
            "requires_input": clisitef_status == 10000 and command_id in INPUT_COMMANDS,
            "finish_required": finish_required,
            "aprovado": aprovado,
            "command_id": command_id,
            "field_id": field_id,
            "field_is_secret": field_id == 500 or command_id == 41,
            "field_min_length": int(response.get("fieldMinLength") or 0),
            "field_max_length": int(response.get("fieldMaxLength") or 0),
            "field_label": field_label,
            "field_hint": field_hint,
            "prompt": prompt,
            "default_value": self._default_input_value(response),
            "message": _resolve_final_message(prompt, session, clisitef_status, aprovado),
            "function_id": session.get("function_id"),
            "cupom_fiscal": session.get("tax_invoice_number"),
            "data_fiscal": _extract_sitef_date(session.get("data_hora_transacao")) or session.get("tax_invoice_date"),
            "hora_fiscal": _extract_sitef_time(session.get("data_hora_transacao")) or session.get("tax_invoice_time"),
            "nsu": session.get("nsu") or session.get("nsu_host") or session.get("nsu_sitef"),
            "nsu_sitef": session.get("nsu_sitef"),
            "nsu_host": session.get("nsu_host"),
            "rede_autorizadora": session.get("rede_autorizadora"),
            "bandeira": session.get("bandeira"),
            "autorizacao": session.get("autorizacao"),
            "codigo_estabelecimento": session.get("codigo_estabelecimento"),
            "data_hora_transacao": session.get("data_hora_transacao"),
            "cupom_cliente": session.get("cupom_cliente"),
            "cupom_estabelecimento": session.get("cupom_estabelecimento"),
            "tipo_campos": session.get("tipo_campos", []),
            "menu_title": session.get("menu_title", ""),
            "header": session.get("header", ""),
            "messages": messages,
            "float_decimals": session.get("float_decimals"),
            "nfpag": _sanitize_nfpag(session.get("nfpag")),
            "evento_atual": session.get("evento_atual"),
            "eventos": session.get("eventos", [])[-12:],
            "reimpressao": session.get("reimpressao") or None,
            "referencia_reimpressao": _build_reimpressao_reference(session),
            "receipt_required": receipt_required,
            "receipt_kind": receipt_kind,
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

    async def iniciar_fluxo_interativo(
        self,
        valor: float | None,
        reserva_id: int | None,
        function_id: int = 3,
        cupom_fiscal: str | None = None,
        data_fiscal: str | None = None,
        hora_fiscal: str | None = None,
        trn_additional_parameters: str | None = None,
        trn_init_parameters: str | None = None,
        session_parameters: str | None = None,
        cashier_operator: str | None = None,
        sitef_ip: str | None = None,
        store_id: str | None = None,
        terminal_id: str | None = None,
        justificativa: str | None = None,
        original_transaction_reference: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if function_id in (2, 3, 122) and valor is None:
            return {
                "success": False,
                "error": "Valor obrigatorio para a funcao solicitada",
            }
        valor_centavos = int(round(valor * 100)) if valor is not None else None
        if function_id == 110:
            valor_centavos = None
        tax_invoice_number = cupom_fiscal or self._generate_cupom_fiscal()
        tax_invoice_date = data_fiscal or _now_fiscal_date()
        tax_invoice_time = hora_fiscal or _now_fiscal_time()
        session_parameters_resolved = self._resolve_session_parameters(session_parameters)
        trn_init_resolved = self._resolve_trn_init_parameters(function_id, trn_init_parameters)
        trn_additional_resolved = trn_additional_parameters or settings.TEF_TRN_PARAMETERS or None
        sitef_ip_resolved = sitef_ip or settings.TEF_SITEF_IP or None
        store_id_resolved = store_id or settings.TEF_STORE_ID or None
        terminal_id_resolved = terminal_id or settings.TEF_TERMINAL_ID or None
        cashier_operator_resolved = cashier_operator or settings.TEF_CASHIER_OPERATOR or None

        try:
            start = self._start_transaction(
                function_id=function_id,
                valor_centavos=valor_centavos,
                tax_invoice_number=tax_invoice_number,
                tax_invoice_date=tax_invoice_date,
                tax_invoice_time=tax_invoice_time,
                sitef_ip=sitef_ip_resolved,
                store_id=store_id_resolved,
                terminal_id=terminal_id_resolved,
                cashier_operator=cashier_operator_resolved,
                trn_additional_parameters=trn_additional_resolved,
                trn_init_parameters=trn_init_resolved,
                session_parameters=session_parameters_resolved,
            )
        except requests.RequestException as exc:
            return {
                "success": False,
                "error": f"Falha ao iniciar TEF: {exc}",
            }

        if int(start.get("serviceStatus") or 0) == 98:
            self._cleanup_remote_session()
            self._reset_local_interactive_sessions()
            await self._clear_cached_sessions()
            try:
                start = self._start_transaction(
                    function_id=function_id,
                    valor_centavos=valor_centavos,
                    tax_invoice_number=tax_invoice_number,
                    tax_invoice_date=tax_invoice_date,
                    tax_invoice_time=tax_invoice_time,
                    sitef_ip=sitef_ip_resolved,
                    store_id=store_id_resolved,
                    terminal_id=terminal_id_resolved,
                    cashier_operator=cashier_operator_resolved,
                    trn_additional_parameters=trn_additional_resolved,
                    trn_init_parameters=trn_init_resolved,
                    session_parameters=session_parameters_resolved,
                )
            except requests.RequestException as exc:
                return {
                    "success": False,
                    "error": f"Falha ao reiniciar TEF apos sessao ocupada: {exc}",
                }

        _log_tef_response("start", function_id, start, start.get("sessionId"))
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
            "function_id": function_id,
            "justificativa": justificativa,
            "tax_invoice_number": tax_invoice_number,
            "tax_invoice_date": tax_invoice_date,
            "tax_invoice_time": tax_invoice_time,
            "sitef_ip": sitef_ip_resolved,
            "store_id": store_id_resolved,
            "terminal_id": terminal_id_resolved,
            "cashier_operator": cashier_operator_resolved,
            "trn_additional_parameters": trn_additional_resolved,
            "trn_init_parameters": trn_init_resolved,
            "session_parameters": session_parameters_resolved,
            "cupom_cliente": "",
            "cupom_estabelecimento": "",
            "nsu": None,
            "autorizacao": None,
            "tipo_campos": [],
            "messages": {},
            "menu_title": "",
            "header": "",
            "last_non_empty_prompt": "",
            "float_decimals": None,
            "nfpag": {},
            "evento_atual": None,
            "eventos": [],
            "reimpressao": {},
            "reprint_receipt_type": None,
            "reprint_value_input": None,
            "reprint_date_input": None,
            "reprint_document_input": None,
            "original_transaction_reference": dict(original_transaction_reference) if isinstance(original_transaction_reference, dict) else None,
            "last_response": None,
            "created_at": datetime.now(),
            "last_activity_at": datetime.now(),
        }
        if function_id in REPRINT_FLOW_FUNCTION_IDS and not isinstance(
            TEF_INTERACTIVE_SESSIONS[session_id].get("original_transaction_reference"), dict
        ):
            TEF_INTERACTIVE_SESSIONS[session_id]["original_transaction_reference"] = await self._resolve_original_transaction_reference(
                TEF_INTERACTIVE_SESSIONS[session_id]
            )
        await self._persist_session(session_id)

        if justificativa:
            print(f"[TEF] Justificativa funcao {function_id}: {justificativa}")

        return await self.continuar_fluxo_interativo(session_id, continue_flag=0, data="")

    async def continuar_fluxo_interativo(
        self,
        session_id: str,
        continue_flag: int = 0,
        data: str = "",
    ) -> Dict[str, Any]:
        session = await self._get_interactive_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Sessao TEF nao encontrada ou expirada",
            }
        if self._is_session_expired(session):
            await self._drop_session(session_id)
            self._cleanup_remote_session()
            return {
                "success": False,
                "error": "Sessao TEF expirada por inatividade",
            }

        next_continue = continue_flag
        next_data = "" if data is None else str(data)

        last_response = session.get("last_response") or {}
        expected_command_id = int(last_response.get("commandId") or 0)
        last_field_id = int(last_response.get("fieldId") or 0)
        transport_mode, transport_value = _split_transport_input(expected_command_id, next_data)
        normalized_transport_value = _normalize_lookup_transport_value(last_field_id, transport_value, session)
        if next_continue == 0 and normalized_transport_value != transport_value:
            next_data = f"{transport_mode}:{normalized_transport_value}" if transport_mode is not None else normalized_transport_value
        captured_reprint_input = False
        if next_continue == 0 and last_field_id in REPRINT_LOOKUP_FIELD_IDS:
            captured_reprint_input = self._capture_reprint_lookup_input(session, last_field_id, normalized_transport_value)
        if captured_reprint_input:
            session["last_activity_at"] = datetime.now()
            await self._persist_session(session_id)
        _log_tef_input(session.get("function_id"), session_id, next_continue, expected_command_id, last_field_id, next_data)
        if last_field_id == 500:
            if not transport_value:
                return {
                    "success": False,
                    "error": "Senha do supervisor obrigatoria",
                }
            if transport_value != settings.TEF_SUPERVISOR_PASSWORD:
                return {
                    "success": False,
                    "error": "Senha do supervisor invalida",
                }

        last_response: Dict[str, Any] | None = None

        for _ in range(INTERACTIVE_CONTINUE_MAX_ITERATIONS):
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

            _log_tef_response("continue", session.get("function_id"), response, session_id)
            if int(response.get("serviceStatus") or 0) != 0:
                return {
                    "success": False,
                    "error": f"Erro no continueTransaction (serviceStatus={response.get('serviceStatus')})",
                    "detail": response,
                }

            last_response = response
            session = self._register_response(session_id, response)
            session["last_activity_at"] = datetime.now()
            await self._persist_session(session_id)
            clisitef_status = int(response.get("clisitefStatus") or 0)
            command_id = int(response.get("commandId") or 0)
            field_id = int(response.get("fieldId") or 0)

            if clisitef_status != 10000:
                session["aprovado_pre_finish"] = clisitef_status == 0
                await self._persist_session(session_id)
                return self._build_interactive_payload(session_id, response)

            if command_id == 0 and field_id in (121, 122):
                return self._build_interactive_payload(session_id, response)

            if command_id == 29:
                next_continue = 0
                next_data = self._default_input_value(response)
                continue

            if command_id in INPUT_COMMANDS:
                auto_menu_selection = self._infer_specific_reprint_menu_selection(session, response)
                if auto_menu_selection:
                    next_continue = 0
                    next_data = auto_menu_selection
                    _log_tef_input(session.get("function_id"), session_id, next_continue, command_id, field_id, next_data)
                    continue
                if self._should_auto_continue_input_command(response):
                    next_continue = 0
                    next_data = self._default_input_value(response)
                    continue
                return self._build_interactive_payload(session_id, response)

            if command_id == 3:
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
            "error": "Fluxo TEF excedeu o limite de iteracoes automaticas",
            "detail": last_response,
        }

    async def finalizar_fluxo_interativo(
        self,
        session_id: str,
        confirm: bool,
        param_adic: str | None = None,
    ) -> Dict[str, Any]:
        session = await self._get_interactive_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Sessao TEF nao encontrada ou expirada",
            }
        if self._is_session_expired(session):
            await self._drop_session(session_id)
            self._cleanup_remote_session()
            return {
                "success": False,
                "error": "Sessao TEF expirada por inatividade",
            }

        finish_payload: Dict[str, Any] = {
            "sessionId": session_id,
            "confirm": 1 if confirm else 0,
            "taxInvoiceNumber": session["tax_invoice_number"],
            "taxInvoiceDate": session["tax_invoice_date"],
            "taxInvoiceTime": session["tax_invoice_time"],
        }
        if param_adic:
            finish_payload["paramAdic"] = param_adic
            finish_payload["trnAdditionalParameters"] = param_adic

        try:
            finish = self._request("POST", "/finishTransaction", finish_payload)
        except requests.RequestException as exc:
            return {
                "success": False,
                "error": f"Falha ao finalizar TEF: {exc}",
            }

        nsu_sitef = finish.get("nsu_sitef") or session.get("nsu_sitef")
        nsu_host = finish.get("nsu_host") or finish.get("nsu") or session.get("nsu_host") or session.get("nsu")
        nsu = nsu_host or nsu_sitef
        autorizacao = finish.get("autorizacao") or session.get("autorizacao")
        cupom_cliente = finish.get("cupom_cliente") or session.get("cupom_cliente")
        cupom_estabelecimento = finish.get("cupom_estabelecimento") or session.get("cupom_estabelecimento")
        aprovado = bool(confirm and session.get("aprovado_pre_finish"))

        session["nsu_sitef"] = nsu_sitef
        session["nsu_host"] = nsu_host
        session["nsu"] = nsu
        session["autorizacao"] = autorizacao
        session["cupom_cliente"] = cupom_cliente
        session["cupom_estabelecimento"] = cupom_estabelecimento

        current_transaction_reference = _build_transaction_reference(session)
        if isinstance(current_transaction_reference, dict):
            session["current_transaction_reference"] = current_transaction_reference

        if aprovado:
            await self._store_approved_transaction_reference(session)

        await self._drop_session(session_id)

        return {
            "success": aprovado,
            "finalizado": True,
            "aprovado": aprovado,
            "status": "APROVADO" if aprovado else "RECUSADO",
            "nsu": nsu,
            "nsu_sitef": nsu_sitef,
            "nsu_host": nsu_host,
            "rede_autorizadora": session.get("rede_autorizadora"),
            "bandeira": session.get("bandeira"),
            "autorizacao": autorizacao,
            "codigo_estabelecimento": session.get("codigo_estabelecimento"),
            "data_hora_transacao": session.get("data_hora_transacao"),
            "cupom_cliente": cupom_cliente,
            "cupom_estabelecimento": cupom_estabelecimento,
            "tipo_campos": session.get("tipo_campos", []),
            "nfpag": _sanitize_nfpag(session.get("nfpag")),
            "evento_atual": session.get("evento_atual"),
            "eventos": session.get("eventos", [])[-12:],
            "reimpressao": session.get("reimpressao") or None,
            "referencia_reimpressao": _build_reimpressao_reference(session),
            "message": finish.get("serviceMessage") or ("Transacao aprovada" if aprovado else "Transacao nao aprovada"),
            "detail": finish,
        }

    async def cancelar_fluxo_interativo(self, session_id: str) -> Dict[str, Any]:
        session = await self._get_interactive_session(session_id)
        if not session:
            return {
                "success": True,
                "message": "Sessao TEF ja encerrada",
            }
        if self._is_session_expired(session):
            await self._drop_session(session_id)
            self._cleanup_remote_session()
            return {
                "success": True,
                "message": "Sessao TEF expirada e encerrada",
            }

        try:
            self._request(
                "POST",
                "/continueTransaction",
                {
                    "sessionId": session_id,
                    "continue": -1,
                    "data": "",
                },
            )
        except Exception:
            pass

        resultado = await self.finalizar_fluxo_interativo(session_id, confirm=False)
        cancel_success = bool(resultado.get("success"))

        if cancel_success:
            return {
                "success": True,
                "message": "Sessao TEF cancelada",
                "detail": resultado,
            }

        return {
            "success": False,
            "message": "Falha ao finalizar cancelamento da sessao TEF",
            "error": resultado.get("error") or "Nao foi possivel finalizar a sessao TEF",
            "detail": resultado,
        }

    async def limpar_sessao_interativa(self) -> Dict[str, Any]:
        self._cleanup_remote_session()
        self._reset_local_interactive_sessions()
        await self._clear_cached_sessions()
        return {
            "success": True,
            "message": "Sessao TEF limpa",
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

    async def resolver_pendencias(self, confirmar: bool = True) -> Dict[str, Any]:
        function_id = 130
        tax_invoice_number = self._generate_cupom_fiscal()
        tax_invoice_date = _now_fiscal_date()
        tax_invoice_time = _now_fiscal_time()
        session_parameters = self._resolve_session_parameters(None)

        try:
            start = self._start_transaction(
                function_id=130,
                valor_centavos=None,
                tax_invoice_number=tax_invoice_number,
                tax_invoice_date=tax_invoice_date,
                tax_invoice_time=tax_invoice_time,
                sitef_ip=settings.TEF_SITEF_IP or None,
                store_id=settings.TEF_STORE_ID or None,
                terminal_id=settings.TEF_TERMINAL_ID or None,
                cashier_operator=settings.TEF_CASHIER_OPERATOR or None,
                trn_additional_parameters=settings.TEF_TRN_PARAMETERS or None,
                trn_init_parameters=self._resolve_trn_init_parameters(130, None),
                session_parameters=session_parameters,
            )
        except requests.RequestException as exc:
            _set_pending_status("Falha ao iniciar pendencias TEF", {"error": str(exc)})
            return {
                "success": False,
                "error": f"Falha ao iniciar pendencias TEF: {exc}",
            }

        _log_tef_response("start", function_id, start, start.get("sessionId"))
        if int(start.get("serviceStatus") or 0) != 0:
            _set_pending_status("Agente retornou erro ao iniciar pendencias TEF", start)
            return {
                "success": False,
                "error": f"Agente retornou serviceStatus={start.get('serviceStatus')}",
                "detail": start,
            }

        if int(start.get("clisitefStatus") or 0) != 10000:
            _set_pending_status("CliSiTef nao iniciou pendencias", start)
            return {
                "success": False,
                "error": f"CliSiTef nao iniciou pendencias (status {start.get('clisitefStatus')})",
                "detail": start,
            }

        session_id = start.get("sessionId")
        if not session_id:
            _set_pending_status("Agente nao retornou sessionId", start)
            return {
                "success": False,
                "error": "Agente nao retornou sessionId no startTransaction",
                "detail": start,
            }

        next_continue = 0
        next_data = ""
        last_response: Dict[str, Any] | None = None
        data_hora_transacao = None
        nsu_host = None
        nsu_sitef = None

        for _ in range(PENDING_CONTINUE_MAX_ITERATIONS):
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
                _set_pending_status("Falha no continueTransaction pendencias", {"error": str(exc)})
                return {
                    "success": False,
                    "error": f"Falha no continueTransaction: {exc}",
                }

            _log_tef_response("continue", function_id, response, session_id)
            if int(response.get("serviceStatus") or 0) != 0:
                _set_pending_status("Erro no continueTransaction pendencias", response)
                return {
                    "success": False,
                    "error": f"Erro no continueTransaction (serviceStatus={response.get('serviceStatus')})",
                    "detail": response,
                }

            last_response = response
            clisitef_status = int(response.get("clisitefStatus") or 0)
            command_id = int(response.get("commandId") or 0)
            field_id = int(response.get("fieldId") or 0)
            response_data = response.get("data")

            if field_id == 105 and response_data:
                data_hora_transacao = str(response_data)
            elif field_id == 134 and response_data:
                nsu_host = str(response_data)
            elif field_id == 133 and response_data:
                nsu_sitef = str(response_data)

            if clisitef_status != 10000:
                break

            if command_id == 29:
                next_continue = 0
                next_data = self._default_input_value(response)
                continue

            if command_id in INPUT_COMMANDS:
                next_continue = 0
                next_data = self._default_input_value(response)
                continue

            if command_id in AUTO_ADVANCE_COMMANDS or (command_id == 0 and field_id > 0):
                next_continue = 0
                next_data = ""
                continue

            next_continue = 0
            next_data = ""

        try:
            finish = self._request(
                "POST",
                "/finishTransaction",
                {
                    "sessionId": session_id,
                    "confirm": 1 if confirmar else 0,
                    "taxInvoiceNumber": tax_invoice_number,
                    "taxInvoiceDate": tax_invoice_date,
                    "taxInvoiceTime": tax_invoice_time,
                },
            )
        except requests.RequestException as exc:
            _set_pending_status("Falha ao finalizar pendencias TEF", {"error": str(exc)})
            return {
                "success": False,
                "error": f"Falha ao finalizar pendencias TEF: {exc}",
            }

        finish_success = int(finish.get("serviceStatus") or 0) == 0
        data_hora_transacao = finish.get("data_hora_transacao") or finish.get("dataHoraTransacao") or data_hora_transacao
        nsu_host = finish.get("nsu_host") or finish.get("nsu") or nsu_host
        nsu_sitef = finish.get("nsu_sitef") or nsu_sitef
        message = _build_pending_resolution_message(
            confirmar=confirmar,
            success=finish_success,
            data_hora_transacao=data_hora_transacao,
            nsu_host=nsu_host,
        )

        pending_detail = {
            "finish": finish,
            "data_hora_transacao": data_hora_transacao,
            "nsu_host": nsu_host,
            "nsu_sitef": nsu_sitef,
            "confirmar": confirmar,
        }
        _set_pending_status(message, pending_detail)

        return {
            "success": finish_success,
            "session_id": session_id,
            "clisitef_status": int((last_response or {}).get("clisitefStatus") or 0),
            "message": message,
            "confirmar": confirmar,
            "data_hora_transacao": data_hora_transacao,
            "nsu_host": nsu_host,
            "nsu_sitef": nsu_sitef,
            "detail": finish,
        }





















