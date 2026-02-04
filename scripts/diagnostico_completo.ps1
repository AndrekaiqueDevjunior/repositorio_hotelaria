# Script de Diagnóstico Completo

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   DIAGNOSTICO COMPLETO DO SISTEMA" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Processos Cloudflare
Write-Host "[1/7] Processos Cloudflare Tunnel..." -ForegroundColor Cyan
$cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflared) {
    Write-Host "   [INFO] $($cloudflared.Count) processo(s) encontrado(s)" -ForegroundColor Yellow
    $cloudflared | ForEach-Object {
        Write-Host "      PID: $($_.Id) - Iniciado: $($_.StartTime)" -ForegroundColor White
    }
    Write-Host "   [AVISO] Deve haver apenas 1 processo!" -ForegroundColor Yellow
} else {
    Write-Host "   [OK] Nenhum processo encontrado" -ForegroundColor Green
}
Write-Host ""

# 2. Proxy
Write-Host "[2/7] Proxy (porta 8080)..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   [OK] Proxy respondendo (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Proxy NAO responde" -ForegroundColor Red
    Write-Host "      Erro: $($_.Exception.Message)" -ForegroundColor Yellow
    
    # Verificar se há processo na porta
    $conn = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        Write-Host "      [INFO] Porta 8080 ocupada por PID: $($conn.OwningProcess)" -ForegroundColor Yellow
    } else {
        Write-Host "      [INFO] Porta 8080 livre (nenhum processo)" -ForegroundColor Yellow
    }
}
Write-Host ""

# 3. Backend
Write-Host "[3/7] Backend (porta 8000)..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   [OK] Backend respondendo (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Backend NAO responde" -ForegroundColor Red
    Write-Host "      Erro: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Frontend
Write-Host "[4/7] Frontend (porta 3000)..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   [OK] Frontend respondendo (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Frontend NAO responde" -ForegroundColor Red
    Write-Host "      Erro: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Arquivo .env.local
Write-Host "[5/7] Configuracao frontend/.env.local..." -ForegroundColor Cyan
if (Test-Path "frontend\.env.local") {
    $envContent = Get-Content "frontend\.env.local" -Raw
    Write-Host "   [OK] Arquivo existe" -ForegroundColor Green
    
    if ($envContent -match "NEXT_PUBLIC_API_URL\s*=\s*(.+)") {
        $apiUrl = $matches[1].Trim()
        Write-Host "   URL configurada: $apiUrl" -ForegroundColor Cyan
        
        # Verificar se é URL única ou múltiplas
        if ($apiUrl -match "trycloudflare\.com") {
            Write-Host "   [OK] URL Cloudflare configurada" -ForegroundColor Green
        } else {
            Write-Host "   [AVISO] URL nao parece ser Cloudflare Tunnel" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   [ERRO] NEXT_PUBLIC_API_URL nao encontrado no arquivo" -ForegroundColor Red
    }
} else {
    Write-Host "   [ERRO] Arquivo nao existe!" -ForegroundColor Red
    Write-Host "      Crie: frontend\.env.local" -ForegroundColor Yellow
}
Write-Host ""

# 6. Portas em uso
Write-Host "[6/7] Portas em uso..." -ForegroundColor Cyan
$ports = @(
    @{Port=8000; Name="Backend"},
    @{Port=3000; Name="Frontend"},
    @{Port=8080; Name="Proxy"}
)
foreach ($p in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $p.Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        $procName = if ($proc) { $proc.ProcessName } else { "Desconhecido" }
        Write-Host "   Porta $($p.Port) ($($p.Name)): $($conn.State) - $procName (PID: $($conn.OwningProcess))" -ForegroundColor White
    } else {
        Write-Host "   Porta $($p.Port) ($($p.Name)): Livre" -ForegroundColor Gray
    }
}
Write-Host ""

# 7. Resumo e recomendações
Write-Host "[7/7] Resumo e Recomendacoes..." -ForegroundColor Cyan
Write-Host ""

$issues = @()

if (-not (Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue)) {
    $issues += "Nenhum Cloudflare Tunnel rodando"
}

try {
    Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 2 -ErrorAction Stop | Out-Null
} catch {
    $issues += "Proxy nao esta respondendo"
}

try {
    Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop | Out-Null
} catch {
    $issues += "Backend nao esta respondendo"
}

try {
    Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop | Out-Null
} catch {
    $issues += "Frontend nao esta respondendo"
}

if (-not (Test-Path "frontend\.env.local")) {
    $issues += "Arquivo frontend/.env.local nao existe"
}

if ($issues.Count -eq 0) {
    Write-Host "   [OK] Tudo parece estar funcionando!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Se ainda houver problemas:" -ForegroundColor Yellow
    Write-Host "   1. Verifique os logs dos terminais" -ForegroundColor White
    Write-Host "   2. Teste a URL do Cloudflare Tunnel diretamente" -ForegroundColor White
    Write-Host "   3. Verifique o console do navegador (F12)" -ForegroundColor White
} else {
    Write-Host "   [ERRO] Problemas encontrados:" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "      - $issue" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "   SOLUCAO RECOMENDADA:" -ForegroundColor Cyan
    Write-Host "      Execute: .\iniciar_tudo_automatico.ps1" -ForegroundColor White
    Write-Host "      Isso vai reiniciar tudo na ordem correta" -ForegroundColor Gray
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan

