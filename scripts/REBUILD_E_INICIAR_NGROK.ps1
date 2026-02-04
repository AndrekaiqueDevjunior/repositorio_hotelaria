# =========================================
# Rebuild Completo + ngrok FREE
# =========================================
# Preserva dados do banco de dados

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  REBUILD + NGROK FREE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Rebuild apenas backend e frontend (preserva postgres)
Write-Host "[1/9] Rebuilding Backend..." -ForegroundColor Cyan
docker-compose build --no-cache backend
Write-Host ""

Write-Host "[2/9] Rebuilding Frontend..." -ForegroundColor Cyan
docker-compose build --no-cache frontend
Write-Host ""

# Iniciar PostgreSQL (com dados preservados)
Write-Host "[3/9] Iniciando PostgreSQL (dados preservados)..." -ForegroundColor Cyan
docker-compose up -d postgres
Start-Sleep -Seconds 10

# Iniciar Redis
Write-Host "[4/9] Iniciando Redis..." -ForegroundColor Cyan
docker-compose up -d redis
Start-Sleep -Seconds 5

# Iniciar Backend
Write-Host "[5/9] Iniciando Backend..." -ForegroundColor Cyan
docker-compose up -d backend
Start-Sleep -Seconds 12

# Iniciar Frontend
Write-Host "[6/9] Iniciando Frontend..." -ForegroundColor Cyan
docker-compose up -d frontend
Start-Sleep -Seconds 12

# Iniciar Nginx Proxy
Write-Host "[7/9] Iniciando Nginx Proxy..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d nginx-proxy
Start-Sleep -Seconds 5

# Iniciar ngrok
Write-Host "[8/9] Iniciando ngrok..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d ngrok
Start-Sleep -Seconds 20

# Obter URL do ngrok
Write-Host "[9/9] Obtendo URL publica..." -ForegroundColor Cyan
$ngrokUrl = $null

for ($i = 1; $i -le 15; $i++) {
    try {
        $api = Invoke-RestMethod "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($api.tunnels.Count -gt 0) {
            $ngrokUrl = $api.tunnels[0].public_url
            break
        }
    } catch {}
    
    Write-Host "   Tentativa $i/15..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $ngrokUrl) {
    Write-Host ""
    Write-Host "[ERRO] Nao foi possivel obter URL do ngrok!" -ForegroundColor Red
    Write-Host ""
    Write-Host "[DEBUG] Verifique:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs ngrok" -ForegroundColor Gray
    Write-Host "   docker-compose ps" -ForegroundColor Gray
    Write-Host "   http://localhost:4040" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  URL OBTIDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "   $ngrokUrl" -ForegroundColor White
Write-Host ""

# Configurar Frontend
Write-Host "[CONFIG] Configurando Frontend..." -ForegroundColor Cyan
Set-Content -Path "frontend\.env.local" -Value "NEXT_PUBLIC_API_URL=$ngrokUrl/api/v1"

# Configurar Backend
Write-Host "[CONFIG] Configurando Backend..." -ForegroundColor Cyan
$backendEnv = Get-Content "backend\.env.docker" -Raw

if ($backendEnv -match "CORS_ORIGINS=.*") {
    $backendEnv = $backendEnv -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=$ngrokUrl,http://localhost:3000"
} else {
    $backendEnv += "`nCORS_ORIGINS=$ngrokUrl,http://localhost:3000"
}

if ($backendEnv -match "FRONTEND_URL=.*") {
    $backendEnv = $backendEnv -replace "FRONTEND_URL=.*", "FRONTEND_URL=$ngrokUrl"
} else {
    $backendEnv += "`nFRONTEND_URL=$ngrokUrl"
}

$backendEnv = $backendEnv -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=True"
$backendEnv = $backendEnv -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$backendEnv = $backendEnv -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="

Set-Content -Path "backend\.env.docker" -Value $backendEnv

Write-Host "[RESTART] Aplicando configuracoes..." -ForegroundColor Cyan
docker-compose restart backend frontend
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  TESTANDO SISTEMA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Teste 1: Frontend
Write-Host "[TEST 1/3] Frontend..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri $ngrokUrl -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] Status: $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 2: Backend Health
Write-Host "[TEST 2/3] Backend Health..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri "$ngrokUrl/health" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] Status: $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 3: Login API
Write-Host "[TEST 3/3] Login API..." -ForegroundColor Cyan
try {
    $body = @{
        email = "admin@hotelreal.com.br"
        password = "admin123"
    } | ConvertTo-Json

    $r = Invoke-WebRequest -Uri "$ngrokUrl/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] Status: $($r.StatusCode)" -ForegroundColor Green
    
    $loginData = $r.Content | ConvertFrom-Json
    if ($loginData.access_token) {
        Write-Host "[OK] JWT Token gerado com sucesso!" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[COMPARTILHE]" -ForegroundColor Cyan
Write-Host ""
Write-Host "   URL: $ngrokUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN]" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[ARQUITETURA]" -ForegroundColor Cyan
Write-Host "   - 1 tunel ngrok (FREE plan)" -ForegroundColor Gray
Write-Host "   - Nginx proxy reverso interno" -ForegroundColor Gray
Write-Host "   - Frontend: $ngrokUrl" -ForegroundColor Gray
Write-Host "   - Backend API: $ngrokUrl/api/v1" -ForegroundColor Gray
Write-Host "   - Backend Health: $ngrokUrl/health" -ForegroundColor Gray
Write-Host ""
Write-Host "[DASHBOARD]" -ForegroundColor Cyan
Write-Host "   ngrok: http://localhost:4040" -ForegroundColor Gray
Write-Host "   Proxy local: http://localhost:8080" -ForegroundColor Gray
Write-Host ""
Write-Host "[LOGS]" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f" -ForegroundColor Gray
Write-Host "   docker-compose logs -f ngrok" -ForegroundColor Gray
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "[DADOS]" -ForegroundColor Green
Write-Host "   Banco de dados preservado!" -ForegroundColor Gray
Write-Host "   Todos os dados foram mantidos" -ForegroundColor Gray
Write-Host ""
