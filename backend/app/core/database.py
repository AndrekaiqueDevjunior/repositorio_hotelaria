import asyncio
import os
import hashlib
from datetime import timedelta
from typing import Any, Optional
from prisma import Prisma
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from app.utils.hashing import hash_password


DEFAULT_PRISMA_CONNECTION_LIMIT = 5
DEFAULT_PRISMA_POOL_TIMEOUT_SECONDS = 10
DEFAULT_PRISMA_CONNECT_TIMEOUT_SECONDS = 5
DEFAULT_PRISMA_DISCONNECT_TIMEOUT_SECONDS = 5
DEFAULT_CELERY_PRISMA_CONNECTION_LIMIT = 1
_db_connect_lock = asyncio.Lock()


def _get_int_env(name: str, default: int, minimum: int = 1) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError:
        print(f"[DATABASE] {name} invalido; usando {default}.")
        return default

    if value < minimum:
        print(f"[DATABASE] {name} deve ser >= {minimum}; usando {default}.")
        return default

    return value


def _positive_int(value: str) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 1 else None


def configure_prisma_url(
    url: str,
    application_name: Optional[str] = None,
    connection_limit: Optional[int] = None,
) -> str:
    """Aplica limites seguros ao pool do query engine sem alterar DATABASE_URL."""
    if not url:
        return url

    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"postgres", "postgresql"}:
        # URLs prisma:// (Accelerate/Data Platform) possuem pooling proprio.
        return url

    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    pool_settings = {
        "connection_limit": _get_int_env(
            "PRISMA_CONNECTION_LIMIT",
            DEFAULT_PRISMA_CONNECTION_LIMIT,
        ),
        "pool_timeout": _get_int_env(
            "PRISMA_POOL_TIMEOUT_SECONDS",
            DEFAULT_PRISMA_POOL_TIMEOUT_SECONDS,
        ),
        "connect_timeout": _get_int_env(
            "PRISMA_CONNECT_TIMEOUT_SECONDS",
            DEFAULT_PRISMA_CONNECT_TIMEOUT_SECONDS,
        ),
    }
    if connection_limit is not None:
        pool_settings["connection_limit"] = max(1, connection_limit)

    changed = False
    for key, maximum in pool_settings.items():
        values = [
            value
            for existing_key, value in query_params
            if existing_key.lower() == key
        ]
        existing = _positive_int(values[0]) if len(values) == 1 else None

        # A URL pode pedir um limite menor, mas nunca contornar o teto seguro
        # definido pelo processo (Compose/env ou os defaults acima).
        if existing is not None and existing <= maximum:
            continue

        query_params = [
            (existing_key, value)
            for existing_key, value in query_params
            if existing_key.lower() != key
        ]
        query_params.append((key, str(maximum)))
        changed = True

    resolved_application_name = application_name or os.getenv("PRISMA_APPLICATION_NAME")
    if resolved_application_name:
        current_names = [
            value
            for key, value in query_params
            if key.lower() == "application_name"
        ]
        if current_names != [resolved_application_name]:
            query_params = [
                (key, value)
                for key, value in query_params
                if key.lower() != "application_name"
            ]
            query_params.append(("application_name", resolved_application_name))
            changed = True

    if not changed:
        return url

    return urlunsplit(parsed._replace(query=urlencode(query_params)))

def mask_database_url(url: str) -> str:
    """Mascara credenciais da URL do banco para log seguro."""
    if not url:
        return "NOT_SET"
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname or "unknown-host"
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        port = f":{parsed.port}" if parsed.port else ""
        username = f"{parsed.username}:****@" if parsed.username else ""

        # Query params podem conter api_key (Prisma Accelerate) e nunca entram
        # no log. Os parametros de pool tambem nao sao necessarios no startup.
        return f"{parsed.scheme}://{username}{hostname}{port}{parsed.path}"
    except (TypeError, ValueError):
        return "INVALID_URL"

def get_database_url() -> str:
    """
    CRÍTICO: Obter DATABASE_URL com prioridade correta:
    1. Variável de ambiente (Docker)
    2. Arquivo .env (desenvolvimento local)
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Tentar carregar do .env se não estiver nas variáveis de ambiente
        try:
            from dotenv import load_dotenv
            load_dotenv(".env", override=True)
            database_url = os.getenv("DATABASE_URL")
            print("[DATABASE] Carregado DATABASE_URL do arquivo .env")
        except ImportError:
            print("[DATABASE] python-dotenv não disponível")
        except Exception as e:
            print(f"[DATABASE] Erro ao carregar .env: {e}")
    
    return configure_prisma_url(database_url) if database_url else database_url


class ManagedPrismaClient(Prisma):
    """Compatibilidade para encerrar o engine 0.11 com prazo finito."""

    __slots__ = ("_engine_close_timeout", "_created_engines")

    def __init__(self, *, engine_close_timeout: timedelta, **kwargs: Any) -> None:
        self._engine_close_timeout = engine_close_timeout
        # Rastreia cada engine criado para permitir kill garantido no
        # disconnect (ver _kill_leftover_engine_processes).
        self._created_engines = []
        super().__init__(**kwargs)

    def _create_engine(self, *args: Any, **kwargs: Any) -> Any:
        engine = super()._create_engine(*args, **kwargs)
        self._created_engines.append(engine)
        original_close = engine.close

        def close_with_default_timeout(*, timeout=None):
            return original_close(
                timeout=timeout or self._engine_close_timeout
            )

        # prisma-client-py 0.11 chama close() sem timeout se o spawn falha.
        engine.close = close_with_default_timeout
        return engine


def create_prisma_client(
    database_url: Optional[str] = None,
    *,
    connection_limit: Optional[int] = None,
    application_name: Optional[str] = None,
) -> Prisma:
    """Cria clientes Prisma somente pelo factory central e com pool limitado."""
    base_url = database_url if database_url is not None else get_database_url()
    resolved_url = (
        configure_prisma_url(
            base_url,
            application_name=application_name,
            connection_limit=connection_limit,
        )
        if base_url
        else base_url
    )
    kwargs = {"datasource": {"url": resolved_url}} if resolved_url else {}
    connect_timeout_seconds = _get_int_env(
        "PRISMA_CONNECT_TIMEOUT_SECONDS",
        DEFAULT_PRISMA_CONNECT_TIMEOUT_SECONDS,
    )
    client = ManagedPrismaClient(
        **kwargs,
        connect_timeout=timedelta(seconds=connect_timeout_seconds),
        engine_close_timeout=timedelta(seconds=connect_timeout_seconds),
    )
    return client


def create_celery_prisma_client() -> Prisma:
    """Cria o cliente das tasks com teto proprio, inclusive fora do Compose."""
    connection_limit = _get_int_env(
        "CELERY_PRISMA_CONNECTION_LIMIT",
        DEFAULT_CELERY_PRISMA_CONNECTION_LIMIT,
    )
    application_name = os.getenv("PRISMA_APPLICATION_NAME") or "hotel_celery"
    database_url = os.getenv("DATABASE_URL") or get_database_url()
    return create_prisma_client(
        database_url,
        connection_limit=connection_limit,
        application_name=application_name,
    )


def _kill_leftover_engine_processes(client: Any) -> None:
    """Ultima linha de defesa contra engines orfaos.

    Observado em producao (2026-07-16): o worker Celery acumulou ~196
    subprocessos query-engine vivos mesmo com disconnect() retornando sem
    erro apos cada task — cada engine segura connection_limit conexoes e o
    Postgres saturou em max_connections=200 ("too many clients already").
    SIGKILL nao pode ser ignorado, entao aqui o encerramento e garantido.
    """
    engines = getattr(client, "_created_engines", None) or []
    for engine in engines:
        process = getattr(engine, "process", None)
        if process is None:
            continue
        try:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        except Exception:
            print(f"[DATABASE] Falha ao matar query engine remanescente: {process}")
    if hasattr(engines, "clear"):
        engines.clear()


async def disconnect_prisma_client(client: Prisma) -> None:
    """Encerra o query engine sem bloquear indefinidamente o processo chamador."""
    timeout_seconds = _get_int_env(
        "PRISMA_DISCONNECT_TIMEOUT_SECONDS",
        DEFAULT_PRISMA_DISCONNECT_TIMEOUT_SECONDS,
    )
    try:
        await asyncio.wait_for(
            client.disconnect(timeout=timedelta(seconds=timeout_seconds)),
            timeout=timeout_seconds + min(1, timeout_seconds),
        )
    finally:
        _kill_leftover_engine_processes(client)

# Obter DATABASE_URL com fallback
database_url = get_database_url()

# Log seguro da DATABASE_URL no startup
print(f"[DATABASE] URL carregada: {mask_database_url(database_url)}")

if database_url:
    # Verificar se é Prisma remoto
    if "db.prisma.io" in database_url:
        print("[DATABASE] [OK] Usando Prisma Data Platform remoto")
    elif any(host in database_url for host in ["localhost", "127.0.0.1", "postgres:5432"]):
        print("[DATABASE] [PROBLEMA] Usando banco local!")
    else:
        print("[DATABASE] [AVISO] Host não reconhecido")
    
    # CRÍTICO: Sempre passar a URL explicitamente para o Prisma Client
    db = create_prisma_client(database_url)
else:
    print("[DATABASE] [ERRO] DATABASE_URL não definida!")
    # Fallback sem URL (vai usar schema.prisma default)
    db = create_prisma_client(database_url)


async def connect_db() -> None:
    await db.connect()
    print("[Prisma] Conectado ao banco.")


async def disconnect_db() -> None:
    await disconnect_prisma_client(db)
    print("[Prisma] Desconectado do banco.")


async def create_admin_if_not_exists() -> None:
    """Cria usuario admin se nao existir"""
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@hotelreal.com.br")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not admin_password:
            print("[DB] ADMIN_PASSWORD não definido. Admin não será criado automaticamente.")
            return
        
        # Verificar se admin existe
        existing = await db.funcionario.find_unique(
            where={"email": admin_email}
        )
        
        if not existing:
            # Criar admin
            admin = await db.funcionario.create(
                data={
                    "nome": "Administrador",
                    "email": admin_email,
                    "senha": hash_password(admin_password),
                    "perfil": "ADMIN",
                    "status": "ATIVO"
                }
            )
            print(f"[DB] Usuario admin criado: {admin_email}")
        else:
            print(f"[DB] Usuario admin ja existe: {admin_email}")
            
    except Exception as e:
        print(f"[DB] Erro ao criar admin: {e}")


async def init_db() -> None:
    """Initialize database connection and create admin"""
    await connect_db()
    await create_admin_if_not_exists()


def get_db() -> Prisma:
    """Get Prisma database client instance"""
    return db


async def get_db_connected() -> Prisma:
    """Get Prisma database client with established connection"""
    if not db.is_connected():
        async with _db_connect_lock:
            if not db.is_connected():
                await db.connect()
    return db
