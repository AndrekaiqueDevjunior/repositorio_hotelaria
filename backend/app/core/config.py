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
    DESCRIPTION: str = "Sistema de GestÃ£o Hoteleira - Arquitetura Modular"
    
    # CRÃTICO: DATABASE_URL deve estar aqui para ser carregada do .env
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Prisma / DB
    PRISMA_LOG_QUERIES: bool = True

    # Cielo
    CIELO_MERCHANT_ID: str = os.getenv("CIELO_MERCHANT_ID", "")
    CIELO_MERCHANT_KEY: str = os.getenv("CIELO_MERCHANT_KEY", "")
    CIELO_SANDBOX_URL: str = os.getenv("CIELO_SANDBOX_URL", "https://apisandbox.cieloecommerce.cielo.com.br/")
    CIELO_API_URL: str = os.getenv("CIELO_API_URL", "https://api.cieloecommerce.cielo.com.br/")
    CIELO_MODE: str = os.getenv("CIELO_MODE", "sandbox")

    # TEF (CliSiTef)
    TEF_AGENTE_URL: str = os.getenv("TEF_AGENTE_URL", "http://localhost:9999")
    TEF_AGENTE_MODE: str = os.getenv("TEF_AGENTE_MODE", "mock")
    TEF_AGENTE_VERIFY_SSL: bool = os.getenv("TEF_AGENTE_VERIFY_SSL", "true").lower() == "true"
    # Timeout de requisiÃ§Ã£o ao agente (segundos)
    TEF_TIMEOUT: int = int(os.getenv("TEF_TIMEOUT", "60"))
    # Timeout de inatividade de sessÃ£o TEF (segundos)
    TEF_SESSION_TIMEOUT: int = int(os.getenv("TEF_SESSION_TIMEOUT", "60"))
    TEF_TIMEZONE: str = os.getenv("TEF_TIMEZONE", "America/Sao_Paulo")
    # ParÃ¢metros de conexÃ£o/identificaÃ§Ã£o do terminal
    TEF_SITEF_IP: str = os.getenv("TEF_SITEF_IP", "")
    TEF_STORE_ID: str = os.getenv("TEF_STORE_ID", "")
    TEF_TERMINAL_ID: str = os.getenv("TEF_TERMINAL_ID", "")
    TEF_CASHIER_OPERATOR: str = os.getenv("TEF_CASHIER_OPERATOR", "")
    # ParÃ¢metros de sessÃ£o/transaÃ§Ã£o enviados ao agente
    TEF_SESSION_PARAMETERS: str = os.getenv("TEF_SESSION_PARAMETERS", "")
    TEF_TRN_INIT_PARAMETERS: str = os.getenv(
        "TEF_TRN_INIT_PARAMETERS",
        "",
    )
    TEF_TRN_PARAMETERS: str = os.getenv("TEF_TRN_PARAMETERS", "")
    # Envio de CNPJ via ParmsClient (parametrosAdicionais)
    TEF_PARMSCLIENT_PREFIX: str = os.getenv("TEF_PARMSCLIENT_PREFIX", "ParmsClient=>")
    TEF_CNPJ_ESTAB: str = os.getenv("TEF_CNPJ_ESTAB", "")
    TEF_CNPJ_AUTOMACAO: str = os.getenv("TEF_CNPJ_AUTOMACAO", "")
    TEF_PARAMETROS_ADICIONAIS: str = os.getenv("TEF_PARAMETROS_ADICIONAIS", "")
    # Senha de supervisor para validaÃ§Ã£o do TipoCampo 500
    TEF_SUPERVISOR_PASSWORD: str = os.getenv("TEF_SUPERVISOR_PASSWORD", os.getenv("ADMIN_PASSWORD", "admin123"))
    TEF_AUTO_RESOLVE_PENDING: bool = os.getenv("TEF_AUTO_RESOLVE_PENDING", "false").lower() == "true"
    TEF_AUTO_RESOLVE_PENDING_ACTION: str = os.getenv("TEF_AUTO_RESOLVE_PENDING_ACTION", "confirm").strip().lower()

    @property
    def TEF_AUTO_RESOLVE_PENDING_CONFIRM(self) -> bool:
        return self.TEF_AUTO_RESOLVE_PENDING_ACTION not in {"undo", "desfazer", "0", "false", "cancel", "cancelar"}

    SMS_TWILIO_ACCOUNT_SID: str = os.getenv("SMS_TWILIO_ACCOUNT_SID", "")
    SMS_TWILIO_AUTH_TOKEN: str = os.getenv("SMS_TWILIO_AUTH_TOKEN", "")
    SMS_TWILIO_FROM_NUMBER: str = os.getenv("SMS_TWILIO_FROM_NUMBER", "")

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
