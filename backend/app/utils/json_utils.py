"""Conversoes seguras para respostas JSON da API."""

from fastapi.encoders import jsonable_encoder


def to_json_safe(payload):
    """Converte datas, Decimals e modelos em tipos serializaveis por JSON."""
    return jsonable_encoder(payload)
