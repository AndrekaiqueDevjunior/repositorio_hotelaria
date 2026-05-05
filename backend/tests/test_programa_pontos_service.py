from types import SimpleNamespace

import pytest

from app.services.programa_pontos_service import ProgramaPontosService


class FakeModel:
    def __init__(self, *, find_unique_result=None, find_first_result=None):
        self.find_unique_result = find_unique_result
        self.find_first_result = find_first_result

    async def find_unique(self, **kwargs):
        return self.find_unique_result

    async def find_first(self, **kwargs):
        return self.find_first_result


class FakeDbPrograma:
    def __init__(self):
        self.cliente = FakeModel(find_unique_result=SimpleNamespace(id=1, nivelFidelidade=0))
        self.usuariopontos = FakeModel(find_unique_result=SimpleNamespace(saldo=18))
        self.premio = FakeModel(find_first_result=SimpleNamespace(id=10, nome="Diaria premio", precoEmPontos=20, categoria="HOSPEDAGEM"))
        self.query_calls = 0

    async def query_raw(self, *args):
        self.query_calls += 1
        if self.query_calls == 1:
            return [{"total": 21}]
        return [{"total": 2}]


def test_aplica_bonus_nivel_experiencia():
    nivel = ProgramaPontosService.nivel_por_codigo(1)
    calculo = ProgramaPontosService.aplicar_bonus_nivel(5, nivel)

    assert calculo["pontos_base"] == 5
    assert calculo["pontos_bonus_nivel"] == 1
    assert calculo["pontos_total"] == 6


def test_aplica_bonus_nivel_real():
    nivel = ProgramaPontosService.nivel_por_codigo(2)
    calculo = ProgramaPontosService.aplicar_bonus_nivel(5, nivel)

    assert calculo["pontos_base"] == 5
    assert calculo["pontos_bonus_nivel"] == 2
    assert calculo["pontos_total"] == 7


@pytest.mark.asyncio
async def test_programa_calcula_barras_nivel_e_premio():
    service = ProgramaPontosService(FakeDbPrograma())

    programa = await service.obter_programa_cliente(1)

    assert programa["success"] is True
    assert programa["nivel"]["nome"] == "EXPERIENCIA"
    assert programa["barra_premios"]["faltam_pontos"] == 2
    assert programa["premio_proximo"] is True
