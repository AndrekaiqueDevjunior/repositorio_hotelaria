#!/bin/sh
# ============================================================
# SCRIPT DE BACKUP AUTOMÁTICO - POSTGRESQL
# ============================================================
# Executa backup diário do banco de dados PostgreSQL
# Mantém backups dos últimos N dias (definido por BACKUP_RETENTION_DAYS)
# ============================================================

set -e

# Variáveis de ambiente (definidas no docker-compose)
BACKUP_DIR="/backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/hotel_backup_${TIMESTAMP}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

echo "============================================================"
echo "BACKUP POSTGRESQL - $(date)"
echo "============================================================"
echo "Database: ${POSTGRES_DB}"
echo "Host: ${POSTGRES_HOST}"
echo "Retention: ${RETENTION_DAYS} days"
echo "============================================================"

# Criar diretório de backup se não existir
mkdir -p ${BACKUP_DIR}

# Executar backup
echo "[$(date)] Iniciando backup..."
PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    -F p \
    --no-owner \
    --no-acl \
    > ${BACKUP_FILE}

# Verificar se backup foi criado
if [ -f "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    echo "[$(date)] Backup criado com sucesso: ${BACKUP_FILE} (${BACKUP_SIZE})"
    
    # Comprimir backup
    echo "[$(date)] Comprimindo backup..."
    gzip ${BACKUP_FILE}
    COMPRESSED_FILE="${BACKUP_FILE}.gz"
    COMPRESSED_SIZE=$(du -h ${COMPRESSED_FILE} | cut -f1)
    echo "[$(date)] Backup comprimido: ${COMPRESSED_FILE} (${COMPRESSED_SIZE})"
else
    echo "[$(date)] ERRO: Backup falhou!"
    exit 1
fi

# Limpar backups antigos
echo "[$(date)] Limpando backups antigos (>${RETENTION_DAYS} dias)..."
find ${BACKUP_DIR} -name "hotel_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
REMAINING_BACKUPS=$(find ${BACKUP_DIR} -name "hotel_backup_*.sql.gz" -type f | wc -l)
echo "[$(date)] Backups mantidos: ${REMAINING_BACKUPS}"

echo "============================================================"
echo "BACKUP CONCLUÍDO - $(date)"
echo "============================================================"
