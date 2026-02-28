#!/bin/bash
# ============================================================
# SCRIPT DE APLICAÇÃO - Migration Sistema de Pontos
# Data: 21/12/2024
# Descrição: Aplica a migration de correção do sistema de pontos
# ============================================================

set -e  # Parar em caso de erro

echo "=========================================="
echo "APLICAÇÃO DA MIGRATION - SISTEMA DE PONTOS"
echo "=========================================="

# Configurações (ajustar conforme necessário)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-hotel_cabo_frio}"
DB_USER="${DB_USER:-postgres}"

MIGRATION_FILE="./002_corrigir_sistema_pontos.sql"

# Verificar se o arquivo de migration existe
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ ERRO: Arquivo de migration não encontrado!"
    echo "   Esperado: $MIGRATION_FILE"
    exit 1
fi

echo ""
echo "⚠️  ATENÇÃO:"
echo "   Esta migration irá modificar a estrutura do banco de dados."
echo "   Certifique-se de ter um backup recente!"
echo ""
read -p "Você fez backup do banco de dados? (s/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "❌ ABORTADO!"
    echo "   Execute primeiro: ./backup_pontos.sh"
    exit 1
fi

echo ""
echo "📊 Informações da migration:"
echo "   Arquivo: $MIGRATION_FILE"
echo "   Banco: $DB_NAME"
echo "   Host: $DB_HOST:$DB_PORT"
echo ""

read -p "Confirma aplicação da migration? (s/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ ABORTADO pelo usuário."
    exit 1
fi

echo ""
echo "🚀 Aplicando migration..."
echo ""

# Aplicar migration
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE"; then
    echo ""
    echo "=========================================="
    echo "✅ MIGRATION APLICADA COM SUCESSO!"
    echo "=========================================="
    echo ""
    echo "Próximos passos:"
    echo "  1. Verificar logs acima para estatísticas"
    echo "  2. Testar o sistema de pontos"
    echo "  3. Verificar histórico de transações"
    echo ""
    echo "Em caso de problemas, restaure o backup:"
    echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < backup_file.sql"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ ERRO AO APLICAR MIGRATION!"
    echo "=========================================="
    echo ""
    echo "A migration foi revertida automaticamente (ROLLBACK)."
    echo "Verifique os erros acima e corrija antes de tentar novamente."
    echo ""
    exit 1
fi

