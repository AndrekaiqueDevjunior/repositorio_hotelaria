"""
Rotas de autenticação com refresh tokens
"""

from fastapi import APIRouter, HTTPException, Body, Request, Depends, Response, UploadFile, File
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from app.utils.datetime_utils import now_utc, cookie_expires
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    get_current_user,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from app.core.enums import PerfilUsuario
from app.utils.hashing import verify_password
from app.core.database import get_db, get_db_connected
from app.core.cache import cache
from app.core.config import settings
import jwt
import os
import uuid

router = APIRouter()


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


async def check_login_attempts(email: str, ip: str):
    """Verificar tentativas de login falhadas"""
    
    key = f"login_attempts:{email}:{ip}"
    attempts = await cache.get(key)
    
    if attempts and int(attempts) >= 5:
        # Verificar se ainda está bloqueado
        ttl = await cache.ttl(key)
        if ttl > 0:
            raise HTTPException(
                status_code=429,
                detail=f"Conta temporariamente bloqueada. Tente novamente em {ttl} segundos"
            )
    
    return True


async def log_failed_login(email: str, ip: str):
    """Registrar tentativa falha"""
    
    key = f"login_attempts:{email}:{ip}"
    
    # Incrementar contador
    attempts = await cache.incr(key)
    
    if attempts == 1:
        # Primeira tentativa, definir expiração de 15 minutos
        await cache.expire(key, 900)
    
    if attempts >= 5:
        # 5 falhas = bloquear por 15 minutos
        await cache.expire(key, 900)
        print(f"[AUTH] Bloqueio ativado para {email} de {ip}")


async def log_successful_login(user_id: int, ip: str, user_agent: str):
    """Registrar login bem-sucedido e limpar tentativas"""
    
    db = await get_db_connected()
    funcionario = await db.funcionario.find_unique(where={"id": user_id})
    
    # Limpar tentativas falhas
    key = f"login_attempts:{funcionario.email}:{ip}"
    await cache.delete(key)
    
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
        print(f"[AUTH DEBUG] Funcionário não encontrado: {credentials.email}")
        await log_failed_login(credentials.email, ip)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    print(f"[AUTH DEBUG] Funcionário encontrado: {funcionario.email}")
    print(f"[AUTH DEBUG] Hash no banco: {funcionario.senha[:20]}...")
    print(f"[AUTH DEBUG] Senha recebida (len): {len(credentials.password)}")
    
    # Verificar senha
    senha_valida = verify_password(credentials.password, funcionario.senha)
    print(f"[AUTH DEBUG] Resultado verify_password: {senha_valida}")
    
    if not senha_valida:
        await log_failed_login(credentials.email, ip)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Verificar se conta está ativa
    if funcionario.status != "ATIVO":
        raise HTTPException(status_code=403, detail="Conta inativa")
    
    # Verificar se é primeiro acesso
    primeiro_acesso = getattr(funcionario, 'primeiro_acesso', False)
    
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

    expires_at = cookie_expires(settings.COOKIE_MAX_AGE)
    
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
        "refresh_token": refresh_token,
        "token_type": "cookie",
        "requirePasswordChange": primeiro_acesso
    }


@router.post("/change-password")
async def change_password(
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
    
    # Validar nova senha (forte)
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 8 caracteres")
    
    has_upper = any(c.isupper() for c in new_password)
    has_lower = any(c.islower() for c in new_password)
    has_digit = any(c.isdigit() for c in new_password)
    has_special = any(c in '!@#$%&*()_+-=[]{}|;:,.<>?' for c in new_password)
    
    if not (has_upper and has_lower and has_digit and has_special):
        raise HTTPException(
            status_code=400, 
            detail="A nova senha deve conter: letras maiúsculas, minúsculas, números e símbolos"
        )
    
    # Atualizar senha
    new_hash = hash_password(new_password)
    await db.funcionario.update(
        where={"id": current_user.id},
        data={
            "senha": new_hash,
            "primeiroAcesso": False
        }
    )
    
    return {
        "success": True,
        "message": "Senha alterada com sucesso"
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
    refresh_token = body.refresh_token if body else request.cookies.get(refresh_cookie_name)
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
        raise HTTPException(status_code=401, detail="Refresh token revogado")
    
    # Gerar novo access token
    token_data = {
        "sub": payload["sub"],
        "email": payload["email"],
        "perfil": payload["perfil"]
    }
    
    new_access_token = create_access_token(token_data)
    
    cookie_domain, cookie_secure, cookie_samesite = _get_cookie_options(request)
    expires_at = cookie_expires(settings.COOKIE_MAX_AGE)
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

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
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
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        
        try:
            # Decodificar para obter jti e expiração
            secret_key = os.getenv("SECRET_KEY", "hotel-real-cabo-frio-secret-key")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_exp": False})
            jti = payload.get("jti")
            exp = datetime.fromtimestamp(payload["exp"])
            ttl = int((exp - now_utc()).total_seconds())
            
            if ttl > 0 and jti:
                await cache.set(f"blacklist:jti:{jti}", "1", ttl=ttl)
        except Exception as e:
            print(f"[AUTH] Erro ao adicionar token à blacklist: {e}")
    
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
