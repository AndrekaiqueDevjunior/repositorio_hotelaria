import os
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from app.services import otp_service
from app.services.otp_service import OtpService
from app.utils.datetime_utils import now_utc


CPF_VALIDO = "11144477735"


class FakeOtpModel:
    def __init__(self):
        self.create_calls = []
        self.update_calls = []
        self.find_unique_result = None

    async def create(self, data):
        self.create_calls.append(data)
        return SimpleNamespace(id=data["id"])

    async def update(self, where, data):
        self.update_calls.append({"where": where, "data": data})
        return SimpleNamespace(**data)

    async def find_unique(self, where):
        return self.find_unique_result


class FakeClienteModel:
    def __init__(self, cliente=None):
        self.cliente = cliente

    async def find_unique(self, where):
        return self.cliente


class FakeDbOtp:
    def __init__(self, rate_limited=False, cliente_row=None):
        self.otpverificacao = FakeOtpModel()
        self.cliente = FakeClienteModel()
        self.rate_limited = rate_limited
        self.cliente_row = cliente_row or {
            "id": 10,
            "nome_completo": "Joao Silva",
            "documento": CPF_VALIDO,
            "telefone": "+55 22 99999-0000",
            "email": "joao@example.com",
            "status": "ATIVO",
            "created_at": now_utc(),
        }
        self.query_calls = []
        self.execute_calls = []

    async def query_raw(self, query, *args):
        self.query_calls.append((query, args))
        if "FROM clientes" in query:
            return [self.cliente_row] if self.cliente_row else []
        if "FROM otp_verificacoes" in query:
            return [{"id": "otp_recent", "ultimo_envio_em": now_utc()}] if self.rate_limited else []
        return []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeWhatsApp:
    def __init__(self):
        self.sent = []

    async def enviar_otp_verificacao(self, telefone_destino, codigo):
        self.sent.append({"telefone": telefone_destino, "codigo": codigo})
        return {"success": True, "message_sid": "SM123"}


@pytest.mark.asyncio
async def test_gerar_otp_envia_whatsapp_e_guarda_hash(monkeypatch):
    fake_whatsapp = FakeWhatsApp()
    monkeypatch.setattr(otp_service, "get_whatsapp_service", lambda: fake_whatsapp)
    monkeypatch.setattr(otp_service.secrets, "token_urlsafe", lambda size: "fixedtoken")
    monkeypatch.setattr(otp_service.secrets, "randbelow", lambda limit: 123456)

    db = FakeDbOtp()
    service = OtpService(db)

    resultado = await service.gerar_otp(CPF_VALIDO, ip="127.0.0.1", user_agent="pytest")

    assert resultado["success"] is True
    assert resultado["otp_id"] == "otp_fixedtoken"
    assert fake_whatsapp.sent == [{"telefone": "+55 22 99999-0000", "codigo": "123456"}]

    create_data = db.otpverificacao.create_calls[0]
    assert create_data["clienteId"] == 10
    assert create_data["documento"] == CPF_VALIDO
    assert create_data["codigoHash"] != "123456"
    assert create_data["status"] == "pending"
    assert create_data["maxTentativas"] == 3
    assert len(db.execute_calls) >= 2


@pytest.mark.asyncio
async def test_gerar_otp_respeita_rate_limit_de_um_minuto():
    service = OtpService(FakeDbOtp(rate_limited=True))

    with pytest.raises(HTTPException) as exc:
        await service.gerar_otp(CPF_VALIDO)

    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_validar_otp_correto_retorna_token(monkeypatch):
    monkeypatch.setattr(otp_service, "create_access_token", lambda data: "jwt-cliente")
    db = FakeDbOtp()
    service = OtpService(db)
    otp_id = "otp_valid"
    db.otpverificacao.find_unique_result = SimpleNamespace(
        id=otp_id,
        clienteId=10,
        documento=CPF_VALIDO,
        codigoHash=service._hash_codigo(otp_id, "123456"),
        status="pending",
        tentativas=0,
        maxTentativas=3,
        expiraEm=now_utc() + timedelta(minutes=5),
    )
    db.cliente.cliente = SimpleNamespace(
        id=10,
        nomeCompleto="Joao Silva",
        documento=CPF_VALIDO,
        telefone="+5522999990000",
        email="joao@example.com",
        status="ATIVO",
        createdAt=now_utc(),
    )

    resultado = await service.validar_otp(otp_id, "123456")

    assert resultado["success"] is True
    assert resultado["access_token"] == "jwt-cliente"
    assert resultado["scope"] == "jornada_reserva"
    assert resultado["customer"]["id"] == 10
    assert db.otpverificacao.update_calls[0]["data"]["status"] == "validated"


@pytest.mark.asyncio
async def test_validar_token_reserva_confere_escopo_documento_e_cliente(monkeypatch):
    monkeypatch.setattr(
        otp_service,
        "verify_token",
        lambda token, token_type="access": {
            "sub": "10",
            "scope": "jornada_reserva",
            "cliente_id": 10,
            "documento": CPF_VALIDO,
        },
    )
    db = FakeDbOtp()
    db.cliente.cliente = SimpleNamespace(
        id=10,
        nomeCompleto="Joao Silva",
        documento=CPF_VALIDO,
        telefone="+5522999990000",
        email="joao@example.com",
        status="ATIVO",
        createdAt=now_utc(),
    )
    service = OtpService(db)

    resultado = await service.validar_token_reserva("jwt-cliente", CPF_VALIDO)

    assert resultado["id"] == 10
    assert resultado["documento"] == CPF_VALIDO


@pytest.mark.asyncio
async def test_validar_token_reserva_rejeita_cpf_divergente(monkeypatch):
    monkeypatch.setattr(
        otp_service,
        "verify_token",
        lambda token, token_type="access": {
            "sub": "10",
            "scope": "jornada_reserva",
            "cliente_id": 10,
            "documento": CPF_VALIDO,
        },
    )
    service = OtpService(FakeDbOtp())

    with pytest.raises(HTTPException) as exc:
        await service.validar_token_reserva("jwt-cliente", "12345678909")

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_validar_otp_errado_bloqueia_na_terceira_tentativa():
    db = FakeDbOtp()
    service = OtpService(db)
    db.otpverificacao.find_unique_result = SimpleNamespace(
        id="otp_block",
        clienteId=10,
        documento=CPF_VALIDO,
        codigoHash=service._hash_codigo("otp_block", "123456"),
        status="pending",
        tentativas=2,
        maxTentativas=3,
        expiraEm=now_utc() + timedelta(minutes=5),
    )

    with pytest.raises(HTTPException) as exc:
        await service.validar_otp("otp_block", "000000")

    assert exc.value.status_code == 401
    assert db.otpverificacao.update_calls[0]["data"] == {
        "tentativas": 3,
        "status": "blocked",
    }
