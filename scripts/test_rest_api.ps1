# Script de Testes QA - Validação de Rotas REST
# Testa todas as rotas refatoradas para conformidade REST

$BASE_URL = "http://localhost:8000/api/v1"
$TOKEN = $null

function Write-TestResult {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details = ""
    )
    
    if ($Passed) {
        Write-Host "✅ PASS | $Name" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL | $Name" -ForegroundColor Red
        if ($Details) {
            Write-Host "     └─ $Details" -ForegroundColor Yellow
        }
    }
}

# Login
Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "  TESTES DE QA - VALIDAÇÃO REST API" -ForegroundColor Blue
Write-Host "============================================================`n" -ForegroundColor Blue

try {
    $loginResponse = Invoke-WebRequest -Uri "$BASE_URL/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"email":"admin@hotel.com","password":"admin123"}' `
        -ErrorAction SilentlyContinue
    
    if ($loginResponse.StatusCode -eq 200) {
        $TOKEN = ($loginResponse.Content | ConvertFrom-Json).access_token
        Write-TestResult "Login de autenticação" $true
    } else {
        Write-TestResult "Login de autenticação" $false "Status: $($loginResponse.StatusCode)"
        Write-Host "`n❌ Falha no login. Continuando sem autenticação...`n" -ForegroundColor Red
    }
} catch {
    Write-TestResult "Login de autenticação" $false "Erro: $_"
    Write-Host "`n⚠️ Continuando testes sem autenticação...`n" -ForegroundColor Yellow
}

$headers = @{}
if ($TOKEN) {
    $headers["Authorization"] = "Bearer $TOKEN"
}

# ============================================================
# TESTES DE CLIENTES
# ============================================================
Write-Host "`n=== TESTES: CLIENTES ===" -ForegroundColor Blue

try {
    $r = Invoke-WebRequest -Uri "$BASE_URL/clientes" -Method GET -Headers $headers -ErrorAction SilentlyContinue
    Write-TestResult "GET /clientes" ($r.StatusCode -eq 200) "Status: $($r.StatusCode)"
} catch {
    Write-TestResult "GET /clientes" $false "Erro: $($_.Exception.Message)"
}

try {
    $r = Invoke-WebRequest -Uri "$BASE_URL/clientes/999/" -Method DELETE -Headers $headers -ErrorAction SilentlyContinue
    Write-TestResult "DELETE /clientes/{id}/ (CORS)" ($r.StatusCode -in @(404, 200)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "DELETE /clientes/{id}/ (CORS)" ($statusCode -in @(404, 200)) "Status: $statusCode"
}

# ============================================================
# TESTES DE RESERVAS (REST-compliant)
# ============================================================
Write-Host "`n=== TESTES: RESERVAS (REST-compliant) ===" -ForegroundColor Blue

try {
    $r = Invoke-WebRequest -Uri "$BASE_URL/reservas" -Method GET -Headers $headers -ErrorAction SilentlyContinue
    Write-TestResult "GET /reservas" ($r.StatusCode -eq 200) "Status: $($r.StatusCode)"
} catch {
    Write-TestResult "GET /reservas" $false "Erro: $($_.Exception.Message)"
}

$statusTests = @(
    @{Status="CHECKED_IN"; Desc="Check-in via PATCH"},
    @{Status="CHECKED_OUT"; Desc="Check-out via PATCH"},
    @{Status="CANCELADO"; Desc="Cancelar via PATCH"},
    @{Status="CONFIRMADO"; Desc="Confirmar via PATCH"}
)

foreach ($test in $statusTests) {
    try {
        $body = @{status=$test.Status} | ConvertTo-Json
        $r = Invoke-WebRequest -Uri "$BASE_URL/reservas/999" `
            -Method PATCH `
            -Headers $headers `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction SilentlyContinue
        Write-TestResult "PATCH /reservas/{id} - $($test.Desc)" ($r.StatusCode -in @(404, 200)) "Status: $($r.StatusCode)"
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-TestResult "PATCH /reservas/{id} - $($test.Desc)" ($statusCode -in @(404, 200)) "Status: $statusCode"
    }
}

# Testar rota deprecated
try {
    $r = Invoke-WebRequest -Uri "$BASE_URL/reservas/999/checkin" -Method POST -Headers $headers -ErrorAction SilentlyContinue
    Write-TestResult "POST /reservas/{id}/checkin (deprecated)" ($r.StatusCode -in @(404, 200)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "POST /reservas/{id}/checkin (deprecated)" ($statusCode -in @(404, 200)) "Status: $statusCode"
}

# ============================================================
# TESTES DE PAGAMENTOS (REST-compliant)
# ============================================================
Write-Host "`n=== TESTES: PAGAMENTOS (REST-compliant) ===" -ForegroundColor Blue

try {
    $r = Invoke-WebRequest -Uri "$BASE_URL/pagamentos" -Method GET -Headers $headers -ErrorAction SilentlyContinue
    Write-TestResult "GET /pagamentos" ($r.StatusCode -eq 200) "Status: $($r.StatusCode)"
} catch {
    Write-TestResult "GET /pagamentos" $false "Erro: $($_.Exception.Message)"
}

try {
    $body = @{status="CANCELADO"} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$BASE_URL/pagamentos/999" `
        -Method PATCH `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction SilentlyContinue
    Write-TestResult "PATCH /pagamentos/{id} - Cancelar" ($r.StatusCode -in @(404, 200, 400)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "PATCH /pagamentos/{id} - Cancelar" ($statusCode -in @(404, 200, 400)) "Status: $statusCode"
}

# ============================================================
# TESTES DE PONTOS (REST-compliant)
# ============================================================
Write-Host "`n=== TESTES: PONTOS (REST-compliant) ===" -ForegroundColor Blue

try {
    $body = @{cliente_id=1; pontos=10; motivo="Teste QA"} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$BASE_URL/pontos/ajustes" `
        -Method POST `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction SilentlyContinue
    Write-TestResult "POST /pontos/ajustes" ($r.StatusCode -in @(200, 201, 404)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "POST /pontos/ajustes" ($statusCode -in @(200, 201, 404, 401)) "Status: $statusCode"
}

try {
    $body = @{reserva_id=1} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$BASE_URL/pontos/validacoes" `
        -Method POST `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction SilentlyContinue
    Write-TestResult "POST /pontos/validacoes" ($r.StatusCode -in @(200, 201, 404)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "POST /pontos/validacoes" ($statusCode -in @(200, 201, 404, 401)) "Status: $statusCode"
}

try {
    $body = @{cliente_id=1} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$BASE_URL/pontos/convites" `
        -Method POST `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction SilentlyContinue
    Write-TestResult "POST /pontos/convites" ($r.StatusCode -in @(200, 201, 404)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "POST /pontos/convites" ($statusCode -in @(200, 201, 404, 401)) "Status: $statusCode"
}

# ============================================================
# TESTES DE NOTIFICAÇÕES (REST-compliant)
# ============================================================
Write-Host "`n=== TESTES: NOTIFICAÇÕES (REST-compliant) ===" -ForegroundColor Blue

try {
    $r = Invoke-WebRequest -Uri "$BASE_URL/notificacoes" -Method GET -Headers $headers -ErrorAction SilentlyContinue
    Write-TestResult "GET /notificacoes" ($r.StatusCode -eq 200) "Status: $($r.StatusCode)"
} catch {
    Write-TestResult "GET /notificacoes" $false "Erro: $($_.Exception.Message)"
}

try {
    $body = @{lida=$true} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$BASE_URL/notificacoes/999" `
        -Method PATCH `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction SilentlyContinue
    Write-TestResult "PATCH /notificacoes/{id}" ($r.StatusCode -in @(200, 404)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "PATCH /notificacoes/{id}" ($statusCode -in @(200, 404)) "Status: $statusCode"
}

try {
    $body = @{lida=$true} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$BASE_URL/notificacoes" `
        -Method PATCH `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction SilentlyContinue
    Write-TestResult "PATCH /notificacoes (lote)" ($r.StatusCode -eq 200) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "PATCH /notificacoes (lote)" ($statusCode -eq 200) "Status: $statusCode"
}

# ============================================================
# TESTES DE ANTIFRAUDE (REST-compliant)
# ============================================================
Write-Host "`n=== TESTES: ANTIFRAUDE (REST-compliant) ===" -ForegroundColor Blue

try {
    $r = Invoke-WebRequest -Uri "$BASE_URL/antifraude/operacoes" -Method GET -Headers $headers -ErrorAction SilentlyContinue
    Write-TestResult "GET /antifraude/operacoes" ($r.StatusCode -eq 200) "Status: $($r.StatusCode)"
} catch {
    Write-TestResult "GET /antifraude/operacoes" $false "Erro: $($_.Exception.Message)"
}

try {
    $body = @{status="APROVADO"} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$BASE_URL/antifraude/operacoes/999" `
        -Method PATCH `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction SilentlyContinue
    Write-TestResult "PATCH /antifraude/operacoes/{id} - Aprovar" ($r.StatusCode -in @(200, 404)) "Status: $($r.StatusCode)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-TestResult "PATCH /antifraude/operacoes/{id} - Aprovar" ($statusCode -in @(200, 404)) "Status: $statusCode"
}

Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "✅ Testes de QA concluídos" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Blue
