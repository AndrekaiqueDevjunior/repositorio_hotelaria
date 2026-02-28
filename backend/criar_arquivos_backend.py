# Salve como: criar_arquivos_backend.py e execute com: python criar_arquivos_backend.py

import os
from pathlib import Path

def criar_arquivos_backend():
    base_dir = Path.cwd()
    
    arquivos = {
        # DB Files
        "app/db/__init__.py": "",
        
        "app/db/base.py": """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

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

engine = create_engine(
    database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Metadata para criação de tabelas
metadata = Base.metadata
""",

        "app/db/session.py": """from sqlalchemy.orm import Session
from app.db.base import SessionLocal

def get_db() -> Session:
    \"\"\"Dependency to get database session\"\"\"
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",

        # Docker Compose (na raiz do projeto)
        "../docker-compose.yml": """version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: hotel_redis
    ports:
      - "6379:6379"
    networks:
      - hotel_network

  # PostgreSQL local (opcional - se não usar Prisma Accelerate)
  # db:
  #   image: postgres:15-alpine
  #   container_name: hotel_db
  #   environment:
  #     POSTGRES_USER: postgres
  #     POSTGRES_PASSWORD: postgres
  #     POSTGRES_DB: hotel_cabo_frio
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   networks:
  #     - hotel_network

volumes:
  postgres_data:

networks:
  hotel_network:
    driver: bridge
""",

        "../.gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Next.js
.next/
out/
node_modules/

# Testing
.coverage
htmlcov/
.pytest_cache/

# Celery
celerybeat-schedule
celerybeat.pid

# Docker
docker-compose.override.yml
"""
    }
    
    for filepath, content in arquivos.items():
        full_path = base_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Criado: {filepath}")
    
    print("\n✨ Arquivos criados com sucesso!")

if __name__ == "__main__":
    criar_arquivos_backend()