import os
import hashlib
from prisma import Prisma
from urllib.parse import urlparse
from app.utils.hashing import hash_password

def mask_database_url(url: str) -> str:
    """Mascara credenciais da URL do banco para log seguro."""
    if not url:
        return "NOT_SET"
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked_netloc = f"{parsed.username}:****@{parsed.hostname}:{parsed.port}"
            return f"{parsed.scheme}://{masked_netloc}{parsed.path}"
        return url
    except:
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
    
    return database_url

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
    db = Prisma(datasource={"url": database_url})
else:
    print("[DATABASE] [ERRO] DATABASE_URL não definida!")
    # Fallback sem URL (vai usar schema.prisma default)
    db = Prisma()


async def connect_db() -> None:
    await db.connect()
    print("[Prisma] Conectado ao banco.")


async def disconnect_db() -> None:
    await db.disconnect()
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
        await db.connect()
    return db