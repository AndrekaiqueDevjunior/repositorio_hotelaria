# Script de Validacao para Configuracao Ngrok
# Uso: .\VALIDAR_NGROK.ps1

param(
    [string]$FrontendUrl = "",
    [string]$BackendUrl = ""
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VALIDACAO DE CONFIGURACAO NGROK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Funcao para testar endpoint
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] $Name - Status 200" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[AVISO] $Name - Status $($response.StatusCode)" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "[ERRO] $Name - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 1. Verificar servicos locais
Write-Host "[1] Verificando servicos locais..." -ForegroundColor Yellow
Write-Host ""

$backendLocal = Test-Endpoint -Url "http://localhost:8000/health" -Name "Backend Local"
$frontendLocal = Test-Endpoint -Url "http://localhost:3000" -Name "Frontend Local"

if (-not $backendLocal -or -not $frontendLocal) {
    Write-Host "`n[ERRO] Servicos locais nao estao rodando!" -ForegroundColor Red
    Write-Host "[INFO] Execute: docker-compose up -d backend frontend" -ForegroundColor Cyan
    exit 1
}

# 2. Verificar tuneis ngrok
Write-Host "`n[2] Verificando tuneis ngrok..." -ForegroundColor Yellow
Write-Host ""

try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    
    if ($tunnels.tunnels.Count -eq 0) {
        Write-Host "[ERRO] Nenhum tunel ngrok ativo!" -ForegroundColor Red
        Write-Host "[INFO] Execute: .\INICIAR_NGROK_DUAL.ps1" -ForegroundColor Cyan
        exit 1
    }
    
    Write-Host "[OK] $($tunnels.tunnels.Count) tunel(is) ativo(s)" -ForegroundColor Green
    
    foreach ($tunnel in $tunnels.tunnels) {
        $port = $tunnel.config.addr -replace ".*:", ""
        $url = $tunnel.public_url
        
        if ($port -eq "8000") {
            $BackendUrl = $url
            Write-Host "[INFO] Backend Ngrok: $url" -ForegroundColor White
        }
        elseif ($port -eq "3000") {
            $FrontendUrl = $url
            Write-Host "[INFO] Frontend Ngrok: $url" -ForegroundColor White
        }
    }
    
} catch {
    Write-Host "[ERRO] Ngrok nao esta rodando ou API nao acessivel" -ForegroundColor Red
    Write-Host "[INFO] Verifique se ngrok esta ativo em http://localhost:4040" -ForegroundColor Cyan
    exit 1
}

# 3. Verificar arquivo .env (backend)
Write-Host "`n[3] Verificando configuracao backend (.env)..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    # Verificar CORS_ORIGINS
    if ($envContent -match "CORS_ORIGINS=(.+)") {
        $corsOrigins = $matches[1]
        Write-Host "[INFO] CORS_ORIGINS encontrado" -ForegroundColor White
        
        if ($FrontendUrl -and $corsOrigins -notmatch [regex]::Escape($FrontendUrl)) {
            Write-Host "[AVISO] Frontend URL nao esta em CORS_ORIGINS!" -ForegroundColor Yellow
            Write-Host "[ACAO] Adicione: $FrontendUrl" -ForegroundColor Cyan
        } else {
            Write-Host "[OK] CORS_ORIGINS configurado corretamente" -ForegroundColor Green
        }
    } else {
        Write-Host "[AVISO] CORS_ORIGINS nao encontrado em .env" -ForegroundColor Yellow
    }
    
    # Verificar configuracoes de cookie
    $cookieChecks = @{
        "COOKIE_SECURE" = "true"
        "COOKIE_SAMESITE" = "none"
    }
    
    foreach ($key in $cookieChecks.Keys) {
        if ($envContent -match "$key=(.+)") {
            $value = $matches[1].Trim()
            if ($value -eq $cookieChecks[$key]) {
                Write-Host "[OK] $key=$value" -ForegroundColor Green
            } else {
                Write-Host "[AVISO] $key=$value (esperado: $($cookieChecks[$key]))" -ForegroundColor Yellow
            }
        } else {
            Write-Host "[AVISO] $key nao encontrado" -ForegroundColor Yellow
        }
    }
    
} else {
    Write-Host "[ERRO] Arquivo .env nao encontrado!" -ForegroundColor Red
}

# 4. Verificar arquivo .env.local (frontend)
Write-Host "`n[4] Verificando configuracao frontend (.env.local)..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "frontend/.env.local") {
    $envLocalContent = Get-Content "frontend/.env.local" -Raw
    
    if ($envLocalContent -match "NEXT_PUBLIC_API_URL=(.+)") {
        $apiUrl = $matches[1].Trim()
        Write-Host "[INFO] NEXT_PUBLIC_API_URL=$apiUrl" -ForegroundColor White
        
        if ($BackendUrl -and $apiUrl -notmatch [regex]::Escape($BackendUrl)) {
            Write-Host "[AVISO] URL do backend ngrok nao configurada!" -ForegroundColor Yellow
            Write-Host "[ACAO] Configure: NEXT_PUBLIC_API_URL=$BackendUrl/api/v1" -ForegroundColor Cyan
        } else {
            Write-Host "[OK] NEXT_PUBLIC_API_URL configurado corretamente" -ForegroundColor Green
        }
    } else {
        Write-Host "[AVISO] NEXT_PUBLIC_API_URL nao encontrado" -ForegroundColor Yellow
    }
} else {
    Write-Host "[AVISO] Arquivo frontend/.env.local nao encontrado" -ForegroundColor Yellow
    Write-Host "[INFO] Crie a partir de: frontend/.env.local.ngrok.example" -ForegroundColor Cyan
}

# 5. Testar endpoints ngrok
if ($BackendUrl) {
    Write-Host "`n[5] Testando endpoints ngrok..." -ForegroundColor Yellow
    Write-Host ""
    
    Test-Endpoint -Url "$BackendUrl/health" -Name "Backend Health (Ngrok)" | Out-Null
    Test-Endpoint -Url "$BackendUrl/api/v1/info" -Name "Backend API Info (Ngrok)" | Out-Null
}

# 6. Resumo e proximos passos
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESUMO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "URLs Ngrok Detectadas:" -ForegroundColor Yellow
if ($FrontendUrl) {
    Write-Host "  Frontend: $FrontendUrl" -ForegroundColor White
} else {
    Write-Host "  Frontend: [NAO DETECTADO]" -ForegroundColor Red
}

if ($BackendUrl) {
    Write-Host "  Backend:  $BackendUrl" -ForegroundColor White
} else {
    Write-Host "  Backend:  [NAO DETECTADO]" -ForegroundColor Red
}

Write-Host "`nProximos Passos:" -ForegroundColor Yellow
Write-Host "1. Atualize .env com CORS_ORIGINS incluindo as URLs acima" -ForegroundColor White
Write-Host "2. Atualize frontend/.env.local com NEXT_PUBLIC_API_URL=$BackendUrl/api/v1" -ForegroundColor White
Write-Host "3. Reinicie os containers: docker-compose restart backend frontend" -ForegroundColor White
Write-Host "4. Acesse $FrontendUrl e faca login" -ForegroundColor White
Write-Host "5. Verifique console do browser (F12) para erros de CORS" -ForegroundColor White

Write-Host "`n[INFO] Para testar login:" -ForegroundColor Cyan
Write-Host "  Email: admin@hotelreal.com.br" -ForegroundColor Gray
Write-Host "  Senha: admin123" -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
