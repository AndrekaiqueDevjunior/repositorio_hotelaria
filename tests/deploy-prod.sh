#!/bin/bash
# Script de deploy completo para produção

set -e

echo "🚀 Deploy Hotel Real Cabo Frio - Produção"
echo "=========================================="
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Erro: Execute este script na raiz do projeto"
    exit 1
fi

# Verificar se .env existe
if [ ! -f "backend/.env" ]; then
    echo "❌ Erro: backend/.env não encontrado"
    echo "   Copie: cp backend/env.production.example backend/.env"
    echo "   E configure as credenciais Cielo"
    exit 1
fi

# Verificar credenciais Cielo
echo "🔍 Verificando configuração Cielo..."
if grep -q "seu-merchant-id-aqui" backend/.env; then
    echo "⚠️  AVISO: Credenciais Cielo não configuradas!"
    echo "   Edite backend/.env com suas credenciais reais"
    read -p "Continuar mesmo assim? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

# Pull das últimas imagens
echo "📦 Baixando imagens Docker..."
docker-compose -f docker-compose.prod.yml pull

# Build das imagens
echo "🔨 Construindo imagens..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Parar containers antigos
echo "🛑 Parando containers antigos..."
docker-compose -f docker-compose.prod.yml down

# Aplicar migrações
echo "🗄️  Aplicando migrações do banco..."
docker-compose -f docker-compose.prod.yml run --rm api npx prisma migrate deploy

# Iniciar serviços
echo "🚀 Iniciando serviços..."
docker-compose -f docker-compose.prod.yml up -d

# Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 10

# Verificar saúde
echo "🏥 Verificando saúde dos serviços..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Health check API..."
curl -f http://localhost:8000/health || echo "⚠️  API ainda inicializando"

echo ""
echo "=========================================="
echo "✅ Deploy concluído!"
echo "=========================================="
echo ""
echo "📊 Verificar logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f api"
echo ""
echo "🌐 URLs:"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Health: http://localhost:8000/health"
echo ""
echo "🔍 Próximos passos:"
echo "   1. Configure DNS apontando para este servidor"
echo "   2. Configure SSL com certbot"
echo "   3. Faça deploy do frontend"
echo "   4. Teste pagamento com cartão real (valor baixo)"
echo ""


