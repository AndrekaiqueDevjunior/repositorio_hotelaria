# ============================================================
# VALIDACAO FINAL - Prisma Data Platform
# ============================================================
# Script definitivo para validar se o sistema esta usando
# EXCLUSIVAMENTE o Prisma Data Platform remoto
# ============================================================

Write-Host "[VALIDACAO FINAL] Prisma Data Platform - Hotel Cabo Frio" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Gray

$ErrorCount = 0
$SuccessCount = 0

function Write-Result {
    param($Message, $Type = "Info")
    switch ($Type) {
        "Success" { 
            Write-Host "[OK] $Message" -ForegroundColor Green
            $script:SuccessCount++
        }
        "Error" { 
            Write-Host "[ERRO] $Message" -ForegroundColor Red
            $script:ErrorCount++
        }
        "Warning" { 
            Write-Host "[AVISO] $Message" -ForegroundColor Yellow
        }
        "Info" { 
            Write-Host "[INFO] $Message" -ForegroundColor Cyan
        }
    }
}

# ETAPA 1: VALIDAR CONFIGURACAO DOS ARQUIVOS
Write-Host "`n[ETAPA 1] VALIDACAO DE CONFIGURACAO" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

# Verificar backend/.env
if (Test-Path ".\backend\.env") {
    $backendEnv = Get-Content ".\backend\.env" -Raw
    if ($backendEnv -match "DATABASE_URL=.*db\.prisma\.io") {
        Write-Result "backend/.env aponta para Prisma Data Platform" "Success"
    } else {
        Write-Result "backend/.env NAO aponta para Prisma remoto!" "Error"
    }
} else {
    Write-Result "backend/.env nao encontrado!" "Error"
}

# Verificar docker-compose.yml
if (Test-Path ".\docker-compose.yml") {
    $dockerCompose = Get-Content ".\docker-compose.yml" -Raw
    
    if ($dockerCompose -match "env_file:\s*-\s*\./backend/\.env") {
        Write-Result "docker-compose.yml usa env_file do backend" "Success"
    } else {
        Write-Result "docker-compose.yml NAO usa env_file do backend!" "Error"
    }
    
    if ($dockerCompose -notmatch "depends_on:\s*postgres:") {
        Write-Result "docker-compose.yml NAO depende do postgres local" "Success"
    } else {
        Write-Result "docker-compose.yml ainda depende do postgres local!" "Error"
    }
} else {
    Write-Result "docker-compose.yml nao encontrado!" "Error"
}

# ETAPA 2: TESTAR BACKEND EM RUNTIME
Write-Host "`n[ETAPA 2] TESTE DE RUNTIME" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

try {
    Write-Host "Testando endpoint critico de runtime..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/runtime-debug/database-connection-proof" -Method GET -TimeoutSec 20
    
    Write-Result "Backend respondeu ao teste de runtime" "Success"
    
    # Analisar resposta critica
    if ($response.critical_diagnosis -eq "SUCCESS_PRISMA_REMOTE") {
        Write-Result "CONFIRMADO: Backend conectado ao Prisma Data Platform!" "Success"
    } elseif ($response.critical_diagnosis -eq "PROBLEM_LOCAL_DB") {
        Write-Result "PROBLEMA: Backend ainda conectado ao banco local!" "Error"
    } else {
        Write-Result "Status indefinido: $($response.critical_diagnosis)" "Warning"
    }
    
    # Verificar DATABASE_URL em runtime
    $dbUrl = $response.environment_vars.DATABASE_URL_masked
    if ($dbUrl -match "db\.prisma\.io") {
        Write-Result "DATABASE_URL em runtime aponta para Prisma remoto" "Success"
    } else {
        Write-Result "DATABASE_URL em runtime NAO aponta para Prisma remoto!" "Error"
    }
    
    # Verificar contagens
    if ($response.record_counts) {
        Write-Host "`n[CONTAGENS] Registros encontrados:" -ForegroundColor Cyan
        $totalRecords = 0
        $response.record_counts.PSObject.Properties | ForEach-Object {
            if ($_.Name -ne "error") {
                Write-Host "   $($_.Name): $($_.Value)" -ForegroundColor White
                $totalRecords += [int]$_.Value
            }
        }
        
        if ($totalRecords -gt 50) {
            Write-Result "Contagem de registros indica banco com dados (total: $totalRecords)" "Success"
        } elseif ($totalRecords -gt 10) {
            Write-Result "Contagem moderada de registros (total: $totalRecords)" "Warning"
        } else {
            Write-Result "Poucos registros encontrados (total: $totalRecords) - possivel banco local/vazio" "Error"
        }
    }
    
} catch {
    Write-Result "Backend nao esta respondendo ou erro no teste" "Error"
    Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Certifique-se de que o backend esta rodando" -ForegroundColor Yellow
}

# ETAPA 3: COMPARACAO COM PRISMA STUDIO
Write-Host "`n[ETAPA 3] INSTRUCOES PARA COMPARACAO COM PRISMA STUDIO" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

Write-Host "MANUAL: Compare os numeros acima com o Prisma Studio:" -ForegroundColor White
Write-Host "1. Acesse: https://cloud.prisma.io/" -ForegroundColor Gray
Write-Host "2. Abra seu projeto Hotel Cabo Frio" -ForegroundColor Gray
Write-Host "3. Va para Data Browser" -ForegroundColor Gray
Write-Host "4. Compare as contagens de cada tabela" -ForegroundColor Gray
Write-Host "5. Os numeros DEVEM ser IDENTICOS" -ForegroundColor Gray

# ETAPA 4: RESULTADO FINAL
Write-Host "`n[ETAPA 4] RESULTADO FINAL" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`nResumo:" -ForegroundColor White
Write-Host "   Sucessos: $SuccessCount" -ForegroundColor Green
Write-Host "   Erros: $ErrorCount" -ForegroundColor $(if ($ErrorCount -eq 0) { "Green" } else { "Red" })

if ($ErrorCount -eq 0) {
    Write-Host "`n[SUCESSO TOTAL] Sistema configurado corretamente!" -ForegroundColor Green
    Write-Host "O backend esta usando EXCLUSIVAMENTE o Prisma Data Platform." -ForegroundColor Green
    Write-Host "As contagens devem bater 100% com o Prisma Studio." -ForegroundColor Green
} elseif ($ErrorCount -le 2) {
    Write-Host "`n[SUCESSO PARCIAL] Alguns problemas menores encontrados" -ForegroundColor Yellow
    Write-Host "Revise os erros acima antes de usar em producao." -ForegroundColor Yellow
} else {
    Write-Host "`n[FALHA] Muitos problemas encontrados!" -ForegroundColor Red
    Write-Host "O sistema ainda NAO esta usando exclusivamente o Prisma remoto." -ForegroundColor Red
}

# COMANDOS FINAIS
Write-Host "`n[COMANDOS] Para corrigir problemas:" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Reiniciar com nova configuracao:" -ForegroundColor White
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host "   docker-compose up -d --build backend" -ForegroundColor Gray
Write-Host "`nVer logs detalhados:" -ForegroundColor White
Write-Host "   docker-compose logs -f backend | findstr DATABASE" -ForegroundColor Gray
Write-Host "`nTestar novamente:" -ForegroundColor White
Write-Host "   .\validacao_final_prisma.ps1" -ForegroundColor Gray

Write-Host "`n[CONCLUIDO] Validacao final concluida!" -ForegroundColor Green

# Retornar codigo de saida
exit $ErrorCount
