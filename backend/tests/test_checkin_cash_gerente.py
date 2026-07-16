"""Aprovacao de check-in em dinheiro pelo gerente via WhatsApp.

O pedido sai pelo content template quick-reply TEMPLATE_CHECKIN_DINHEIRO_GERENTE
(botoes Aprovar/Recusar) e a resposta volta no webhook /twilio/whatsapp/incoming
como ButtonPayload chk_aprovar_<CHK> / chk_recusar_<CHK>.
"""
import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("CIELO_MERCHANT_ID", "test-merchant")
os.environ.setdefault("CIELO_MERCHANT_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from app.api.v1 import twilio_routes
from app.services.whatsapp_service import WhatsAppService


class FakeMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(sid=f"SM-{len(self.calls)}", status="queued")


def make_service(monkeypatch, gerentes="+5522999643131"):
    monkeypatch.setenv("TWILIO_WHATSAPP_ENABLED", "false")  # evita Client real
    monkeypatch.setenv("FRONTEND_BASE_URL", "https://hotelrealcabofrio.com")
    service = WhatsAppService()
    service.client = SimpleNamespace(messages=FakeMessages())
    service.gerente_numbers = [g.strip() for g in gerentes.split(",") if g.strip()]
    return service


def test_numero_gerente_padrao(monkeypatch):
    monkeypatch.setenv("TWILIO_WHATSAPP_ENABLED", "false")
    monkeypatch.delenv("WHATSAPP_GERENTE_NUMERO", raising=False)
    service = WhatsAppService()
    assert service.gerente_numbers == ["+5522999643131"]


@pytest.mark.asyncio
async def test_aprovacao_gerente_usa_template_quick_reply(monkeypatch):
    service = make_service(monkeypatch)

    resultado = await service.enviar_aprovacao_checkin_gerente(
        cliente_nome="Joao Silva",
        cliente_cpf="123.456.789-00",
        recepcionista_nome="Maria Souza",
        valor=350.0,
        horario_checkin="16/07/2026 14:30",
        approval_code="CHK-AB12CD34",
    )

    calls = service.client.messages.calls
    assert resultado["success"] is True
    assert len(calls) == 1
    call = calls[0]
    assert call["to"] == "whatsapp:+5522999643131"
    assert call["content_sid"] == WhatsAppService.TEMPLATE_CHECKIN_DINHEIRO_GERENTE
    assert "body" not in call

    variables = json.loads(call["content_variables"])
    assert set(variables.keys()) == {"1", "2", "3", "4", "5", "6", "7"}
    assert variables["1"] == "Joao Silva"
    assert variables["2"] == "123.456.789-00"
    assert variables["3"] == "Maria Souza"
    assert variables["4"] == "350.00"
    assert variables["5"] == "16/07/2026 14:30"
    assert "checkin-approvals" in variables["6"]  # fallback sem foto: link do painel
    assert variables["7"] == "CHK-AB12CD34"


@pytest.mark.asyncio
async def test_aprovacao_gerente_foto_do_dominio_usa_template_card(monkeypatch):
    """Foto hospedada no site do hotel vai embutida via template card: o
    template fixa o prefixo https://hotelrealcabofrio.com/ na media, entao
    o slot 6 leva so o caminho relativo."""
    service = make_service(monkeypatch)

    await service.enviar_aprovacao_checkin_gerente(
        cliente_nome="Joao",
        cliente_cpf=None,
        recepcionista_nome=None,
        valor=100.0,
        horario_checkin="16/07/2026 10:00",
        approval_code="CHK-FF00AA11",
        foto_link="https://hotelrealcabofrio.com/uploads/foto123.jpg",
    )

    call = service.client.messages.calls[0]
    assert call["content_sid"] == WhatsAppService.TEMPLATE_CHECKIN_DINHEIRO_GERENTE_FOTO
    variables = json.loads(call["content_variables"])
    assert variables["2"] == "nao informado"
    assert variables["3"] == "-"
    assert variables["6"] == "uploads/foto123.jpg"


@pytest.mark.asyncio
async def test_aprovacao_gerente_foto_externa_cai_no_quick_reply_com_link(monkeypatch):
    service = make_service(monkeypatch)

    await service.enviar_aprovacao_checkin_gerente(
        cliente_nome="Joao",
        cliente_cpf=None,
        recepcionista_nome=None,
        valor=100.0,
        horario_checkin="16/07/2026 10:00",
        approval_code="CHK-FF00AA22",
        foto_link="https://imgur.com/foto-externa.jpg",
    )

    call = service.client.messages.calls[0]
    assert call["content_sid"] == WhatsAppService.TEMPLATE_CHECKIN_DINHEIRO_GERENTE
    variables = json.loads(call["content_variables"])
    assert variables["6"] == "https://imgur.com/foto-externa.jpg"


@pytest.mark.asyncio
async def test_aprovacao_gerente_sem_numero_retorna_erro(monkeypatch):
    service = make_service(monkeypatch, gerentes="")

    resultado = await service.enviar_aprovacao_checkin_gerente(
        cliente_nome="Joao",
        cliente_cpf=None,
        recepcionista_nome=None,
        valor=100.0,
        horario_checkin="16/07/2026 10:00",
        approval_code="CHK-11223344",
    )

    assert resultado["success"] is False
    assert not service.client.messages.calls


def test_extrair_acao_chk_do_button_payload():
    # ids fixos dos botoes do template (Meta nao permite variavel em botao);
    # o codigo CHK vem depois via OriginalRepliedMessageSid
    assert twilio_routes._extrair_acao_chk(
        {"ButtonPayload": "chk_aprovar"}
    ) == ("aprovar", None)
    assert twilio_routes._extrair_acao_chk(
        {"ButtonPayload": "chk_recusar"}
    ) == ("recusar", None)
    # resposta digitada manualmente com o codigo explicito
    assert twilio_routes._extrair_acao_chk(
        {"Body": "chk_aprovar_chk-ab12cd34"}
    ) == ("aprovar", "CHK-AB12CD34")
    assert twilio_routes._extrair_acao_chk({"Body": "Oi, tudo bem?"}) is None
    assert twilio_routes._extrair_acao_chk({"ButtonPayload": "outro_botao"}) is None


def _make_foto_db(approval=None, comprovante=None):
    async def find_unique(where=None):
        return approval

    async def find_first(where=None, order=None):
        return comprovante

    return SimpleNamespace(
        checkincashapproval=SimpleNamespace(find_unique=find_unique),
        comprovantepagamento=SimpleNamespace(find_first=find_first),
    )


@pytest.mark.asyncio
async def test_obter_foto_retorna_arquivo_do_comprovante():
    from app.services.checkin_cash_approval_service import CheckinCashApprovalService
    from app.utils.datetime_utils import now_utc

    approval = SimpleNamespace(pagamentoId=9, createdAt=now_utc())
    comprovante = SimpleNamespace(
        caminhoArquivo="uploads/comprovantes/1_cliente/2026/07/foto.jpg",
        nomeArquivo="foto.jpg",
    )
    service = CheckinCashApprovalService(_make_foto_db(approval, comprovante))

    info = await service.obter_foto("chk-ab12cd34")

    assert info["caminho"] == "uploads/comprovantes/1_cliente/2026/07/foto.jpg"
    assert info["nome"] == "foto.jpg"


@pytest.mark.asyncio
async def test_obter_foto_bloqueia_apos_24h_e_casos_invalidos():
    from datetime import timedelta

    from fastapi import HTTPException

    from app.services.checkin_cash_approval_service import CheckinCashApprovalService
    from app.utils.datetime_utils import now_utc

    comprovante = SimpleNamespace(caminhoArquivo="uploads/x.jpg", nomeArquivo="x.jpg")

    # janela de 24h vencida: o link no WhatsApp do gerente para de servir
    velho = SimpleNamespace(pagamentoId=9, createdAt=now_utc() - timedelta(hours=25))
    service = CheckinCashApprovalService(_make_foto_db(velho, comprovante))
    with pytest.raises(HTTPException) as exc:
        await service.obter_foto("CHK-AB12CD34")
    assert exc.value.status_code == 404

    # codigo fora do padrao CHK
    service = CheckinCashApprovalService(_make_foto_db(None, None))
    with pytest.raises(HTTPException):
        await service.obter_foto("qualquer-coisa")

    # approval sem pagamento vinculado (fluxo antigo, sem foto)
    sem_pagamento = SimpleNamespace(pagamentoId=None, createdAt=now_utc())
    service = CheckinCashApprovalService(_make_foto_db(sem_pagamento, comprovante))
    with pytest.raises(HTTPException):
        await service.obter_foto("CHK-AB12CD34")

    # approval ok mas sem comprovante anexado
    recente = SimpleNamespace(pagamentoId=9, createdAt=now_utc())
    service = CheckinCashApprovalService(_make_foto_db(recente, None))
    with pytest.raises(HTTPException):
        await service.obter_foto("CHK-AB12CD34")


def test_numero_e_gerente(monkeypatch):
    monkeypatch.setattr(
        twilio_routes,
        "get_whatsapp_service",
        lambda: SimpleNamespace(gerente_numbers=["+5522999643131"]),
    )
    assert twilio_routes._numero_e_gerente("whatsapp:+5522999643131") is True
    assert twilio_routes._numero_e_gerente("+55 22 99964-3131") is True
    assert twilio_routes._numero_e_gerente("whatsapp:+5511999999999") is False
    assert twilio_routes._numero_e_gerente("") is False
