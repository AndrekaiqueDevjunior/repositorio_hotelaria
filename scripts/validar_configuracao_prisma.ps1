# ============================================================
# VALIDAÇÃO COMPLETA - Configuração Prisma Remoto
# ============================================================
# Script completo para validar e testar a configuração
# do banco de dados remoto Prisma Data Platform
# ============================================================

param(
    [switch]$SkipBackendTest,
    [switch]$Verbose
)

Write-Host "[VALIDACAO] COMPLETA - Prisma Data Platform" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Gray

$ErrorCount = 0
$WarningCount = 0

# Funcao para log com cores
function Write-Status {
    param($Message, $Type = "Info")
    switch ($Type) {
        "Success" { Write-Host "[OK] $Message" -ForegroundColor Green }
        "Error" { Write-Host "[ERRO] $Message" -ForegroundColor Red; $script:ErrorCount++ }
        "Warning" { Write-Host "[AVISO] $Message" -ForegroundColor Yellow; $script:WarningCount++ }
        "Info" { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
        default { Write-Host $Message }
    }
}

# 1. VALIDAR ARQUIVOS .ENV
Write-Host "`n[1] VALIDACAO DOS ARQUIVOS .ENV" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

# Backend .env
if (Test-Path ".\backend\.env") {
    Write-Status "Arquivo backend/.env encontrado" "Success"
    
    $backendEnv = Get-Content ".\backend\.env" -Raw
    if ($backendEnv -match "DATABASE_URL=.*db\.prisma\.io") {
        Write-Status "DATABASE_URL do Prisma encontrada no backend/.env" "Success"
    } elseif ($backendEnv -match "DATABASE_URL=.*localhost|127\.0\.0\.1|postgres:5432") {
        Write-Status "PROBLEMA: DATABASE_URL local encontrada no backend/.env!" "Error"
    } else {
        Write-Status "DATABASE_URL nao encontrada no backend/.env" "Error"
    }
} else {
    Write-Status "Arquivo backend/.env nao encontrado!" "Error"
}

# Root .env
if (Test-Path ".\.env") {
    Write-Status "Arquivo raiz/.env encontrado" "Success"
    
    $rootEnv = Get-Content ".\.env" -Raw
    if ($rootEnv -match "DATABASE_URL=.*db\.prisma\.io") {
        Write-Status "DATABASE_URL do Prisma encontrada no raiz/.env" "Info"
    }
} else {
    Write-Status "Arquivo raiz/.env nao encontrado" "Warning"
}

# 2. VALIDAR DOCKER-COMPOSE.YML
Write-Host "`n[2] VALIDACAO DO DOCKER-COMPOSE" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

if (Test-Path ".\docker-compose.yml") {
    $dockerCompose = Get-Content ".\docker-compose.yml" -Raw
    
    # Verificar env_file
    if ($dockerCompose -match "env_file:\s*-\s*\./backend/\.env") {
        Write-Status "Docker-compose configurado para usar backend/.env" "Success"
    } else {
        Write-Status "Docker-compose NAO esta usando backend/.env" "Error"
    }
    
    # Verificar DATABASE_URL hardcoded
    if ($dockerCompose -match "DATABASE_URL:\s*postgresql://.*postgres:5432") {
        Write-Status "PROBLEMA: DATABASE_URL local hardcoded no docker-compose!" "Error"
    } else {
        Write-Status "Nenhuma DATABASE_URL local hardcoded encontrada" "Success"
    }
    
    # Verificar dependência do postgres
    if ($dockerCompose -match "depends_on:\s*postgres:") {
        Write-Status "ATENCAO: Backend ainda depende do servico postgres local" "Warning"
        Write-Host "   Considere remover a dependencia ja que usa Prisma remoto" -ForegroundColor Yellow
    }
} else {
    Write-Status "docker-compose.yml nao encontrado!" "Error"
}

# 3. VALIDAR CONFIGURACAO PYDANTIC
Write-Host "`n[3] VALIDACAO DA CONFIGURACAO PYDANTIC" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

if (Test-Path ".\backend\app\config.py") {
    $configPy = Get-Content ".\backend\app\config.py" -Raw
    
    if ($configPy -match "env_override\s*=\s*True") {
        Write-Status "pydantic_settings configurado com env_override=True" "Success"
    } else {
        Write-Status "pydantic_settings SEM env_override=True" "Warning"
        Write-Host "   Variaveis de ambiente podem nao sobrescrever o .env" -ForegroundColor Yellow
    }
    
    if ($configPy -match 'env_file\s*=\s*"\.env"') {
        Write-Status "pydantic_settings configurado para ler .env" "Success"
    } else {
        Write-Status "pydantic_settings pode nao estar lendo .env" "Warning"
    }
} else {
    Write-Status "backend/app/config.py nao encontrado!" "Error"
}

# 4. TESTAR VARIAVEIS DE AMBIENTE
Write-Host "`n[4] TESTE DE VARIAVEIS DE AMBIENTE" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

# Simular carregamento do .env do backend
if (Test-Path ".\backend\.env") {
    $envVars = @{}
    Get-Content ".\backend\.env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $envVars[$matches[1]] = $matches[2]
        }
    }
    
    if ($envVars.ContainsKey("DATABASE_URL")) {
        $dbUrl = $envVars["DATABASE_URL"]
        $maskedUrl = $dbUrl -replace "://[^@]+@", "://****:****@"
        Write-Status "DATABASE_URL carregada: $maskedUrl" "Success"
        
        if ($dbUrl -match "db\.prisma\.io") {
            Write-Status "Confirmado: URL aponta para Prisma Data Platform" "Success"
        } else {
            Write-Status "PROBLEMA: URL nao aponta para Prisma remoto!" "Error"
        }
    } else {
        Write-Status "DATABASE_URL nao encontrada no backend/.env!" "Error"
    }
}

# 5. TESTAR BACKEND (SE SOLICITADO)
if (-not $SkipBackendTest) {
    Write-Host "`n[5] TESTE DE CONEXAO COM BACKEND" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
    
    try {
        Write-Host "Testando endpoint de debug..." -ForegroundColor Gray
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/debug/prisma" -Method GET -TimeoutSec 15
        
        Write-Status "Backend respondeu com sucesso!" "Success"
        
        if ($response.prisma_connected -eq $true) {
            Write-Status "Prisma conectado ao banco" "Success"
        } else {
            Write-Status "Prisma NAO esta conectado!" "Error"
        }
        
        if ($response.database_url_masked -match "db\.prisma\.io") {
            Write-Status "Backend confirmou uso do Prisma remoto" "Success"
        } else {
            Write-Status "Backend pode nao estar usando Prisma remoto!" "Warning"
        }
        
        # Mostrar contagens se disponiveis
        if ($response.tables -and $Verbose) {
            Write-Host "`n[DADOS] Contagens de registros:" -ForegroundColor Cyan
            $response.tables.PSObject.Properties | ForEach-Object {
                Write-Host "   $($_.Name): $($_.Value)" -ForegroundColor White
            }
        }
        
        # Mostrar erros se houver
        if ($response.errors -and $response.errors.Count -gt 0) {
            Write-Status "Erros encontrados no backend:" "Warning"
            $response.errors | ForEach-Object {
                Write-Host "   - $_" -ForegroundColor Red
            }
        }
        
    } catch {
        Write-Status "Backend nao esta respondendo" "Warning"
        Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   Para testar: Inicie o backend e execute novamente" -ForegroundColor Gray
    }
} else {
    Write-Host "`n[5] TESTE DE BACKEND PULADO (use -SkipBackendTest para pular)" -ForegroundColor Yellow
}

# 6. EXECUTAR VALIDACAO PYTHON (SE DISPONIVEL)
Write-Host "`n[6] VALIDACAO PYTHON DIRETA" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

if (Test-Path ".\backend\validar_prisma_remoto.py") {
    try {
        Write-Host "Executando validação Python..." -ForegroundColor Gray
        
        Push-Location ".\backend"
        $pythonResult = python validar_prisma_remoto.py 2>&1
        Pop-Location
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Validacao Python executada com sucesso!" "Success"
            if ($Verbose) {
                Write-Host $pythonResult -ForegroundColor Gray
            }
        } else {
            Write-Status "Validacao Python falhou" "Error"
            Write-Host $pythonResult -ForegroundColor Red
        }
    } catch {
        Write-Status "Erro ao executar validacao Python" "Warning"
        Write-Host "   Certifique-se de que Python esta instalado e no PATH" -ForegroundColor Yellow
    }
} else {
    Write-Status "Script de validacao Python nao encontrado" "Warning"
}

# 7. RESUMO FINAL
Write-Host "`n[7] RESUMO DA VALIDACAO" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`nResultados:" -ForegroundColor White
Write-Host "   Erros: $ErrorCount" -ForegroundColor $(if ($ErrorCount -eq 0) { "Green" } else { "Red" })
Write-Host "   Avisos: $WarningCount" -ForegroundColor $(if ($WarningCount -eq 0) { "Green" } else { "Yellow" })

if ($ErrorCount -eq 0) {
    Write-Host "`n[SUCESSO] Configuracao validada!" -ForegroundColor Green
    Write-Host "   O sistema esta configurado para usar o Prisma Data Platform remoto." -ForegroundColor Green
} elseif ($ErrorCount -le 2) {
    Write-Host "`n[ATENCAO] Alguns problemas encontrados" -ForegroundColor Yellow
    Write-Host "   Revise os erros acima e corrija antes de usar em producao." -ForegroundColor Yellow
} else {
    Write-Host "`n[FALHA] Muitos problemas encontrados!" -ForegroundColor Red
    Write-Host "   Corrija os erros antes de continuar." -ForegroundColor Red
}

# 8. COMANDOS UTEIS
Write-Host "`n[COMANDOS] COMANDOS UTEIS:" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Reiniciar containers:" -ForegroundColor White
Write-Host "   docker-compose down && docker-compose up -d" -ForegroundColor Gray
Write-Host "`nVer logs do backend:" -ForegroundColor White
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "`nTestar endpoint diretamente:" -ForegroundColor White
Write-Host "   curl http://localhost:8000/api/v1/debug/prisma" -ForegroundColor Gray
Write-Host "`nExecutar validação Python:" -ForegroundColor White
Write-Host "   cd backend && python validar_prisma_remoto.py" -ForegroundColor Gray

Write-Host "`n[CONCLUIDO] Validacao concluida!" -ForegroundColor Green

# Retornar código de saída baseado nos erros
exit $ErrorCount
