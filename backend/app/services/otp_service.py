import hashlib
import hmac
import json
import os
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.core.enums import PerfilUsuario
from app.core.security import create_access_token, verify_token
from app.core.validators import ClienteValidator
from app.schemas.cliente_schema import ClienteCreate
from app.repositories.cliente_repo import ClienteRepository
from app.services.cliente_service import ClienteService
from app.services.whatsapp_service import get_whatsapp_service
from app.utils.datetime_utils import now_utc, to_utc


OTP_STATUS_PENDING = "pending"
OTP_STATUS_VALIDATED = "validated"
OTP_STATUS_EXPIRED = "expired"
OTP_STATUS_BLOCKED = "blocked"
OTP_STATUS_DELIVERY_FAILED = "delivery_failed"

OTP_TTL_MINUTES = 5
OTP_MIN_INTERVAL_SECONDS = 60
OTP_MAX_ATTEMPTS = 3


def normalizar_documento(documento: str) -> str:
    return "".join(filter(str.isdigit, documento or ""))


def normalizar_telefone(telefone: str) -> str:
    return "".join(filter(str.isdigit, telefone or ""))


def validar_cpf_ou_erro(cpf: str) -> str:
    cpf_norm = normalizar_documento(cpf)
    ClienteValidator.validar_cpf(cpf_norm)
    return cpf_norm


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


class OtpService:
    def __init__(self, db):
        self.db = db

    async def obter_customer_por_cpf(self, cpf: str) -> Dict[str, Any]:
        cpf_norm = validar_cpf_ou_erro(cpf)
        cliente = await self._buscar_cliente_por_documento(cpf_norm)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nao encontrado")
        return self._serialize_cliente(cliente)

    async def criar_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cpf_norm = validar_cpf_ou_erro(data.get("documento") or data.get("cpf") or "")
        payload = ClienteCreate(
            nome_completo=data["nome_completo"],
            documento=cpf_norm,
            telefone=data.get("telefone"),
            email=data.get("email"),
        )
        try:
            cliente = await ClienteService(ClienteRepository(self.db)).create(payload)
        except HTTPException as exc:
            detail = str(exc.detail)
            if "ja esta cadastrado" in detail.lower() or "já está cadastrado" in detail.lower():
                raise HTTPException(status_code=409, detail=exc.detail)
            raise
        return cliente

    async def gerar_otp(
        self,
        cpf: str,
        telefone: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        cpf_norm = validar_cpf_ou_erro(cpf)
        cliente = await self._buscar_cliente_por_documento(cpf_norm)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nao encontrado")

        telefone_destino = telefone or _row_get(cliente, "telefone")
        telefone_norm = normalizar_telefone(telefone_destino)
        if len(telefone_norm) < 10:
            raise HTTPException(status_code=400, detail="Cliente sem telefone valido para OTP")

        await self._verificar_rate_limit(cpf_norm, telefone_norm)
        await self._expirar_otps_pendentes(cpf_norm, telefone_norm)

        otp_id = f"otp_{secrets.token_urlsafe(18)}"
        codigo = f"{secrets.randbelow(1_000_000):06d}"
        expira_em = now_utc() + timedelta(minutes=OTP_TTL_MINUTES)

        otp = await self.db.otpverificacao.create(
            data={
                "id": otp_id,
                "clienteId": int(_row_get(cliente, "id")),
                "documento": cpf_norm,
                "telefone": telefone_norm,
                "codigoHash": self._hash_codigo(otp_id, codigo),
                "status": OTP_STATUS_PENDING,
                "tentativas": 0,
                "maxTentativas": OTP_MAX_ATTEMPTS,
                "expiraEm": expira_em,
                "ultimoEnvioEm": now_utc(),
                "ip": ip,
                "userAgent": user_agent,
            }
        )

        await self._registrar_log(
            int(_row_get(cliente, "id")),
            "otp_generate",
            {"otp_id": otp_id, "documento": cpf_norm, "telefone": telefone_norm},
            ip,
            user_agent,
        )

        entrega = await get_whatsapp_service().enviar_otp_verificacao(
            telefone_destino=telefone_destino,
            codigo=codigo,
        )
        if not entrega.get("success") and self._is_production():
            await self.db.otpverificacao.update(
                where={"id": otp_id},
                data={"status": OTP_STATUS_DELIVERY_FAILED},
            )
            await self._registrar_log(
                int(_row_get(cliente, "id")),
                "otp_delivery_failed",
                {"otp_id": otp_id, "error": entrega.get("error")},
                ip,
                user_agent,
            )
            raise HTTPException(status_code=503, detail="Falha ao enviar OTP via WhatsApp")

        return {
            "success": True,
            "otp_id": otp.id,
            "expires_in_seconds": OTP_TTL_MINUTES * 60,
            "max_attempts": OTP_MAX_ATTEMPTS,
            "channel": "whatsapp",
            "delivery": entrega,
        }

    async def validar_otp(
        self,
        otp_id: str,
        code: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        codigo = (code or "").strip()
        if not codigo.isdigit() or len(codigo) != 6:
            raise HTTPException(status_code=400, detail="OTP deve ter 6 digitos")

        otp = await self.db.otpverificacao.find_unique(where={"id": otp_id})
        if not otp:
            raise HTTPException(status_code=404, detail="OTP nao encontrado")

        cliente_id = _row_get(otp, "clienteId")
        status = (_row_get(otp, "status") or "").lower()
        expira_em = to_utc(_row_get(otp, "expiraEm"))
        tentativas = int(_row_get(otp, "tentativas") or 0)
        max_tentativas = int(_row_get(otp, "maxTentativas") or OTP_MAX_ATTEMPTS)

        if status != OTP_STATUS_PENDING:
            raise HTTPException(status_code=400, detail=f"OTP indisponivel: {status}")

        if expira_em and expira_em < now_utc():
            await self.db.otpverificacao.update(
                where={"id": otp_id},
                data={"status": OTP_STATUS_EXPIRED},
            )
            await self._registrar_log(cliente_id, "otp_expired", {"otp_id": otp_id}, ip, user_agent)
            raise HTTPException(status_code=400, detail="OTP expirado")

        if tentativas >= max_tentativas:
            await self.db.otpverificacao.update(
                where={"id": otp_id},
                data={"status": OTP_STATUS_BLOCKED},
            )
            raise HTTPException(status_code=400, detail="OTP bloqueado por excesso de tentativas")

        if not hmac.compare_digest(self._hash_codigo(otp_id, codigo), _row_get(otp, "codigoHash") or ""):
            nova_tentativa = tentativas + 1
            novo_status = OTP_STATUS_BLOCKED if nova_tentativa >= max_tentativas else OTP_STATUS_PENDING
            await self.db.otpverificacao.update(
                where={"id": otp_id},
                data={"tentativas": nova_tentativa, "status": novo_status},
            )
            await self._registrar_log(
                cliente_id,
                "otp_validate_failed",
                {
                    "otp_id": otp_id,
                    "tentativas": nova_tentativa,
                    "remaining_attempts": max(0, max_tentativas - nova_tentativa),
                },
                ip,
                user_agent,
            )
            raise HTTPException(
                status_code=401,
                detail=f"Codigo invalido. {max(0, max_tentativas - nova_tentativa)} tentativas restantes",
            )

        validado_em = now_utc()
        await self.db.otpverificacao.update(
            where={"id": otp_id},
            data={
                "status": OTP_STATUS_VALIDATED,
                "validadoEm": validado_em,
            },
        )

        cliente = await self.db.cliente.find_unique(where={"id": int(cliente_id)})
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nao encontrado")

        token = create_access_token(
            {
                "sub": str(cliente.id),
                "email": getattr(cliente, "email", "") or "",
                "perfil": PerfilUsuario.CLIENTE.value,
                "scope": "jornada_reserva",
                "cliente_id": int(cliente.id),
                "documento": normalizar_documento(getattr(cliente, "documento", "")),
            }
        )
        await self._registrar_log(
            int(cliente.id),
            "otp_validated",
            {"otp_id": otp_id, "documento": normalizar_documento(getattr(cliente, "documento", ""))},
            ip,
            user_agent,
        )

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "scope": "jornada_reserva",
            "customer": self._serialize_cliente(cliente),
            "validated_at": validado_em.isoformat(),
        }

    async def validar_token_reserva(self, token: str, documento: str) -> Dict[str, Any]:
        if not token:
            raise HTTPException(status_code=401, detail="Autenticacao por WhatsApp obrigatoria para reservar")

        payload = verify_token(token, token_type="access")
        documento_norm = validar_cpf_ou_erro(documento)
        token_documento = normalizar_documento(payload.get("documento") or "")

        if payload.get("scope") != "jornada_reserva" or token_documento != documento_norm:
            raise HTTPException(status_code=403, detail="Token de autenticacao nao corresponde ao CPF informado")

        cliente_id = payload.get("cliente_id") or payload.get("sub")
        try:
            cliente_id_int = int(cliente_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Token de autenticacao invalido")

        cliente = await self.db.cliente.find_unique(where={"id": cliente_id_int})
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nao encontrado")

        if normalizar_documento(_row_get(cliente, "documento")) != documento_norm:
            raise HTTPException(status_code=403, detail="CPF do token nao corresponde ao cadastro")

        return self._serialize_cliente(cliente)

    async def _buscar_cliente_por_documento(self, documento: str) -> Optional[Any]:
        rows = await self.db.query_raw(
            """
            SELECT id,
                   "nomeCompleto" AS nome_completo,
                   documento,
                   telefone,
                   email,
                   status,
                   "createdAt" AS created_at
            FROM clientes
            WHERE regexp_replace(documento, '\\D', '', 'g') = $1
            LIMIT 1
            """,
            documento,
        )
        return rows[0] if rows else None

    async def _verificar_rate_limit(self, documento: str, telefone: str) -> None:
        limite = now_utc() - timedelta(seconds=OTP_MIN_INTERVAL_SECONDS)
        rows = await self.db.query_raw(
            """
            SELECT id, ultimo_envio_em
            FROM otp_verificacoes
            WHERE (documento = $1 OR regexp_replace(telefone, '\\D', '', 'g') = $2)
              AND ultimo_envio_em > $3::timestamptz
            ORDER BY ultimo_envio_em DESC
            LIMIT 1
            """,
            documento,
            telefone,
            limite,
        )
        if rows:
            raise HTTPException(status_code=429, detail="Aguarde 1 minuto antes de solicitar novo OTP")

    async def _expirar_otps_pendentes(self, documento: str, telefone: str) -> None:
        await self.db.execute_raw(
            """
            UPDATE otp_verificacoes
            SET status = $1,
                updated_at = NOW()
            WHERE status = $2
              AND (documento = $3 OR regexp_replace(telefone, '\\D', '', 'g') = $4)
            """,
            OTP_STATUS_EXPIRED,
            OTP_STATUS_PENDING,
            documento,
            telefone,
        )

    async def _registrar_log(
        self,
        cliente_id: Optional[int],
        acao: str,
        payload: Dict[str, Any],
        ip: Optional[str],
        user_agent: Optional[str],
    ) -> None:
        try:
            await self.db.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, ip, user_agent, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), $4, $5, NOW())
                """,
                int(cliente_id) if cliente_id else None,
                acao,
                json.dumps(payload),
                ip,
                user_agent,
            )
        except Exception:
            pass

    def _hash_codigo(self, otp_id: str, codigo: str) -> str:
        secret = (
            os.getenv("OTP_HASH_SECRET")
            or os.getenv("SECRET_KEY")
            or os.getenv("JWT_SECRET_KEY")
            or "dev-otp-secret"
        )
        message = f"{otp_id}:{codigo}".encode("utf-8")
        return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    def _serialize_cliente(self, cliente: Any) -> Dict[str, Any]:
        created_at = _row_get(cliente, "created_at", _row_get(cliente, "createdAt"))
        return {
            "id": int(_row_get(cliente, "id")),
            "nome_completo": _row_get(cliente, "nome_completo", _row_get(cliente, "nomeCompleto")),
            "documento": normalizar_documento(_row_get(cliente, "documento")),
            "telefone": _row_get(cliente, "telefone") or None,
            "email": _row_get(cliente, "email") or None,
            "status": _row_get(cliente, "status"),
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        }

    def _is_production(self) -> bool:
        return (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower() == "production"
