import pytest

from app.services.jornada_service import JornadaService


class FakeDbJornada:
    async def query_raw(self, sql, *args):
        if "regexp_replace(documento" in sql or "FROM clientes" in sql:
            return [{
                "id": 10,
                "nomeCompleto": "Joao Silva",
                "documento": "52998224725",
                "telefone": "22999999999",
                "email": "joao@example.com",
            }]

        if "FROM usuarios_pontos" in sql:
            return [{"saldo": 72}]

        if "SUM(pontos)" in sql:
            return [{"total": 0}]

        if "FROM niveis_fidelidade" in sql:
            return [
                {"id": 1, "codigo": 0, "nome": "ESSENCIA", "pontos_minimos": 0, "ordem": 0},
                {"id": 2, "codigo": 1, "nome": "EXPERIENCIA", "pontos_minimos": 50, "ordem": 1},
                {"id": 3, "codigo": 2, "nome": "REAL", "pontos_minimos": 90, "ordem": 2},
            ]

        if "FROM premios p" in sql:
            return [
                {"id": 1, "nome": "1 diaria", "descricao": None, "preco_em_pontos": 25, "estoque": 3, "categoria": "O Retorno do Sonho"},
                {"id": 2, "nome": "Cafeteira Premium", "descricao": None, "preco_em_pontos": 35, "estoque": 5, "categoria": "Rituais do Real"},
                {"id": 3, "nome": "iPhone 16", "descricao": None, "preco_em_pontos": 90, "estoque": 1, "categoria": "Tecnologia Real"},
            ]

        if "FROM beneficios_nivel" in sql:
            return []

        if "FROM transacoes_pontos" in sql:
            return []

        if "FROM resgates_premios" in sql:
            return []

        return []

    async def execute_raw(self, *args):
        return 1


@pytest.mark.asyncio
async def test_dashboard_jornada_cliente_72_pontos():
    service = JornadaService(FakeDbJornada())

    dashboard = await service.montar_dashboard_jornada(10)

    assert dashboard["cliente"]["nome"] == "Joao"
    assert dashboard["pontos"]["saldo"] == 72
    assert dashboard["nivel"]["atual"] == "Experiência"
    assert dashboard["nivel"]["pontos_inicio"] == 50
    assert dashboard["nivel"]["pontos_meta"] == 90
    assert dashboard["nivel"]["faltam_proximo_nivel"] == 18
    assert dashboard["nivel"]["percentual"] == 55
    assert dashboard["progresso_premios"] == {"alcancados": 2, "total": 3}


@pytest.mark.asyncio
async def test_consulta_jornada_por_cpf_retorna_dashboard():
    service = JornadaService(FakeDbJornada())

    dashboard = await service.consultar_jornada_por_cpf("529.982.247-25")

    assert dashboard["success"] is True
    assert dashboard["cliente"]["id"] == 10
    assert dashboard["nivel"]["codigo"] == "experiencia"
