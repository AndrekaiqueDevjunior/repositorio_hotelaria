# Script de Teste de Autenticacao via Ngrok
# Uso: .\TESTAR_AUTENTICACAO_NGROK.ps1 -BackendUrl "https://abc123.ngrok-free.app"

param(
    [Parameter(Mandatory=$false)]
    [string]$BackendUrl = ""
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TESTE DE AUTENTICACAO NGROK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Detectar URL do backend automaticamente se nao fornecida
if (-not $BackendUrl) {
    try {
        $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
        foreach ($tunnel in $tunnels.tunnels) {
            $port = $tunnel.config.addr -replace ".*:", ""
            if ($port -eq "8000") {
                $BackendUrl = $tunnel.public_url
                Write-Host "[INFO] Backend detectado: $BackendUrl" -ForegroundColor Green
                break
            }
        }
    } catch {
        Write-Host "[ERRO] Nao foi possivel detectar URL do backend" -ForegroundColor Red
        Write-Host "[INFO] Execute: .\TESTAR_AUTENTICACAO_NGROK.ps1 -BackendUrl 'https://sua-url.ngrok-free.app'" -ForegroundColor Cyan
        exit 1
    }
}

if (-not $BackendUrl) {
    Write-Host "[ERRO] URL do backend nao fornecida" -ForegroundColor Red
    exit 1
}

# Credenciais de teste
$email = "admin@hotelreal.com.br"
$password = "admin123"

# 1. Teste de Health Check
Write-Host "[1] Testando Health Check..." -ForegroundColor Yellow

try {
    $health = Invoke-RestMethod -Uri "$BackendUrl/health" -Method GET -Headers @{
        "ngrok-skip-browser-warning" = "true"
    }
    Write-Host "[OK] Backend respondendo: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Health check falhou: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Teste de Login
Write-Host "`n[2] Testando Login..." -ForegroundColor Yellow

$loginBody = @{
    email = $email
    password = $password
} | ConvertTo-Json

try {
    # PowerShell nao suporta cookies automaticamente como browser
    # Vamos testar apenas se o endpoint responde
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    
    $loginResponse = Invoke-WebRequest `
        -Uri "$BackendUrl/api/v1/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json" `
        -WebSession $session `
        -Headers @{
            "ngrok-skip-browser-warning" = "true"
        }
    
    $loginData = $loginResponse.Content | ConvertFrom-Json
    
    if ($loginData.success) {
        Write-Host "[OK] Login bem-sucedido!" -ForegroundColor Green
        Write-Host "[INFO] Usuario: $($loginData.user.nome)" -ForegroundColor White
        Write-Host "[INFO] Perfil: $($loginData.user.perfil)" -ForegroundColor White
        Write-Host "[INFO] Token Type: $($loginData.token_type)" -ForegroundColor White
        
        # Verificar se cookie foi definido
        $cookies = $session.Cookies.GetCookies("$BackendUrl")
        if ($cookies.Count -gt 0) {
            Write-Host "[OK] Cookie recebido:" -ForegroundColor Green
            foreach ($cookie in $cookies) {
                Write-Host "  Nome: $($cookie.Name)" -ForegroundColor White
                Write-Host "  Secure: $($cookie.Secure)" -ForegroundColor White
                Write-Host "  HttpOnly: $($cookie.HttpOnly)" -ForegroundColor White
            }
        } else {
            Write-Host "[AVISO] Nenhum cookie recebido (normal em PowerShell)" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "[ERRO] Login falhou: $($loginData.message)" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "[ERRO] Login falhou: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "[DETALHES] $responseBody" -ForegroundColor Gray
    }
    
    exit 1
}

# 3. Teste de Endpoint Protegido (usando refresh_token como Bearer)
Write-Host "`n[3] Testando Endpoint Protegido..." -ForegroundColor Yellow

if ($loginData.refresh_token) {
    try {
        $meResponse = Invoke-RestMethod `
            -Uri "$BackendUrl/api/v1/me" `
            -Method GET `
            -Headers @{
                "Authorization" = "Bearer $($loginData.refresh_token)"
                "ngrok-skip-browser-warning" = "true"
            }
        
        Write-Host "[OK] Endpoint /me respondeu:" -ForegroundColor Green
        Write-Host "  ID: $($meResponse.id)" -ForegroundColor White
        Write-Host "  Nome: $($meResponse.nome)" -ForegroundColor White
        Write-Host "  Email: $($meResponse.email)" -ForegroundColor White
        
    } catch {
        Write-Host "[AVISO] Endpoint /me falhou (esperado em PowerShell - use browser)" -ForegroundColor Yellow
    }
}

# 4. Teste de CORS (Preflight)
Write-Host "`n[4] Testando CORS (Preflight)..." -ForegroundColor Yellow

try {
    $corsResponse = Invoke-WebRequest `
        -Uri "$BackendUrl/api/v1/login" `
        -Method OPTIONS `
        -Headers @{
            "Origin" = "https://frontend-test.ngrok-free.app"
            "Access-Control-Request-Method" = "POST"
            "Access-Control-Request-Headers" = "Content-Type,Authorization"
            "ngrok-skip-browser-warning" = "true"
        }
    
    $allowOrigin = $corsResponse.Headers["Access-Control-Allow-Origin"]
    $allowCredentials = $corsResponse.Headers["Access-Control-Allow-Credentials"]
    $allowMethods = $corsResponse.Headers["Access-Control-Allow-Methods"]
    
    Write-Host "[OK] CORS Preflight respondeu:" -ForegroundColor Green
    Write-Host "  Allow-Origin: $allowOrigin" -ForegroundColor White
    Write-Host "  Allow-Credentials: $allowCredentials" -ForegroundColor White
    Write-Host "  Allow-Methods: $allowMethods" -ForegroundColor White
    
    if ($allowCredentials -eq "true") {
        Write-Host "[OK] Credentials habilitados (cookies funcionarao)" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] Credentials nao habilitados!" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "[AVISO] CORS Preflight falhou: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 5. Resumo
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESUMO DOS TESTES" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "[INFO] Testes realizados via PowerShell (limitado)" -ForegroundColor Yellow
Write-Host "[INFO] Para teste completo, use o browser:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Abra o DevTools (F12)" -ForegroundColor White
Write-Host "2. Va para a aba Network" -ForegroundColor White
Write-Host "3. Acesse a URL do frontend ngrok" -ForegroundColor White
Write-Host "4. Faca login com:" -ForegroundColor White
Write-Host "   Email: $email" -ForegroundColor Gray
Write-Host "   Senha: $password" -ForegroundColor Gray
Write-Host "5. Verifique:" -ForegroundColor White
Write-Host "   - Cookie 'hotel_auth_token' criado (Application > Cookies)" -ForegroundColor Gray
Write-Host "   - Sem erros de CORS no console" -ForegroundColor Gray
Write-Host "   - Dashboard carrega corretamente" -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
