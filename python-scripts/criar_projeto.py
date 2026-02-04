import os
import json
from pathlib import Path

def criar_estrutura_projeto():
    """
    Script para criar toda a estrutura do projeto Hotel Real Cabo Frio
    """
    
    base_dir = Path.cwd()
    
    # Estrutura de arquivos e conteúdo
    arquivos = {
        # ============= BACKEND =============
        "backend/.env.example": """# Application
APP_NAME="Hotel Real Cabo Frio"
APP_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/hotel_cabo_frio
DB_ECHO=False

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Cookie
COOKIE_NAME=hotel_session
COOKIE_DOMAIN=localhost
COOKIE_SECURE=False
COOKIE_SAMESITE=lax

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Cielo E-commerce API 3.0
CIELO_MERCHANT_ID=your-merchant-id
CIELO_MERCHANT_KEY=your-merchant-key
CIELO_API_URL=https://api.cieloecommerce.cielo.com.br/
CIELO_SANDBOX_URL=https://apisandbox.cieloecommerce.cielo.com.br/
CIELO_MODE=sandbox
CIELO_TIMEOUT_MS=8000

# Antifraude
ANTIFRAUDE_RISK_THRESHOLD_AUTO=30
ANTIFRAUDE_RISK_THRESHOLD_REJECT=70

# Admin
ADMIN_EMAIL=admin@hotelreal.com.br
ADMIN_PASSWORD=ChangeMe123!
""",

        "backend/requirements.txt": """# FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Pydantic
pydantic==2.5.0
pydantic-settings==2.1.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.1

# Redis
redis==5.0.1
hiredis==2.2.3

# Celery
celery==5.3.4

# HTTP Requests
httpx==0.25.2
requests==2.31.0

# Utilities
python-dotenv==1.0.0
email-validator==2.1.0
""",

        "backend/app/__init__.py": "",
        
        "backend/app/config.py": """from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Hotel Real Cabo Frio"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Redis
    REDIS_URL: str
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # Cookie
    COOKIE_NAME: str = "hotel_session"
    COOKIE_DOMAIN: str = "localhost"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Cielo
    CIELO_MERCHANT_ID: str
    CIELO_MERCHANT_KEY: str
    CIELO_API_URL: str = "https://api.cieloecommerce.cielo.com.br/"
    CIELO_SANDBOX_URL: str = "https://apisandbox.cieloecommerce.cielo.com.br/"
    CIELO_MODE: str = "sandbox"
    CIELO_TIMEOUT_MS: int = 8000
    
    @property
    def cielo_base_url(self) -> str:
        return self.CIELO_SANDBOX_URL if self.CIELO_MODE == "sandbox" else self.CIELO_API_URL
    
    # Antifraude
    ANTIFRAUDE_RISK_THRESHOLD_AUTO: int = 30
    ANTIFRAUDE_RISK_THRESHOLD_REJECT: int = 70
    
    # Admin
    ADMIN_EMAIL: str = "admin@hotelreal.com.br"
    ADMIN_PASSWORD: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
""",

        "backend/app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, clientes, reservas, pontos, antifraude, financeiro, auditoria, admin
from app.db.init_db import init_db

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(clientes.router, prefix=f"{settings.API_V1_PREFIX}/clientes", tags=["clientes"])
app.include_router(reservas.router, prefix=f"{settings.API_V1_PREFIX}/reservas", tags=["reservas"])
app.include_router(pontos.router, prefix=f"{settings.API_V1_PREFIX}/pontos", tags=["pontos"])
app.include_router(antifraude.router, prefix=f"{settings.API_V1_PREFIX}/antifraude", tags=["antifraude"])
app.include_router(financeiro.router, prefix=f"{settings.API_V1_PREFIX}/financeiro", tags=["financeiro"])
app.include_router(auditoria.router, prefix=f"{settings.API_V1_PREFIX}/auditoria", tags=["auditoria"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["admin"])

@app.on_event("startup")
async def startup_event():
    # Initialize database with default data
    init_db()

@app.get("/")
async def root():
    return {
        "message": f"Bem-vindo ao {settings.APP_NAME}",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
""",

        "backend/app/core/__init__.py": "",
        
        "backend/app/core/enums.py": """from enum import Enum


class PerfilUsuario(str, Enum):
    RECEPCIONISTA = "RECEPCIONISTA"
    GERENTE = "GERENTE"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"
    HOSPEDE = "HOSPEDE"


class StatusUsuario(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"


class TipoDocumento(str, Enum):
    RG = "RG"
    CPF = "CPF"
    CNPJ = "CNPJ"
    CNH = "CNH"
    PASSAPORTE = "PASSAPORTE"
    OUTROS = "OUTROS"


class StatusCliente(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"


class StatusReserva(str, Enum):
    PENDENTE = "PENDENTE"
    HOSPEDADO = "HOSPEDADO"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELADO = "CANCELADO"


class OrigemReserva(str, Enum):
    TELEFONE = "TELEFONE"
    WHATSAPP = "WHATSAPP"
    SITE = "SITE"
    BALCAO = "BALCAO"
    OUTRO = "OUTRO"


class StatusQuarto(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    MANUTENCAO = "MANUTENCAO"


class MetodoPagamento(str, Enum):
    DINHEIRO = "DINHEIRO"
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"
    PIX = "PIX"
    TRANSFERENCIA = "TRANSFERENCIA"
    CIELO_CARTAO = "CIELO_CARTAO"
    OUTRO = "OUTRO"


class StatusPagamento(str, Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADO = "CONFIRMADO"
    NEGADO = "NEGADO"
    ESTORNADO = "ESTORNADO"


class TipoTransacaoPontos(str, Enum):
    GANHO = "GANHO"
    RESGATE = "RESGATE"
    AJUSTE_MANUAL = "AJUSTE_MANUAL"


class StatusAntifraude(str, Enum):
    PENDENTE = "PENDENTE"
    AUTO_APROVADO = "AUTO_APROVADO"
    RECUSADO = "RECUSADO"
    DUPLICADO = "DUPLICADO"
    MANUAL_APROVADO = "MANUAL_APROVADO"
    MANUAL_RECUSADO = "MANUAL_RECUSADO"


class TipoItemCobranca(str, Enum):
    CONSUMO = "CONSUMO"
    TAXA = "TAXA"
    OUTRO = "OUTRO"


class TipoComprovante(str, Enum):
    PIX = "PIX"
    DEPOSITO = "DEPOSITO"
    TERCEIRO = "TERCEIRO"
    OUTRO = "OUTRO"
""",

        "backend/app/core/security.py": """from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
""",

        "backend/app/core/deps.py": """from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from app.models.usuario import Usuario
from app.core.enums import PerfilUsuario

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
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
    
    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


def require_roles(*allowed_roles: PerfilUsuario):
    def role_checker(current_user: Usuario = Depends(get_current_user)):
        if current_user.perfil not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.status != "ATIVO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
""",

        # Continua com mais arquivos...
    }
    
    # Criar estrutura
    print("🚀 Criando estrutura do projeto Hotel Real Cabo Frio...")
    
    for filepath, content in arquivos.items():
        full_path = base_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Criado: {filepath}")
    
    print("\n✨ Projeto criado com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. cd backend && pip install -r requirements.txt")
    print("2. Copie .env.example para .env e configure")
    print("3. docker-compose up -d (para subir PostgreSQL e Redis)")
    print("4. alembic upgrade head (para criar as tabelas)")
    print("5. uvicorn app.main:app --reload")

if __name__ == "__main__":
    criar_estrutura_projeto()