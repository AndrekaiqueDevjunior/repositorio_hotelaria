# ============================================================
# SCRIPT DE APLICAÇÃO - Migration Sistema de Pontos (Windows)
# Data: 21/12/2024
# Descrição: Aplica a migration de correção do sistema de pontos
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "APLICAÇÃO DA MIGRATION - SISTEMA DE PONTOS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Configurações (ajustar conforme necessário)
$DB_HOST = if ($env:DB_HOST) { $env:DB_HOST } else { "localhost" }
$DB_PORT = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }
$DB_NAME = if ($env:DB_NAME) { $env:DB_NAME } else { "hotel_cabo_frio" }
$DB_USER = if ($env:DB_USER) { $env:DB_USER } else { "postgres" }

$MIGRATION_FILE = ".\002_corrigir_sistema_pontos.sql"

# Verificar se o arquivo de migration existe
if (-not (Test-Path $MIGRATION_FILE)) {
    Write-Host ""
    Write-Host "❌ ERRO: Arquivo de migration não encontrado!" -ForegroundColor Red
    Write-Host "   Esperado: $MIGRATION_FILE" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⚠️  ATENÇÃO:" -ForegroundColor Yellow
Write-Host "   Esta migration irá modificar a estrutura do banco de dados."
Write-Host "   Certifique-se de ter um backup recente!"
Write-Host ""

$backup = Read-Host "Você fez backup do banco de dados? (s/N)"

if ($backup -ne "s" -and $backup -ne "S") {
    Write-Host ""
    Write-Host "❌ ABORTADO!" -ForegroundColor Red
    Write-Host "   Execute primeiro o backup!" -ForegroundColor Red
    Write-Host "   pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > backup.sql"
    exit 1
}

Write-Host ""
Write-Host "📊 Informações da migration:" -ForegroundColor Cyan
Write-Host "   Arquivo: $MIGRATION_FILE"
Write-Host "   Banco: $DB_NAME"
Write-Host "   Host: ${DB_HOST}:${DB_PORT}"
Write-Host ""

$confirm = Read-Host "Confirma aplicação da migration? (s/N)"

if ($confirm -ne "s" -and $confirm -ne "S") {
    Write-Host "❌ ABORTADO pelo usuário." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Aplicando migration..." -ForegroundColor Cyan
Write-Host ""

# Definir senha do PostgreSQL (se necessário)
if ($env:PGPASSWORD) {
    $env:PGPASSWORD = $env:PGPASSWORD
} else {
    Write-Host "⚠️  Você pode precisar informar a senha do PostgreSQL" -ForegroundColor Yellow
}

# Aplicar migration
try {
    $output = & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE 2>&1
    
    Write-Host $output
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "✅ MIGRATION APLICADA COM SUCESSO!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos passos:" -ForegroundColor Cyan
    Write-Host "  1. Verificar logs acima para estatísticas"
    Write-Host "  2. Testar o sistema de pontos"
    Write-Host "  3. Verificar histórico de transações"
    Write-Host ""
    Write-Host "Em caso de problemas, restaure o backup:" -ForegroundColor Yellow
    Write-Host "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < backup.sql"
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "❌ ERRO AO APLICAR MIGRATION!" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Erro: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "A migration foi revertida automaticamente (ROLLBACK)." -ForegroundColor Yellow
    Write-Host "Verifique os erros acima e corrija antes de tentar novamente."
    Write-Host ""
    exit 1
}

