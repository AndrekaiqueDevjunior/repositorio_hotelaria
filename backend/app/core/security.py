from fastapi import Header, HTTPException, Depends, Request, Cookie
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import os
import json
import secrets
from app.core.enums import PerfilUsuario
from app.core.config import settings

# JWT Implementation
try:
    from jose import JWTError, jwt
    from jose.exceptions import ExpiredSignatureError
    JWT_AVAILABLE = True
except ImportError:
    try:
        import jwt
        from jwt import PyJWTError as JWTError
        from jwt import ExpiredSignatureError
        JWT_AVAILABLE = True
    except ImportError:
        JWT_AVAILABLE = False
        jwt = None
        JWTError = Exception
        ExpiredSignatureError = Exception


class User(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    fotoUrl: Optional[str] = None


# Configurações de token
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 dias

# Configurações JWT
ISSUER = os.getenv("JWT_ISSUER", "hotel-real")
AUDIENCE = os.getenv("JWT_AUDIENCE", "hotel-real-api")


def hash_password(password: str) -> str:
    """
    Hash seguro de senha usando bcrypt
    
    Args:
        password: Senha em texto plano
    
    Returns:
        Hash bcrypt (60 caracteres)
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verificar senha contra hash
    
    Args:
        password: Senha em texto plano
        hashed: Hash bcrypt armazenado
    
    Returns:
        True se senha correta
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    """
    Criar access token JWT (curta duração - 1 hora)
    """
    if not JWT_AVAILABLE:
        return "fake-jwt-token"
    
    to_encode = data.copy()
    from app.utils.datetime_utils import now_utc
    now = now_utc()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": secrets.token_urlsafe(16),
        "exp": int(expire.timestamp()),
        "type": "access"
    })
    
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise ValueError("SECRET_KEY environment variable must be set in production")
        secret_key = "hotel-real-cabo-frio-secret-key"  # fallback apenas para desenvolvimento
    
    try:
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
        return encoded_jwt
    except Exception as e:
        print(f"[JWT] Erro ao criar access token: {e}")
        return "fake-jwt-token"


def create_refresh_token(data: dict) -> str:
    """
    Criar refresh token JWT (longa duração - 7 dias)
    """
    if not JWT_AVAILABLE:
        return "fake-jwt-token"
    
    to_encode = data.copy()
    from app.utils.datetime_utils import now_utc
    now = now_utc()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "jti": secrets.token_urlsafe(16),
        "exp": int(expire.timestamp()),
        "type": "refresh"
    })
    
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise ValueError("SECRET_KEY environment variable must be set in production")
        secret_key = "hotel-real-cabo-frio-secret-key"  # fallback apenas para desenvolvimento
    
    try:
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
        return encoded_jwt
    except Exception as e:
        print(f"[JWT] Erro ao criar refresh token: {e}")
        return "fake-jwt-token"


def verify_token(token: str, token_type: str = "access") -> dict:
    """
    Verificar e decodificar token JWT
    
    Args:
        token: Token JWT
        token_type: Tipo esperado (access ou refresh)
    
    Returns:
        Payload do token
    
    Raises:
        HTTPException: Se token inválido ou expirado
    """
    if not JWT_AVAILABLE:
        raise HTTPException(status_code=401, detail="JWT não disponível")
    
    try:
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("SECRET_KEY environment variable must be set in production")
            secret_key = "hotel-real-cabo-frio-secret-key"  # fallback apenas para desenvolvimento
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
            options={
                "require": ["exp", "iat", "nbf", "iss", "aud", "sub", "jti"]
            }
        )
        
        # Verificar tipo do token
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=401,
                detail=f"Token type mismatch. Expected {token_type}"
            )
        
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except JWTError as e:
        print(f"[JWT] Erro na verificação: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")


async def verify_token_not_blacklisted(token: str) -> bool:
    """
    Verificar se token não está na blacklist usando jti
    
    Args:
        token: Token JWT
    
    Returns:
        True se não está na blacklist
    
    Raises:
        HTTPException: Se token está revogado
    """
    try:
        # Primeiro, decodificar para obter o jti
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY", "hotel-real-cabo-frio-secret-key"),
            algorithms=["HS256"],
            options={"verify_signature": False}  # Só para pegar o jti
        )
        
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Token inválido: sem jti")
        
        from app.core.cache import cache
        is_blacklisted = await cache.get(f"blacklist:jti:{jti}")
        if is_blacklisted:
            raise HTTPException(status_code=401, detail="Token revogado")
        return True
    except HTTPException:
        raise
    except Exception:
        # Verificar se estamos em produção
        IS_PROD = os.getenv("ENVIRONMENT", "development").lower() == "production"
        if IS_PROD:
            raise HTTPException(status_code=503, detail="Serviço de autenticação indisponível")
        # Em desenvolvimento, permitir (fail-open)
        return True


async def get_current_user(
    request: Request,
    authorization: str = Header(None, alias="Authorization")
) -> User:
    """Obter usuário atual a partir do token JWT (header ou cookie)"""
    
    # Tentar obter token do header Authorization
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    # Se não encontrou no header, tentar no cookie
    if not token:
        token = request.cookies.get(settings.COOKIE_NAME)
    
    if not token:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    # Verificar se estamos em produção
    IS_PROD = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    # Se JWT não estiver disponível, falhar em produção
    if not JWT_AVAILABLE:
        if IS_PROD:
            raise HTTPException(status_code=503, detail="Serviço de autenticação indisponível")
        return User(id=1, nome="Dev Admin", email="dev@local", perfil=PerfilUsuario.ADMIN)
    
    # Se for fake token, falhar em produção
    if token == "fake-jwt-token":
        if IS_PROD:
            raise HTTPException(status_code=401, detail="Token inválido")
        return User(id=1, nome="Dev Admin", email="dev@local", perfil=PerfilUsuario.ADMIN)
    
    try:
        # Verificar e decodificar token
        payload = verify_token(token, token_type="access")
        
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        perfil = payload.get("perfil")
        
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Validar e normalizar perfil
        if perfil and not PerfilUsuario.is_valid(perfil):
            raise HTTPException(status_code=401, detail="Perfil inválido")
        
        # Buscar usuário no banco para validar
        from app.core.database import get_db
        db = get_db()
        funcionario = await db.funcionario.find_unique(where={"id": user_id})
        
        if not funcionario or funcionario.status != "ATIVO":
            raise HTTPException(status_code=401, detail="Usuário inválido ou inativo")
        
        return User(
            id=funcionario.id,
            nome=funcionario.nome,
            email=funcionario.email,
            perfil=PerfilUsuario.normalize(funcionario.perfil),
            fotoUrl=getattr(funcionario, "fotoUrl", None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH] Erro na validação do token: {e}")
        raise HTTPException(status_code=401, detail="Erro na autenticação")


def require_roles(*roles_allowed: str):
    async def checker(user: User = Depends(get_current_user)):
        if user.perfil not in roles_allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Acesso negado. Perfis permitidos: {', '.join(roles_allowed)}",
            )
        return user

    return checker
