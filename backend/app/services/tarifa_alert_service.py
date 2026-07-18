import json
import os
from datetime import date, datetime, timezone
from typing import Any, Dict, List

import httpx

from app.core.cache import cache


TARIFA_ALERT_CHANNEL = "operacional:tarifas:alertas"


class TarifaAlertService:
    def __init__(self, db):
        self.db = db

    async def verificar_temporadas_vencidas(self, disparar: bool = True) -> Dict[str, Any]:
        agora = datetime.now(timezone.utc)
        tarifas = await self.db.tarifasuite.find_many(
            where={"ativo": True}, order={"dataFim": "desc"}
        )

        vigentes = set()
        ultima_vencida_por_suite: Dict[str, Any] = {}
        for tarifa in tarifas:
            suite = str(getattr(tarifa, "suiteTipo", "") or "").upper().strip()
            if not suite:
                continue
            inicio = getattr(tarifa, "dataInicio", None)
            fim = getattr(tarifa, "dataFim", None)
            inicio_data = inicio.date() if hasattr(inicio, "date") else inicio
            fim_data = fim.date() if hasattr(fim, "date") else fim
            if inicio_data and fim_data and inicio_data <= agora.date() <= fim_data:
                vigentes.add(suite)
            if fim_data and fim_data < agora.date() and suite not in ultima_vencida_por_suite:
                ultima_vencida_por_suite[suite] = tarifa

        vencidas: List[Dict[str, Any]] = []
        for suite, tarifa in ultima_vencida_por_suite.items():
            fim = getattr(tarifa, "dataFim", None)
            if suite not in vigentes and fim:
                vencidas.append({
                    "tarifa_id": tarifa.id,
                    "suite_tipo": suite,
                    "temporada": getattr(tarifa, "temporada", None),
                    "data_fim": fim.date().isoformat(),
                    "preco_diaria": float(getattr(tarifa, "precoDiaria", 0) or 0),
                })

        payload = {
            "evento": "TARIFA_TEMPORADA_VENCIDA",
            "ativo": bool(vencidas),
            "titulo": "Temporada tarifaria vencida",
            "mensagem": (
                f"Atualize os valores de tarifa para {len(vencidas)} tipo(s) de suite."
                if vencidas else "Todas as suites possuem tarifa vigente."
            ),
            "tarifas_vencidas": vencidas,
            "url_acao": "/tarifas",
            "verificado_em": agora.isoformat(),
        }

        if disparar and vencidas:
            await self._disparar_uma_vez_ao_dia(payload, agora.date())
        return payload

    async def _disparar_uma_vez_ao_dia(self, payload: Dict[str, Any], hoje: date) -> None:
        chave = f"tarifa-alerta:disparado:{hoje.isoformat()}"
        deve_disparar = True
        if cache.redis is not None:
            deve_disparar = bool(await cache.redis.set(chave, "1", ex=86400, nx=True))
        if not deve_disparar:
            return

        if cache.redis is not None:
            await cache.redis.publish(TARIFA_ALERT_CHANNEL, json.dumps(payload, default=str))

        webhook_url = os.getenv("TARIFA_ALERT_WEBHOOK_URL", "").strip()
        if webhook_url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(webhook_url, json=payload)
                    response.raise_for_status()
            except Exception as exc:
                print(f"[TARIFA ALERTA] Falha ao enviar webhook: {exc}")
