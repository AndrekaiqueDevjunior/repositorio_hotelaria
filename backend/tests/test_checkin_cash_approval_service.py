from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import checkin_cash_approval_service
from app.services.checkin_cash_approval_service import CheckinCashApprovalService
from app.utils.datetime_utils import now_utc


class FakeApprovalModel:
    def __init__(self):
        self.created = []

    async def create(self, data):
        self.created.append(data)
        return SimpleNamespace(id=5, codigo=data["codigo"])

    async def find_unique(self, where):
        return None


class FakeReservaModel:
    async def find_unique(self, where, include=None):
        return SimpleNamespace(
            id=10,
            clienteId=20,
            codigoReserva="RES-10",
            clienteNome="Joao Silva",
            cliente=SimpleNamespace(id=20, nomeCompleto="Joao Silva"),
        )


class FakeDbCashApproval:
    def __init__(self):
        self.reserva = FakeReservaModel()
        self.checkincashapproval = FakeApprovalModel()
        self.execute_calls = []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeWhatsAppCash:
    def __init__(self):
        self.calls = []

    async def enviar_confirmacao_checkin_dinheiro(self, **kwargs):
        self.calls.append(kwargs)
        return {"success": True, "message_sid": "SM-CHK"}


@pytest.mark.asyncio
async def test_solicitar_checkin_cash_approval_gera_chk_e_envia_whatsapp(monkeypatch):
    fake_whatsapp = FakeWhatsAppCash()
    monkeypatch.setattr(checkin_cash_approval_service, "get_whatsapp_service", lambda: fake_whatsapp)
    monkeypatch.setattr(checkin_cash_approval_service.secrets, "token_hex", lambda size: "abc123ef")

    db = FakeDbCashApproval()
    service = CheckinCashApprovalService(db)

    result = await service.solicitar(10, Decimal("2500.00"), funcionario_id=7)

    assert result["success"] is True
    assert result["approval_code"] == "CHK-ABC123EF"
    assert db.checkincashapproval.created[0]["status"] == "pending"
    assert fake_whatsapp.calls[0]["approval_code"] == "CHK-ABC123EF"
    assert fake_whatsapp.calls[0]["valor"] == 2500.0


class FakePagamentoModel:
    def __init__(self):
        self.created = []

    async def create(self, data):
        self.created.append(data)
        return SimpleNamespace(id=88)


class FakeTxApprove:
    def __init__(self, approval_status="pending"):
        self.approval_status = approval_status
        self.pagamento = FakePagamentoModel()
        self.execute_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query_raw(self, query, *args):
        if "FROM checkin_cash_approvals" in query:
            return [{
                "id": 5,
                "reserva_id": 10,
                "codigo": "CHK-ABC123EF",
                "valor": Decimal("2500.00"),
                "status": self.approval_status,
                "expira_em": now_utc() + timedelta(minutes=30),
            }]
        if "FROM reservas" in query:
            return [{
                "id": 10,
                "cliente_id": 20,
                "codigo_reserva": "RES-10",
                "cliente_nome": "Joao Silva",
                "status_reserva": "PENDENTE",
            }]
        if "FROM pagamentos" in query:
            return []
        return []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeDbApprove:
    def __init__(self, approval_status="pending"):
        self._tx = FakeTxApprove(approval_status=approval_status)

    def tx(self):
        return self._tx


@pytest.mark.asyncio
async def test_aprovar_chk_cria_pagamento_e_marca_codigo_usado():
    service = CheckinCashApprovalService(FakeDbApprove())

    result = await service.aprovar("CHK-ABC123EF", funcionario_id=7)

    assert result["success"] is True
    assert result["approved"] is True
    assert result["payment_id"] == 88
    assert service.db._tx.pagamento.created[0]["statusPagamento"] == "CONFIRMADO"
    assert any(call[1] == "approved" for call in service.db._tx.execute_calls)


@pytest.mark.asyncio
async def test_aprovar_chk_nao_reutiliza_codigo():
    service = CheckinCashApprovalService(FakeDbApprove(approval_status="approved"))

    with pytest.raises(HTTPException) as exc:
        await service.aprovar("CHK-ABC123EF", funcionario_id=7)

    assert exc.value.status_code == 400
    assert "utilizado" in exc.value.detail


class FakeDbListApprovals:
    def __init__(self):
        self.execute_calls = []
        self.query_args = None

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1

    async def query_raw(self, query, *args):
        self.query_args = args
        return [{
            "id": 9,
            "reserva_id": 10,
            "codigo": "CHK-ABC123EF",
            "valor": Decimal("2500.00"),
            "status": "pending",
            "expira_em": now_utc() + timedelta(minutes=20),
            "aprovado_em": None,
            "aprovado_por": None,
            "pagamento_id": None,
            "payload": {"requested_by": 7},
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "codigo_reserva": "RES-10",
            "cliente_nome": "Joao Silva",
            "quarto_numero": "201",
            "status_reserva": "PENDENTE",
            "cliente_telefone": "+5522999999999",
            "aprovado_por_nome": None,
        }]


@pytest.mark.asyncio
async def test_listar_chk_cash_approvals_retorna_pendentes_para_painel():
    db = FakeDbListApprovals()
    service = CheckinCashApprovalService(db)

    result = await service.listar(status="pending", limit=20)

    assert result["success"] is True
    assert result["total"] == 1
    assert db.query_args == ("pending", 20)
    approval = result["approvals"][0]
    assert approval["approval_code"] == "CHK-ABC123EF"
    assert approval["reservation_id"] == 10
    assert approval["guest_name"] == "Joao Silva"
    assert approval["room_number"] == "201"
    assert approval["amount"] == 2500.0
    assert approval["can_approve"] is True
