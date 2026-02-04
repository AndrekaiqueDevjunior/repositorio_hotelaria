from pydantic_settings import BaseSettings
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
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    
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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "allow"  # Permitir campos extras do ambiente
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
