import pytest

from app.repositories.cupom_repo import CupomRepository


class FakeDbCuponsInvalidacao:
    def __init__(self):
        self.calls = []

    async def query_raw(self, query, *args):
        self.calls.append((query, args))
        if "data_fim" in query:
            return [{"id": 1, "codigo": "AMIGO1"}]
        if "limite_total_usos" in query:
            return [{"id": 2, "codigo": "AMIGO2"}]
        return []


@pytest.mark.asyncio
async def test_processar_invalidacoes_automaticas_expira_e_esgota_cupons():
    db = FakeDbCuponsInvalidacao()
    repo = CupomRepository(db)

    resultado = await repo.processar_invalidacoes_automaticas()

    assert resultado["success"] is True
    assert resultado["cupons_expirados"] == 1
    assert resultado["cupons_esgotados"] == 1
    assert resultado["expirados"] == [{"id": 1, "codigo": "AMIGO1"}]
    assert resultado["esgotados"] == [{"id": 2, "codigo": "AMIGO2"}]
    assert db.calls[0][1][0] == "expired"
    assert db.calls[1][1][0] == "max_usage_reached"
