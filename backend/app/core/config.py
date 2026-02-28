import os
from functools import lru_cache
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback para pydantic 1.x
    from pydantic import BaseSettings
    class SettingsConfigDict:
        def __init__(self, **kwargs):
            pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        case_sensitive=True
    )
    
    # App Basic Settings
    PROJECT_NAME: str = "Hotel Real Cabo Frio"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DESCRIPTION: str = "Sistema de Gestão Hoteleira - Arquitetura Modular"
    
    # CRÍTICO: DATABASE_URL deve estar aqui para ser carregada do .env
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Prisma / DB
    PRISMA_LOG_QUERIES: bool = True

    # Cielo
    CIELO_MERCHANT_ID: str = os.getenv("CIELO_MERCHANT_ID", "")
    CIELO_MERCHANT_KEY: str = os.getenv("CIELO_MERCHANT_KEY", "")
    CIELO_SANDBOX_URL: str = os.getenv("CIELO_SANDBOX_URL", "https://apisandbox.cieloecommerce.cielo.com.br/")
    CIELO_API_URL: str = os.getenv("CIELO_API_URL", "https://api.cieloecommerce.cielo.com.br/")
    CIELO_MODE: str = os.getenv("CIELO_MODE", "sandbox")

    # Admin
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # Cookie Configuration
    COOKIE_NAME: str = os.getenv("COOKIE_NAME", "hotel_auth_token")
    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", ".localhost")
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "False").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")
    COOKIE_HTTPONLY: bool = os.getenv("COOKIE_HTTPONLY", "True").lower() == "true"
    COOKIE_MAX_AGE: int = int(os.getenv("COOKIE_MAX_AGE", 604800))
    
    # CORS
    ALLOWED_HOSTS: list = ["*"]
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
