#!/bin/bash
# Script para diagnosticar e corrigir Bad Gateway

echo "=========================================="
echo "  Diagnóstico Bad Gateway - Frontend"
echo "=========================================="
echo ""

# 1. Verificar status dos containers
echo "[1/6] Verificando status dos containers..."
docker ps -a | grep -E "frontend|nginx"
echo ""

# 2. Verificar logs do frontend
echo "[2/6] Verificando logs do frontend (últimas 20 linhas)..."
docker logs --tail 20 hotel_frontend_prod
echo ""

# 3. Verificar se o frontend está respondendo internamente
echo "[3/6] Testando conexão interna do frontend..."
docker exec hotel_frontend_prod wget -O- http://localhost:3000 2>&1 | head -n 5
echo ""

# 4. Verificar logs do nginx
echo "[4/6] Verificando logs do nginx (últimas 20 linhas)..."
docker logs --tail 20 hotel_nginx_prod
echo ""

# 5. Verificar configuração do nginx
echo "[5/6] Verificando configuração do nginx..."
docker exec hotel_nginx_prod nginx -t
echo ""

# 6. Reiniciar frontend e nginx
echo "[6/6] Reiniciando frontend e nginx..."
cd /opt/hotel
docker-compose -f docker-compose.production.yml restart frontend nginx
echo ""

echo "=========================================="
echo "  Diagnóstico Concluído!"
echo "=========================================="
echo ""
echo "Aguarde 10 segundos e teste o site novamente."
