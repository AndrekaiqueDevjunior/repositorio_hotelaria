from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import psycopg2

# Ajustar DATABASE_URL se estiver usando Prisma Accelerate
database_url = settings.DATABASE_URL

# Se estiver usando Prisma Accelerate, precisamos ajustar a URL
if database_url.startswith("prisma+"):
    # Remove o prefixo 'prisma+' para SQLAlchemy
    database_url = database_url.replace("prisma+", "", 1)
    # Adiciona parâmetros SSL se necessário
    if "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"

# Engine será criado sob demanda para evitar erros de importação
engine = None
SessionLocal = None

def get_engine():
    global engine, SessionLocal
    if engine is None:
        engine = create_engine(
            database_url,
            echo=settings.DB_ECHO,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_session():
    if SessionLocal is None:
        get_engine()
    return SessionLocal()

Base = declarative_base()

# Metadata para criação de tabelas
metadata = Base.metadata
