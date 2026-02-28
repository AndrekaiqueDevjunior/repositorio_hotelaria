#!/bin/bash

# ============================================================
# DEPLOY HOTEL CABO FRIO - VPS SETUP SCRIPT
# ============================================================

set -e

echo "🚀 Iniciando setup/deploy do Hotel Real Cabo Frio..."

# 1. Atualizar sistema
echo "📦 Atualizando sistema..."
apt update && apt upgrade -y

# 2. Instalar dependências
echo "🔧 Instalando dependências..."
apt install -y apt-transport-https ca-certificates curl software-properties-common git

# 3. Instalar Docker
echo "🐳 Instalando Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# 4. Instalar Docker Compose Plugin
echo "🔧 Instalando Docker Compose Plugin..."
apt install -y docker-compose-plugin

# 5. Instalar Nginx
echo "🌐 Instalando Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx

# 6. Instalar Certbot
echo "🔒 Instalando Certbot..."
apt install -y certbot python3-certbot-nginx

# 7. Criar diretório do projeto
echo "📁 Criando diretório do projeto..."
mkdir -p /opt/hotel
cd /opt/hotel

# 8. Obter projeto
echo "⚠️  ATENÇÃO: Faça upload dos arquivos do projeto para /opt/hotel"
echo "   Use scp/rsync ou git clone conforme seu fluxo"

# 9. Verificar instalações
echo "✅ Verificando instalações..."
docker --version
docker compose version
nginx -v

echo "🎉 Setup do ambiente concluído!"
echo "📝 Próximos passos sugeridos:"
echo "   1. Faça upload do projeto para /opt/hotel"
echo "   2. Configure .env.production"
echo "   3. Valide o compose: docker compose -f docker-compose.production.yml --env-file .env.production config"
echo "   4. Suba produção: docker compose -f docker-compose.production.yml --env-file .env.production up -d --build"
