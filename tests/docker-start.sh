#!/bin/bash
# Script para iniciar o sistema via Docker

echo "=========================================="
echo "Hotel Real Cabo Frio - Docker Setup"
echo "=========================================="
echo ""

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "ERRO: Docker não está rodando!"
    echo "Por favor, inicie o Docker Desktop e tente novamente."
    exit 1
fi

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "Criando arquivo .env a partir do .env.example..."
    cp .env.example .env
fi

# Criar diretórios necessários
echo "Criando diretórios necessários..."
mkdir -p logs/nginx
mkdir -p uploads
mkdir -p static

# Construir e iniciar containers
echo ""
echo "Construindo imagens Docker..."
docker-compose build

echo ""
echo "Iniciando containers..."
docker-compose up -d

echo ""
echo "Aguardando serviços iniciarem..."
sleep 10

# Verificar status
echo ""
echo "Status dos containers:"
docker-compose ps

echo ""
echo "=========================================="
echo "Sistema iniciado com sucesso!"
echo "=========================================="
echo ""
echo "Serviços disponíveis:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:80"
echo "  - Grafana: http://localhost:3001 (admin/admin123)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Celery Flower: http://localhost:5555"
echo ""
echo "Para ver os logs:"
echo "  docker-compose logs -f"
echo ""
echo "Para parar o sistema:"
echo "  docker-compose down"
echo ""

