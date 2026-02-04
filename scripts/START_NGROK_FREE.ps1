# =========================================
# START NGROK FREE - Sistema Completo
# =========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NGROK FREE - SETUP FINAL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/10] Rebuild Backend..." -ForegroundColor Cyan
docker-compose build --no-cache backend

Write-Host ""
Write-Host "[2/10] Rebuild Frontend..." -ForegroundColor Cyan
docker-compose build --no-cache frontend

Write-Host ""
Write-Host "[3/10] PostgreSQL..." -ForegroundColor Cyan
docker-compose up -d postgres
Start-Sleep -Seconds 10

Write-Host "[4/10] Redis..." -ForegroundColor Cyan
docker-compose up -d redis
Start-Sleep -Seconds 5

Write-Host "[5/10] Backend..." -ForegroundColor Cyan
docker-compose up -d backend
Start-Sleep -Seconds 12

Write-Host "[6/10] Frontend..." -ForegroundColor Cyan
docker-compose up -d frontend
Start-Sleep -Seconds 12

Write-Host "[7/10] Nginx Proxy..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d nginx-proxy
Start-Sleep -Seconds 5

Write-Host "[8/10] ngrok..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d ngrok
Start-Sleep -Seconds 20

Write-Host "[9/10] Obtendo URL..." -ForegroundColor Cyan
$url = $null
for ($i = 1; $i -le 15; $i++) {
    try {
        $api = Invoke-RestMethod "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($api.tunnels.Count -gt 0) {
            $url = $api.tunnels[0].public_url
            break
        }
    } catch {}
    Write-Host "   $i/15..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $url) {
    Write-Host ""
    Write-Host "[ERRO] Ngrok nao iniciou!" -ForegroundColor Red
    Write-Host "Verifique: docker-compose logs ngrok" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[URL] $url" -ForegroundColor Green
Write-Host ""

Write-Host "[10/10] Configurando..." -ForegroundColor Cyan
Set-Content "frontend\.env.local" "NEXT_PUBLIC_API_URL=$url/api/v1"

$be = Get-Content "backend\.env.docker" -Raw
$be = $be -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=$url,http://localhost:3000"
$be = $be -replace "FRONTEND_URL=.*", "FRONTEND_URL=$url"
$be = $be -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=True"
$be = $be -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$be = $be -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="
Set-Content "backend\.env.docker" $be

docker-compose restart backend frontend
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  TESTANDO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "[1/3] Frontend..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] $($r.StatusCode)" -ForegroundColor Green
} catch { Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red }

Write-Host "[2/3] Health..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest "$url/health" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] $($r.StatusCode)" -ForegroundColor Green
} catch { Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red }

Write-Host "[3/3] Login..." -ForegroundColor Cyan
try {
    $b = @{email="admin@hotelreal.com.br";password="admin123"} | ConvertTo-Json
    $r = Invoke-WebRequest "$url/api/v1/auth/login" -Method POST -Body $b -ContentType "application/json" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] $($r.StatusCode) - Token OK!" -ForegroundColor Green
} catch { Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red }

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  PRONTO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "URL: $url" -ForegroundColor White
Write-Host "Login: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Arquitetura:" -ForegroundColor Cyan
Write-Host "  - 1 tunel ngrok (FREE)" -ForegroundColor Gray
Write-Host "  - Frontend: $url" -ForegroundColor Gray
Write-Host "  - Backend: $url/api/v1" -ForegroundColor Gray
Write-Host ""
Write-Host "Dashboard: http://localhost:4040" -ForegroundColor Cyan
Write-Host "Dados: Preservados!" -ForegroundColor Green
Write-Host ""
