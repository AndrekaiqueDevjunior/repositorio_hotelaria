#!/bin/bash
# ============================================================
# SCRIPT DE BACKUP - Sistema de Pontos
# Data: 21/12/2024
# Descrição: Backup completo antes da migration de pontos
# ============================================================

set -e  # Parar em caso de erro

echo "=========================================="
echo "BACKUP DO BANCO DE DADOS"
echo "=========================================="

# Configurações (ajustar conforme necessário)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-hotel_cabo_frio}"
DB_USER="${DB_USER:-postgres}"

# Nome do arquivo de backup
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_antes_migration_pontos_$TIMESTAMP.sql"

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

echo "📦 Criando backup..."
echo "   Banco: $DB_NAME"
echo "   Arquivo: $BACKUP_FILE"
echo ""

# Fazer backup completo
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F p -f "$BACKUP_FILE"; then
    echo "✅ Backup criado com sucesso!"
    echo "   Tamanho: $(du -h "$BACKUP_FILE" | cut -f1)"
    
    # Comprimir backup
    echo ""
    echo "🗜️  Comprimindo backup..."
    gzip "$BACKUP_FILE"
    echo "✅ Backup comprimido: ${BACKUP_FILE}.gz"
    echo "   Tamanho comprimido: $(du -h "${BACKUP_FILE}.gz" | cut -f1)"
    
    echo ""
    echo "=========================================="
    echo "BACKUP ESPECÍFICO - TABELAS DE PONTOS"
    echo "=========================================="
    
    BACKUP_PONTOS_FILE="$BACKUP_DIR/backup_pontos_$TIMESTAMP.sql"
    
    # Backup apenas das tabelas relacionadas a pontos
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t usuarios_pontos \
        -t transacoes_pontos \
        -t historico_pontos \
        -F p -f "$BACKUP_PONTOS_FILE"
    
    gzip "$BACKUP_PONTOS_FILE"
    
    echo "✅ Backup das tabelas de pontos criado!"
    echo "   Arquivo: ${BACKUP_PONTOS_FILE}.gz"
    echo "   Tamanho: $(du -h "${BACKUP_PONTOS_FILE}.gz" | cut -f1)"
    
    echo ""
    echo "=========================================="
    echo "BACKUP CONCLUÍDO!"
    echo "=========================================="
    echo ""
    echo "Para restaurar em caso de problemas:"
    echo "  gunzip ${BACKUP_FILE}.gz"
    echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $BACKUP_FILE"
    echo ""
    
else
    echo "❌ ERRO ao criar backup!"
    echo "   Verifique as credenciais e conexão com o banco."
    exit 1
fi

