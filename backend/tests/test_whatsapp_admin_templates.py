"""Alertas internos ao admin devem sair pelo content template aprovado.

Texto livre business-initiated fora da janela de 24h cai em undelivered
(erro Twilio 63016) sem falhar o create -- estes testes garantem que nenhum
alerta admin volte a usar `body=` free-form.
"""
import json
from types import SimpleNamespace

import pytest

from app.services.whatsapp_service import WhatsAppService


class FakeMessages:
    def __init__(self, fail_first=False):
        self.calls = []
        self.fail_first = fail_first

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_first and len(self.calls) == 1:
            raise RuntimeError("falha simulada no primeiro numero")
        return SimpleNamespace(sid=f"SM-{len(self.calls)}", status="queued")


def make_service(monkeypatch, numeros="+5511968029600,+5511900000000", fail_first=False):
    monkeypatch.setenv("TWILIO_WHATSAPP_ENABLED", "false")  # evita Client real
    monkeypatch.setenv("FRONTEND_BASE_URL", "https://hotelrealcabofrio.com")
    service = WhatsAppService()
    service.client = SimpleNamespace(messages=FakeMessages(fail_first=fail_first))
    service.notification_numbers = [n.strip() for n in numeros.split(",") if n.strip()]
    service.notification_number = service.notification_numbers[0] if service.notification_numbers else ""
    return service


def _assert_template_call(call):
    assert call["content_sid"] == WhatsAppService.TEMPLATE_RESERVA_CONFIRMADA
    assert "body" not in call
    variables = json.loads(call["content_variables"])
    assert set(variables.keys()) == {"1", "2", "3", "4", "5"}
    return variables


@pytest.mark.asyncio
async def test_checkin_dinheiro_usa_template_aprovado(monkeypatch):
    service = make_service(monkeypatch)

    resultado = await service.enviar_confirmacao_checkin_dinheiro(
        codigo_reserva="RES-10",
        cliente_nome="Joao Silva",
        valor=2500.0,
        comprovante_id=7,
        reserva_id=10,
        approval_code="CHK-ABC123",
    )

    calls = service.client.messages.calls
    assert resultado["success"] is True
    assert len(calls) == 2  # fan-out para todos os numeros configurados

    variables = _assert_template_call(calls[0])
    assert "RES-10" in variables["1"]
    assert "Joao Silva" in variables["1"]
    assert "CHK-ABC123" in variables["2"]
    assert "checkin-approvals" in variables["3"]
    assert variables["5"] == "2500.00"


@pytest.mark.asyncio
async def test_resgate_premio_usa_template(monkeypatch):
    service = make_service(monkeypatch, numeros="+5511968029600")

    await service.enviar_notificacao_resgate_premio(
        cliente_nome="Maria",
        cliente_telefone="+5522999990000",
        cliente_endereco="Rua A, 10",
        premio_nome="iPhone 16e",
        pontos_usados=90,
        codigo_resgate="REAL-XYZ123",
    )

    variables = _assert_template_call(service.client.messages.calls[0])
    assert "REAL-XYZ123" in variables["1"]
    assert "iPhone 16e" in variables["2"]
    assert "90 pontos" in variables["4"]


@pytest.mark.asyncio
async def test_notificacao_pagamento_usa_template(monkeypatch):
    service = make_service(monkeypatch, numeros="+5511968029600")

    await service.enviar_notificacao_pagamento(
        evento="aprovado",
        codigo_reserva="RES-22",
        cliente_nome="Pedro",
        valor=350.5,
        metodo="TEF",
        status="APROVADO",
        tef_nsu="123456",
        pagamento_id=9,
    )

    variables = _assert_template_call(service.client.messages.calls[0])
    assert variables["1"].startswith("PGTO aprovado - RES-22")
    assert "TEF NSU: 123456" in variables["3"]
    assert variables["5"] == "350.50"


@pytest.mark.asyncio
async def test_checkin_realizado_usa_template(monkeypatch):
    service = make_service(monkeypatch, numeros="+5511968029600")

    await service.enviar_notificacao_checkin_realizado(
        codigo_reserva="RES-33",
        cliente_nome="Ana",
        quarto_numero="201",
        num_hospedes=2,
        num_criancas=1,
        reserva_id=33,
    )

    variables = _assert_template_call(service.client.messages.calls[0])
    assert "CHECK-IN REALIZADO" in variables["1"]
    assert "Quarto 201" in variables["2"]
    assert "Hospedes: 2" in variables["2"]
    assert "/reservas/33" in variables["4"]


@pytest.mark.asyncio
async def test_evento_reserva_nao_criada_usa_template(monkeypatch):
    service = make_service(monkeypatch, numeros="+5511968029600")

    await service.enviar_notificacao_evento_reserva(
        evento="cancelada",
        codigo_reserva="RES-44",
        cliente_nome="Rui",
        quarto_numero="102",
        checkin_previsto="2026-07-10",
        checkout_previsto="2026-07-12",
        valor_total=800.0,
        status="CANCELADA",
        detalhe="cancelada pelo cliente",
        reserva_id=44,
    )

    variables = _assert_template_call(service.client.messages.calls[0])
    assert "CANCELADA" in variables["1"]
    assert variables["2"] == "2026-07-10"
    assert "cancelada pelo cliente" in variables["4"]
    assert variables["5"] == "800.00"


@pytest.mark.asyncio
async def test_evento_criada_delega_para_admin(monkeypatch):
    service = make_service(monkeypatch, numeros="+5511968029600")

    await service.enviar_notificacao_evento_reserva(
        evento="criada",
        codigo_reserva="RES-55",
        cliente_nome="Bia",
        quarto_numero="303",
        checkin_previsto="2026-07-15",
        checkout_previsto="2026-07-18",
        valor_total=1200.0,
        status="PENDENTE",
        tipo_suite="LUXO",
    )

    variables = _assert_template_call(service.client.messages.calls[0])
    # comportamento pre-existente do alerta de nova reserva preservado
    assert variables["1"] == "RES-55 - Bia"
    assert "LUXO" in variables["4"]


@pytest.mark.asyncio
async def test_variaveis_sanitizadas_sem_quebra_de_linha(monkeypatch):
    service = make_service(monkeypatch, numeros="+5511968029600")

    await service.enviar_notificacao_checkin_realizado(
        codigo_reserva="RES-66",
        cliente_nome="Carlos",
        quarto_numero="105",
        observacoes="linha1\nlinha2\tcom tab    e espacos " + "x" * 300,
    )

    variables = json.loads(service.client.messages.calls[0]["content_variables"])
    for valor in variables.values():
        assert "\n" not in valor
        assert "\t" not in valor
        assert "    " not in valor  # 4+ espacos seguidos
        assert len(valor) <= 160


@pytest.mark.asyncio
async def test_sem_numeros_configurados_retorna_erro(monkeypatch):
    service = make_service(monkeypatch, numeros="")

    resultado = await service.enviar_notificacao_pagamento(
        evento="aprovado",
        codigo_reserva="RES-77",
        cliente_nome="Duda",
        valor=100.0,
    )

    assert resultado["success"] is False
    assert not service.client.messages.calls


@pytest.mark.asyncio
async def test_agrega_resultados_e_success_any(monkeypatch):
    service = make_service(monkeypatch, fail_first=True)

    resultado = await service.enviar_confirmacao_checkin_dinheiro(
        codigo_reserva="RES-88",
        cliente_nome="Eva",
        valor=500.0,
        approval_code="CHK-DEF456",
    )

    assert len(service.client.messages.calls) == 2
    assert len(resultado["resultados"]) == 2
    assert resultado["resultados"][0]["success"] is False
    assert resultado["resultados"][1]["success"] is True
    assert resultado["success"] is True
