# Script PowerShell para injetar 1000 pontos no CPF 48373663843
# Uso: .\inject_points.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Injeção de Pontos - Hotel Cabo Frio" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker está rodando
Write-Host "Verificando Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker não está rodando!" -ForegroundColor Red
    Write-Host "Inicie o Docker Desktop e tente novamente." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker está rodando" -ForegroundColor Green
Write-Host ""

# Encontrar o container do PostgreSQL
Write-Host "Procurando container do PostgreSQL..." -ForegroundColor Yellow
$postgresContainer = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-Object -First 1

if ([string]::IsNullOrEmpty($postgresContainer)) {
    Write-Host "❌ Container do PostgreSQL não encontrado!" -ForegroundColor Red
    Write-Host "Execute: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Container encontrado: $postgresContainer" -ForegroundColor Green
Write-Host ""

# Executar SQL
Write-Host "Injetando 1000 pontos para CPF 48373663843..." -ForegroundColor Yellow
Write-Host ""

$sql = @"
-- Verificar cliente antes
SELECT 'ANTES DO UPDATE:' as status;
SELECT id, nome, documento, saldo_pontos FROM "Cliente" WHERE documento = '48373663843';

-- Atualizar pontos
UPDATE "Cliente" 
SET saldo_pontos = COALESCE(saldo_pontos, 0) + 1000,
    updated_at = NOW()
WHERE documento = '48373663843';

-- Registrar transação
INSERT INTO "TransacaoPontos" (
    cliente_id,
    tipo,
    pontos,
    descricao,
    created_at
)
SELECT 
    id,
    'CREDITO',
    1000,
    'Crédito manual de pontos para teste de resgate',
    NOW()
FROM "Cliente"
WHERE documento = '48373663843';

-- Verificar resultado
SELECT 'DEPOIS DO UPDATE:' as status;
SELECT id, nome, documento, saldo_pontos, updated_at FROM "Cliente" WHERE documento = '48373663843';

SELECT 'TRANSAÇÕES RECENTES:' as status;
SELECT tp.id, tp.tipo, tp.pontos, tp.descricao, tp.created_at
FROM "TransacaoPontos" tp
JOIN "Cliente" c ON tp.cliente_id = c.id
WHERE c.documento = '48373663843'
ORDER BY tp.created_at DESC
LIMIT 5;
"@

# Executar no container
docker exec -i $postgresContainer psql -U postgres -d hotel_cabo_frio -c "$sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✓ Pontos injetados com sucesso!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos passos:" -ForegroundColor Cyan
    Write-Host "1. Acesse: http://localhost:8080/consultar-pontos" -ForegroundColor White
    Write-Host "2. Digite o CPF: 483.736.638-43" -ForegroundColor White
    Write-Host "3. Clique em 'Consultar Pontos'" -ForegroundColor White
    Write-Host "4. Você verá 1000 pontos disponíveis" -ForegroundColor White
    Write-Host "5. Clique em '🎁 Resgatar Agora' em um prêmio disponível" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Erro ao injetar pontos!" -ForegroundColor Red
    Write-Host "Verifique os logs acima para mais detalhes." -ForegroundColor Red
    exit 1
}
