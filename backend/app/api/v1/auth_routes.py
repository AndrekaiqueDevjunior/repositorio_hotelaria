"""
Rotas de autenticação com refresh tokens
"""

from fastapi import APIRouter, HTTPException, Body, Request, Depends, Response, UploadFile, File
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from typing import Optional
from app.utils.datetime_utils import now_utc
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    get_current_user,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    DEV_FALLBACK_SECRET_KEY,
)
from app.core.enums import PerfilUsuario
from app.utils.hashing import verify_password
from app.core.database import get_db, get_db_connected
from app.core.cache import cache
from app.core.config import settings
import jwt
import os
import uuid
import hashlib

router = APIRouter()

INVALID_CREDENTIALS_MESSAGE = "E-mail, CPF ou senha inválidos"
COMMON_PASSWORDS = {
    "123456",
    "123456789",
    "1234567890",
    "admin",
    "password",
    "senha",
    "hotel123",
    "hotelreal",
    "hotelreal123",
    "qwerty",
}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _get_cookie_options(request: Request) -> tuple[Optional[str], bool, str]:
    cookie_domain = settings.COOKIE_DOMAIN
    cookie_secure = settings.COOKIE_SECURE
    cookie_samesite = settings.COOKIE_SAMESITE

    origin = request.headers.get("origin", "")
    host = request.headers.get("host", "")
    host_no_port = host.split(":")[0].strip().lower() if host else ""

    if host_no_port in ("localhost", "127.0.0.1") or (host_no_port and "." not in host_no_port):
        cookie_domain = None

    if "trycloudflare.com" in origin or "cloudflare" in origin:
        cookie_domain = None
        cookie_secure = True
        cookie_samesite = "none"
    elif "loca.lt" in origin or "loca.lt" in host:
        cookie_domain = None
        cookie_secure = True
        cookie_samesite = "none"
    elif "ngrok" in origin or "ngrok" in host:
        cookie_domain = None
        cookie_secure = True
        cookie_samesite = "none"

    if not cookie_domain or str(cookie_domain).strip() in ("localhost", ".localhost"):
        cookie_domain = None

    return cookie_domain, cookie_secure, cookie_samesite


def _hash_cache_part(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()[:24]


def _login_attempt_keys(email: str, ip: str) -> tuple[str, str]:
    email_hash = _hash_cache_part(email)
    ip_hash = _hash_cache_part(ip or "unknown")
    return f"login_attempts:account_ip:{email_hash}:{ip_hash}", f"login_attempts:ip:{ip_hash}"


def _get_access_token_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "", 1).strip()
    return request.cookies.get(settings.COOKIE_NAME)


async def _blacklist_access_token(token: Optional[str]) -> None:
    if not token:
        return

    try:
        secret_key = os.getenv("SECRET_KEY") or DEV_FALLBACK_SECRET_KEY
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        jti = payload.get("jti")
        exp = datetime.fromtimestamp(payload["exp"], timezone.utc)
        ttl = int((exp - now_utc()).total_seconds())

        if ttl > 0 and jti:
            await cache.set(f"blacklist:jti:{jti}", "1", ttl=ttl)
    except Exception as e:
        print(f"[AUTH] Erro ao adicionar token à blacklist: {e}")


def _validate_new_password(new_password: str, funcionario) -> None:
    normalized = new_password.strip().lower()

    if len(new_password) < 12:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 12 caracteres")

    if normalized in COMMON_PASSWORDS:
        raise HTTPException(status_code=400, detail="A nova senha é muito comum")

    email_prefix = (getattr(funcionario, "email", "") or "").split("@")[0].lower()
    nome_parts = [part for part in (getattr(funcionario, "nome", "") or "").lower().split() if len(part) >= 3]

    if email_prefix and email_prefix in normalized:
        raise HTTPException(status_code=400, detail="A nova senha não deve conter o e-mail do usuário")

    if any(part in normalized for part in nome_parts):
        raise HTTPException(status_code=400, detail="A nova senha não deve conter o nome do usuário")

    categories = [
        any(c.isupper() for c in new_password),
        any(c.islower() for c in new_password),
        any(c.isdigit() for c in new_password),
        any(c in '!@#$%&*()_+-=[]{}|;:,.<>?/' for c in new_password),
    ]

    long_passphrase = len(new_password) >= 20 and " " in new_password
    if sum(categories) < 3 and not long_passphrase:
        raise HTTPException(
            status_code=400,
            detail="A nova senha deve combinar pelo menos 3 tipos: maiúsculas, minúsculas, números ou símbolos",
        )


def _delete_auth_cookies(request: Request, response: Response) -> None:
    cookie_domain, _, _ = _get_cookie_options(request)
    refresh_cookie_name = f"{settings.COOKIE_NAME}_refresh"

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        domain=cookie_domain,
    )
    response.delete_cookie(
        key=refresh_cookie_name,
        path="/",
        domain=cookie_domain,
    )


async def check_login_attempts(email: str, ip: str):
    """Verificar tentativas de login falhadas"""
    
    account_ip_key, ip_key = _login_attempt_keys(email, ip)
    for key, limit in ((account_ip_key, 5), (ip_key, 25)):
        attempts = await cache.get(key)
        if not attempts or int(attempts) < limit:
            continue

        ttl = await cache.ttl(key)
        if ttl > 0:
            raise HTTPException(
                status_code=429,
                detail=f"Muitas tentativas de login. Tente novamente em {ttl} segundos"
            )
    
    return True


async def log_failed_login(email: str, ip: str):
    """Registrar tentativa falha"""
    
    account_ip_key, ip_key = _login_attempt_keys(email, ip)

    for key, threshold in ((account_ip_key, 5), (ip_key, 25)):
        attempts = await cache.incr(key)
        if attempts == 1:
            await cache.expire(key, 900)
        if attempts >= threshold:
            lock_seconds = min(900 * (2 ** max(0, attempts - threshold)), 3600)
            await cache.expire(key, lock_seconds)
            print(f"[AUTH] Bloqueio temporário ativado para chave {key}")


async def log_successful_login(user_id: int, ip: str, user_agent: str):
    """Registrar login bem-sucedido e limpar tentativas"""
    
    db = await get_db_connected()
    funcionario = await db.funcionario.find_unique(where={"id": user_id})
    
    # Limpar tentativas falhas
    account_ip_key, _ = _login_attempt_keys(funcionario.email, ip)
    await cache.delete(account_ip_key)
    
    # Registrar em auditoria (desativado - modelo não existe)
    # try:
    #     await db.auditoria.create(
    #         data={
    #             "usuarioId": user_id,
    #             "acao": "LOGIN",
    #             "descricao": f"Login bem-sucedido para {funcionario.email}",
    #             "ip": ip,
    #             "userAgent": user_agent,
    #             "dataHora": datetime.now()
    #         }
    #     )
    # except Exception as e:
    #     print(f"[AUTH] Erro ao registrar auditoria: {e}")


@router.post("/login")
async def login(credentials: LoginRequest, request: Request, response: Response):
    """
    Login com JWT em cookie HttpOnly
    
    O token é armazenado em cookie seguro e não retornado no body.
    Também fornece refresh_token para renovação.
    
    Returns:
        user: Dados do usuário autenticado
        message: Mensagem de sucesso
    """
    
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # Verificar tentativas de login
    await check_login_attempts(credentials.email, ip)
    
    db = await get_db_connected()
    
    # Buscar funcionário
    funcionario = await db.funcionario.find_unique(
        where={"email": credentials.email}
    )
    
    if not funcionario:
        await log_failed_login(credentials.email, ip)
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS_MESSAGE)

    # Verificar senha
    senha_valida = verify_password(credentials.password, funcionario.senha)

    if not senha_valida:
        await log_failed_login(credentials.email, ip)
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS_MESSAGE)
    
    # Verificar se conta está ativa
    if funcionario.status != "ATIVO":
        raise HTTPException(status_code=403, detail="Conta inativa")
    
    # Verificar se é primeiro acesso
    primeiro_acesso = getattr(funcionario, "primeiroAcesso", False)
    
    # Gerar tokens
    token_data = {
        "sub": str(funcionario.id),
        "email": funcionario.email,
        "perfil": PerfilUsuario.normalize(funcionario.perfil)
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Armazenar refresh token (para revogação)
    await cache.set(
        f"refresh_token:{funcionario.id}",
        refresh_token,
        ttl=REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    
    # Registrar login bem-sucedido
    await log_successful_login(funcionario.id, ip, user_agent)
    
    cookie_domain, cookie_secure, cookie_samesite = _get_cookie_options(request)

    refresh_cookie_name = f"{settings.COOKIE_NAME}_refresh"
    
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        max_age=settings.COOKIE_MAX_AGE,
        path="/",
        domain=cookie_domain,
        secure=cookie_secure,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=cookie_samesite,
    )
    
    response.set_cookie(
        key=refresh_cookie_name,
        value=refresh_token,
        max_age=settings.COOKIE_MAX_AGE,
        path="/",
        domain=cookie_domain,
        secure=cookie_secure,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=cookie_samesite,
    )
    
    return {
        "success": True,
        "message": "Login realizado com sucesso",
        "funcionario": {
            "id": funcionario.id,
            "nome": funcionario.nome,
            "email": funcionario.email,
            "perfil": PerfilUsuario.normalize(funcionario.perfil),
            "fotoUrl": getattr(funcionario, "fotoUrl", None),
            "primeiroAcesso": primeiro_acesso
        },
        "token_type": "cookie",
        "requirePasswordChange": primeiro_acesso
    }


@router.post("/change-password")
async def change_password(
    request: Request,
    response: Response,
    current_password: str = Body(...),
    new_password: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Alterar senha do usuário logado
    """
    
    db = get_db()
    
    # Buscar funcionário
    funcionario = await db.funcionario.find_unique(
        where={"id": current_user.id}
    )
    
    if not funcionario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verificar senha atual
    if not verify_password(current_password, funcionario.senha):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    
    _validate_new_password(new_password, funcionario)
    
    # Atualizar senha
    new_hash = hash_password(new_password)
    await db.funcionario.update(
        where={"id": current_user.id},
        data={
            "senha": new_hash,
            "primeiroAcesso": False
        }
    )

    await cache.delete(f"refresh_token:{current_user.id}")
    await _blacklist_access_token(_get_access_token_from_request(request))
    _delete_auth_cookies(request, response)
    
    return {
        "success": True,
        "message": "Senha alterada com sucesso. Faça login novamente."
    }


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    body: Optional[RefreshRequest] = None,
):
    """
    Renovar access token usando refresh token
    
    Args:
        refresh_token: Refresh token válido
    
    Returns:
        access_token: Novo access token
        token_type: Tipo do token (bearer)
        expires_in: Tempo de expiração em segundos
    """
    
    refresh_cookie_name = f"{settings.COOKIE_NAME}_refresh"
    refresh_token = request.cookies.get(refresh_cookie_name)
    if body and body.refresh_token:
        refresh_token = body.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token não fornecido")

    # Verificar refresh token
    try:
        payload = verify_token(refresh_token, token_type="refresh")
    except HTTPException:
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    
    user_id = int(payload["sub"])
    
    # Verificar se refresh token ainda é válido (não revogado)
    stored_token = await cache.get(f"refresh_token:{user_id}")
    if stored_token != refresh_token:
        await cache.delete(f"refresh_token:{user_id}")
        raise HTTPException(status_code=401, detail="Refresh token revogado")
    
    # Gerar novo access token
    token_data = {
        "sub": payload["sub"],
        "email": payload["email"],
        "perfil": payload["perfil"]
    }
    
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    await cache.set(
        f"refresh_token:{user_id}",
        new_refresh_token,
        ttl=REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    
    cookie_domain, cookie_secure, cookie_samesite = _get_cookie_options(request)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=new_access_token,
        max_age=settings.COOKIE_MAX_AGE,
        path="/",
        domain=cookie_domain,
        secure=cookie_secure,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=cookie_samesite,
    )
    response.set_cookie(
        key=refresh_cookie_name,
        value=new_refresh_token,
        max_age=settings.COOKIE_MAX_AGE,
        path="/",
        domain=cookie_domain,
        secure=cookie_secure,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=cookie_samesite,
    )

    return {
        "success": True,
        "token_type": "cookie",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout com revogação de refresh token e remoção de cookie
    
    Revoga o refresh token, adiciona o access token à blacklist e remove o cookie
    """
    
    user_id = current_user.id
    
    # Revogar refresh token
    await cache.delete(f"refresh_token:{user_id}")
    
    # Blacklist do access token atual (até expirar)
    await _blacklist_access_token(_get_access_token_from_request(request))
    
    # Registrar logout em auditoria (desativado - modelo não existe)
    # db = get_db()
    # try:
    #     ip = request.client.host if request.client else "unknown"
    #     await db.auditoria.create(
    #         data={
    #             "usuarioId": user_id,
    #             "acao": "LOGOUT",
    #             "descricao": f"Logout realizado por {user.email}",
    #             "ip": ip,
    #             "userAgent": request.headers.get("user-agent", "unknown"),
    #             "dataHora": datetime.now()
    #         }
    #     )
    # except Exception as e:
    #     print(f"[AUTH] Erro ao registrar auditoria de logout: {e}")
    
    _delete_auth_cookies(request, response)
    
    return {"success": True, "message": "Logout realizado com sucesso"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Obter informações do usuário atual
    
    Returns:
        Dados do usuário autenticado
    """
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "perfil": current_user.perfil,
        "fotoUrl": getattr(current_user, "fotoUrl", None)
    }


@router.post("/me/avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content_type = (file.content_type or "").lower()
    allowed = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    if content_type not in allowed:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado")

    data = await file.read()
    await file.close()

    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    max_bytes = 5 * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx 5MB)")

    os.makedirs("media/avatars", exist_ok=True)
    ext = allowed[content_type]
    filename = f"user_{current_user.id}_{uuid.uuid4().hex}{ext}"
    rel_path = f"avatars/{filename}"
    disk_path = os.path.join("media", rel_path)

    with open(disk_path, "wb") as f:
        f.write(data)

    db = await get_db_connected()
    await db.funcionario.update(
        where={"id": current_user.id},
        data={"fotoUrl": f"/media/{rel_path}"},
    )

    return {
        "success": True,
        "fotoUrl": f"/media/{rel_path}",
    }
