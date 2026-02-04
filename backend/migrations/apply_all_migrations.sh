#!/bin/bash
# Script para aplicar todas as migrações em ordem
# Hotel Real Cabo Frio - 2026-02-04

echo "🔄 Aplicando migrações do Hotel Real Cabo Frio..."
echo "📅 Data: 2026-02-04"
echo ""

# Lista de migrações em ordem
MIGRATIONS=(
    "002_corrigir_sistema_pontos.sql"
    "003_adicionar_auditoria.sql"
    "003_implementar_sistema_rp.sql"
    "003_remover_status_duplicado.sql"
    "004_seguranca_pagamentos.sql"
    "005_criar_tabelas_premios.sql"
    "006_add_foto_url_funcionarios.sql"
    "007_fix_colunas_faltantes.sql"
)

# Verificar se estamos no diretório correto
if [ ! -d "backend/migrations" ]; then
    echo "❌ Erro: Execute este script do diretório raiz do projeto"
    exit 1
fi

# Aplicar cada migração
for migration in "${MIGRATIONS[@]}"; do
    echo "📝 Aplicando migração: $migration"
    
    # Verificar se o arquivo existe
    if [ ! -f "backend/migrations/$migration" ]; then
        echo "⚠️  Aviso: Arquivo $migration não encontrado, pulando..."
        continue
    fi
    
    # Aplicar migração (assumindo PostgreSQL)
    psql -U postgres -d hotel_cabo_frio -f "backend/migrations/$migration"
    
    if [ $? -eq 0 ]; then
        echo "✅ Migração $migration aplicada com sucesso"
    else
        echo "❌ Erro ao aplicar migração $migration"
        exit 1
    fi
    
    echo ""
done

echo "🎉 Todas as migrações foram aplicadas com sucesso!"
echo "📊 Banco de dados atualizado e pronto para uso"
echo ""
echo "🔐 Credenciais de acesso:"
echo "   Email: admin@hotelrealcabofrio.com"
echo "   Senha: JSNIKDHJUOPLjnsodpsaud09p32hj20921hdy80@##*HfjçNHHçjsh"
echo ""
echo "🚀 Para iniciar o sistema:"
echo "   docker compose up -d"
