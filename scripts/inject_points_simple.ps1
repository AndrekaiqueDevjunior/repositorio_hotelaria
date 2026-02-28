# Script simplificado para injetar 1000 pontos
Write-Host "Iniciando injeção de 1000 pontos..." -ForegroundColor Cyan

# Verificar Docker
if (-not (docker ps 2>&1 | Out-String) -match "CONTAINER") {
    Write-Host "❌ Docker não está rodando!" -ForegroundColor Red
    exit 1
}

# Encontrar container PostgreSQL
$container = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-Object -First 1
if (-not $container) {
    Write-Host "❌ Container do PostgreSQL não encontrado!" -ForegroundColor Red
    Write-Host "Execute: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Container encontrado: $container" -ForegroundColor Green

# Comando SQL
$sql = @"
-- Verificar antes
SELECT 'ANTES:' as status;
SELECT id, nome, documento, saldo_pontos FROM "Cliente" WHERE documento = '48373663843';

-- Atualizar pontos
UPDATE "Cliente" 
SET saldo_pontos = COALESCE(saldo_pontos, 0) + 1000,
    updated_at = NOW()
WHERE documento = '48373663843';

-- Registrar transação
INSERT INTO "TransacaoPontos" (cliente_id, tipo, pontos, descricao, created_at)
SELECT id, 'CREDITO', 1000, 'Crédito manual', NOW()
FROM "Cliente"
WHERE documento = '48373663843';

-- Verificar depois
SELECT 'DEPOIS:' as status;
SELECT id, nome, documento, saldo_pontos FROM "Cliente" WHERE documento = '48373663843';
"@

# Executar SQL
docker exec -i $container psql -U postgres -d hotel_cabo_frie -c "$sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Pontos injetados com sucesso!" -ForegroundColor Green
    Write-Host "Acesse: http://localhost:8080/consultar-pontos" -ForegroundColor Cyan
    Write-Host "CPF: 483.736.638-43" -ForegroundColor Cyan
} else {
    Write-Host "❌ Erro ao executar SQL" -ForegroundColor Red
}
