"""Normalizacao publica dos estados financeiros.

O banco preserva os valores operacionais/legados em maiusculas. A API expoe
um contrato pequeno e estavel para que reserva e pagamento nao sejam
confundidos no frontend.
"""

from typing import Any, Iterable, Optional


PAYMENT_STATUS_PUBLIC_MAP = {
    "PENDENTE": "pending",
    "PROCESSANDO": "processing",
    "AGUARDANDO_PAGAMENTO": "processing",
    "PAGO": "paid",
    "APROVADO": "paid",
    "CONFIRMADO": "paid",
    "CAPTURED": "paid",
    "AUTHORIZED": "paid",
    "PAID": "paid",
    "FALHOU": "failed",
    "RECUSADO": "failed",
    "NEGADO": "failed",
    "FAILED": "failed",
    "CANCELADO": "cancelled",
    "CANCELLED": "cancelled",
    "ESTORNADO": "refunded",
    "REFUNDED": "refunded",
}

PAYMENT_STATUS_STORAGE_MAP = {
    "APROVADO": "PAGO",
    "CONFIRMADO": "PAGO",
    "APPROVED": "PAGO",
    "PENDENTE": "PENDENTE",
    "PROCESSANDO": "PROCESSANDO",
    "AGUARDANDO_PAGAMENTO": "PROCESSANDO",
    "RECUSADO": "FALHOU",
    "NEGADO": "FALHOU",
    "FAILED": "FALHOU",
    "CANCELADO": "CANCELADO",
    "CANCELLED": "CANCELADO",
    "ESTORNADO": "ESTORNADO",
    "REFUNDED": "ESTORNADO",
}


def normalizar_status_pagamento_publico(status: Any) -> str:
    """Converte o status persistido no contrato publico da API."""
    status_raw = str(status or "PENDENTE").strip().upper()
    return PAYMENT_STATUS_PUBLIC_MAP.get(status_raw, "pending")


def normalizar_status_pagamento_persistido(status: Any) -> str:
    """Normaliza aliases sem apagar a diferenca pending/processing."""
    status_raw = str(status or "PENDENTE").strip().upper()
    return PAYMENT_STATUS_STORAGE_MAP.get(status_raw, status_raw)


def pagamento_mais_recente(pagamentos: Iterable[Any]) -> Optional[Any]:
    """Seleciona o ultimo pagamento pelo id monotonicamente crescente."""
    pagamentos_lista = list(pagamentos or [])
    if not pagamentos_lista:
        return None
    return max(pagamentos_lista, key=lambda pagamento: int(getattr(pagamento, "id", 0) or 0))
