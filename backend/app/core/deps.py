from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prisma import Prisma
from jose import jwt
from datetime import datetime, timedelta
from enum import Enum

# Prisma client instance
db = Prisma()

class PerfilUsuario(str, Enum):
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"
    RECEPCAO = "RECEPCAO"

class Usuario:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.nome = kwargs.get('nome')
        self.email = kwargs.get('email')
        self.perfil = kwargs.get('perfil')
        self.status = kwargs.get('status')
        self.senha = kwargs.get('senha')

security = HTTPBearer(auto_error=False)

# JWT Secret (in production, use environment variable)
JWT_SECRET = "hotel-real-cabo-frio-secret-key"
JWT_ALGORITHM = "HS256"


def decode_token(token: str) -> Optional[int]:
    """Decode JWT token and return user ID"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return int(user_id)
        return None
    except jwt.JWTError:
        return None


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    if expires_delta:
        from app.utils.datetime_utils import now_utc
        expire = now_utc() + expires_delta
    else:
        from app.utils.datetime_utils import now_utc
        expire = now_utc() + timedelta(hours=24)
    
    to_encode = {"exp": expire, "sub": str(user_id)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Usuario:
    # Try to get token from cookie first
    token = request.cookies.get("hotel_session")
    
    # If not in cookie, try Bearer token
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Connect to database if not already connected
    try:
        await db.connect()
    except:
        pass  # Already connected
    
    user = await db.funcionario.find_unique(
        where={"id": user_id}
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return Usuario(
        id=user.id,
        nome=user.nome,
        email=user.email,
        perfil=user.perfil,
        status=user.status,
        senha=user.senha
    )


def require_roles(*allowed_roles: PerfilUsuario):
    def role_checker(current_user: Usuario = Depends(get_current_user)):
        if current_user.perfil not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


async def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.status != "ATIVO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
