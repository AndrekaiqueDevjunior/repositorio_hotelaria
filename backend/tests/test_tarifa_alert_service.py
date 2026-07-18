from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.tarifa_alert_service import TarifaAlertService


class FakeTarifas:
    def __init__(self, values):
        self.values = values

    async def find_many(self, **kwargs):
        return self.values


@pytest.mark.asyncio
async def test_alerta_retorna_apenas_suite_sem_tarifa_vigente():
    agora = datetime.now(timezone.utc)
    tarifas = [
        SimpleNamespace(id=1, suiteTipo="LUXO", temporada="Baixa", dataInicio=agora - timedelta(days=30), dataFim=agora - timedelta(days=1), precoDiaria=200),
        SimpleNamespace(id=2, suiteTipo="MASTER", temporada="Atual", dataInicio=agora - timedelta(days=1), dataFim=agora + timedelta(days=30), precoDiaria=300),
    ]
    db = SimpleNamespace(tarifasuite=FakeTarifas(tarifas))

    resultado = await TarifaAlertService(db).verificar_temporadas_vencidas(disparar=False)

    assert resultado["ativo"] is True
    assert [item["suite_tipo"] for item in resultado["tarifas_vencidas"]] == ["LUXO"]


@pytest.mark.asyncio
async def test_alerta_inativo_quando_todas_as_tarifas_estao_vigentes():
    agora = datetime.now(timezone.utc)
    tarifa = SimpleNamespace(id=1, suiteTipo="REAL", temporada="Atual", dataInicio=agora - timedelta(days=1), dataFim=agora + timedelta(days=30), precoDiaria=500)
    db = SimpleNamespace(tarifasuite=FakeTarifas([tarifa]))

    resultado = await TarifaAlertService(db).verificar_temporadas_vencidas(disparar=False)

    assert resultado["ativo"] is False
    assert resultado["tarifas_vencidas"] == []
