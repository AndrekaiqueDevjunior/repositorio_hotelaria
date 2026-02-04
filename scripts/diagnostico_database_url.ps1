# ============================================================
# DIAGNOSTICO DATABASE_URL - Validacao Prisma Remoto
# ============================================================
# Script para validar se o backend esta usando o banco remoto
# do Prisma Data Platform e nao o PostgreSQL local
# ============================================================

Write-Host "[DIAGNOSTICO] DATABASE_URL - Hotel Cabo Frio" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Gray

# 1. Verificar variaveis de ambiente do sistema
Write-Host "`n[1] VARIAVEIS DE AMBIENTE DO SISTEMA:" -ForegroundColor Yellow
Write-Host "DATABASE_URL (sistema): " -NoNewline
$systemDbUrl = $env:DATABASE_URL
if ($systemDbUrl) {
    # Mascarar credenciais para log seguro
    $maskedUrl = $systemDbUrl -replace "://[^@]+@", "://****:****@"
    Write-Host $maskedUrl -ForegroundColor Green
} else {
    Write-Host "NAO DEFINIDA" -ForegroundColor Red
}

# 2. Verificar arquivo .env do backend
Write-Host "`n[2] ARQUIVO BACKEND/.ENV:" -ForegroundColor Yellow
$backendEnvPath = ".\backend\.env"
if (Test-Path $backendEnvPath) {
    Write-Host "Arquivo encontrado: $backendEnvPath" -ForegroundColor Green
    
    # Ler DATABASE_URL do arquivo
    $envContent = Get-Content $backendEnvPath
    $dbUrlLine = $envContent | Where-Object { $_ -match "^DATABASE_URL=" }
    
    if ($dbUrlLine) {
        $dbUrl = $dbUrlLine -replace "^DATABASE_URL=", ""
        $maskedDbUrl = $dbUrl -replace "://[^@]+@", "://****:****@"
        Write-Host "DATABASE_URL (backend/.env): $maskedDbUrl" -ForegroundColor Green
        
        # Verificar se e Prisma remoto
        if ($dbUrl -match "db\.prisma\.io") {
            Write-Host "[OK] CORRETO: Usando Prisma Data Platform remoto" -ForegroundColor Green
        } elseif ($dbUrl -match "localhost|127\.0\.0\.1|postgres:5432") {
            Write-Host "[ERRO] PROBLEMA: Usando banco local!" -ForegroundColor Red
        } else {
            Write-Host "[AVISO] ATENCAO: Host nao reconhecido" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[ERRO] DATABASE_URL nao encontrada no arquivo!" -ForegroundColor Red
    }
} else {
    Write-Host "[ERRO] Arquivo backend/.env nao encontrado!" -ForegroundColor Red
}

# 3. Verificar arquivo .env da raiz (docker)
Write-Host "`n[3] ARQUIVO RAIZ/.ENV (DOCKER):" -ForegroundColor Yellow
$rootEnvPath = ".\.env"
if (Test-Path $rootEnvPath) {
    Write-Host "Arquivo encontrado: $rootEnvPath" -ForegroundColor Green
    
    $rootEnvContent = Get-Content $rootEnvPath
    $rootDbUrlLine = $rootEnvContent | Where-Object { $_ -match "^DATABASE_URL=" }
    
    if ($rootDbUrlLine) {
        $rootDbUrl = $rootDbUrlLine -replace "^DATABASE_URL=", ""
        $maskedRootDbUrl = $rootDbUrl -replace "://[^@]+@", "://****:****@"
        Write-Host "DATABASE_URL (raiz/.env): $maskedRootDbUrl" -ForegroundColor Green
    } else {
        Write-Host "DATABASE_URL nao encontrada no arquivo raiz" -ForegroundColor Yellow
    }
} else {
    Write-Host "Arquivo .env da raiz nao encontrado" -ForegroundColor Yellow
}

# 4. Testar conexao com backend (se estiver rodando)
Write-Host "`n[4] TESTE DE CONEXAO COM BACKEND:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/debug/prisma" -Method GET -TimeoutSec 10
    
    Write-Host "[OK] Backend respondeu!" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor Cyan
    Write-Host "Prisma conectado: $($response.prisma_connected)" -ForegroundColor Cyan
    Write-Host "DATABASE_URL mascarada: $($response.database_url_masked)" -ForegroundColor Cyan
    
    # Mostrar contagens de tabelas
    if ($response.tables) {
        Write-Host "`n[DADOS] CONTAGENS DE REGISTROS:" -ForegroundColor Yellow
        $response.tables.PSObject.Properties | ForEach-Object {
            Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor White
        }
    }
    
    # Mostrar erros se houver
    if ($response.errors -and $response.errors.Count -gt 0) {
        Write-Host "`n[AVISO] ERROS ENCONTRADOS:" -ForegroundColor Red
        $response.errors | ForEach-Object {
            Write-Host "  - $_" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "[ERRO] Backend nao esta respondendo em http://localhost:8000" -ForegroundColor Red
    Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Certifique-se de que o backend esta rodando" -ForegroundColor Yellow
}

# 5. Verificar docker-compose.yml
Write-Host "`n[5] CONFIGURACAO DOCKER-COMPOSE:" -ForegroundColor Yellow
$dockerComposePath = ".\docker-compose.yml"
if (Test-Path $dockerComposePath) {
    $dockerContent = Get-Content $dockerComposePath -Raw
    
    # Verificar se usa env_file
    if ($dockerContent -match "env_file:\s*-\s*\./backend/\.env") {
        Write-Host "[OK] Docker-compose configurado para usar backend/.env" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] Docker-compose pode nao estar usando backend/.env" -ForegroundColor Yellow
    }
    
    # Verificar se tem DATABASE_URL hardcoded
    if ($dockerContent -match "DATABASE_URL:\s*postgresql://.*postgres:5432") {
        Write-Host "[ERRO] PROBLEMA: Docker-compose tem DATABASE_URL local hardcoded!" -ForegroundColor Red
    } else {
        Write-Host "[OK] Docker-compose nao tem DATABASE_URL local hardcoded" -ForegroundColor Green
    }
} else {
    Write-Host "[ERRO] docker-compose.yml nao encontrado!" -ForegroundColor Red
}

# 6. Resumo e recomendacoes
Write-Host "`n[6] RESUMO E RECOMENDACOES:" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`n[OBJETIVO] PARA GARANTIR USO DO PRISMA REMOTO:" -ForegroundColor Cyan
Write-Host "1. Certifique-se de que backend/.env tem DATABASE_URL do Prisma" -ForegroundColor White
Write-Host "2. Docker-compose deve usar env_file: ./backend/.env" -ForegroundColor White
Write-Host "3. Remover DATABASE_URL hardcoded do docker-compose.yml" -ForegroundColor White
Write-Host "4. Reiniciar containers: docker-compose down && docker-compose up -d" -ForegroundColor White

Write-Host "`n[COMANDOS] COMANDOS UTEIS:" -ForegroundColor Cyan
Write-Host "- Testar backend: curl http://localhost:8000/api/v1/debug/prisma" -ForegroundColor White
Write-Host "- Ver logs: docker-compose logs backend" -ForegroundColor White
Write-Host "- Reiniciar: docker-compose restart backend" -ForegroundColor White

Write-Host "`n[CONCLUIDO] Diagnostico concluido!" -ForegroundColor Green
