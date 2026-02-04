# ============================================================
# Dockerfile - Backend FastAPI
# ============================================================

FROM python:3.12-slim

# Metadados
LABEL maintainer="Hotel Cabo Frio"
LABEL description="Backend FastAPI para Sistema de Gestão Hoteleira"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install prisma

# Copiar código da aplicação (incluindo schema.prisma)
COPY . .

# Gerar Prisma Client
RUN prisma generate && python -c "from prisma import Prisma; print('Prisma installed')"

# Criar diretórios necessários
RUN mkdir -p /app/.cache

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
