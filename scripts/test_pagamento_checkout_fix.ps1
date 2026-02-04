# Teste de Pagamento para Reserva CHECKED_OUT
$BASE_URL = "http://localhost:8080"
$AUTH_EMAIL = "admin@hotelreal.com.br"
$AUTH_PASSWORD = "admin123"

Write-Host "Teste: Pagamento para Reserva CHECKED_OUT" -ForegroundColor Cyan
Write-Host "=========================================="

# 1. Login
try {
    $loginData = @{email = $AUTH_EMAIL; password = $AUTH_PASSWORD} | ConvertTo-Json
    $loginResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/login" -Method Post -ContentType "application/json" -Body $loginData -ErrorAction Stop
    
    if ($loginResponse.refresh_token) {
        $refreshData = @{refresh_token = $loginResponse.refresh_token} | ConvertTo-Json
        $refreshResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/refresh" -Method Post -ContentType "application/json" -Body $refreshData -ErrorAction Stop
        
        if ($refreshResponse.access_token) {
            $TOKEN = $refreshResponse.access_token
            Write-Host "Login bem-sucedido" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "Falha no login: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Listar reservas para encontrar uma CHECKED_OUT
Write-Host "`nBuscando reservas CHECKED_OUT..." -ForegroundColor Yellow
try {
    $headers = @{Authorization = "Bearer $TOKEN"}
    $reservasResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/reservas" -Method Get -Headers $headers -ErrorAction Stop
    
    $reservas = $reservasResponse.reservas
    $checkedOutReservas = $reservas | Where-Object { $_.status -eq "CHECKED_OUT" }
    
    Write-Host "Total de reservas: $($reservas.Count)" -ForegroundColor Blue
    Write-Host "Reservas CHECKED_OUT: $($checkedOutReservas.Count)" -ForegroundColor Yellow
    
    if ($checkedOutReservas.Count -gt 0) {
        $reservaTeste = $checkedOutReservas[0]
        Write-Host "Reserva encontrada: ID $($reservaTeste.id) - Status $($reservaTeste.status)" -ForegroundColor Green
        
        # 3. Tentar criar pagamento para reserva CHECKED_OUT
        Write-Host "`nTentando criar pagamento para reserva CHECKED_OUT..." -ForegroundColor Yellow
        
        $pagamentoData = @{
            reserva_id = $reservaTeste.id
            cliente_id = $reservaTeste.cliente_id
            metodo = "CREDITO"
            valor = 100.00
            observacao = "Teste pagamento reserva CHECKED_OUT"
        } | ConvertTo-Json
        
        try {
            $pagamentoResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/pagamentos" -Method Post -ContentType "application/json" -Headers $headers -Body $pagamentoData -ErrorAction Stop
            Write-Host "ERRO: Pagamento criado (nao deveria!)" -ForegroundColor Red
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            $errorBody = $_.Exception.Response.GetResponseStream() | Out-String | ConvertFrom-Json
            
            if ($status -eq 400 -and $errorBody.detail -like "*CHECKED_OUT*") {
                Write-Host "SUCESSO: Validacao funcionando!" -ForegroundColor Green
                Write-Host "Status: $status" -ForegroundColor Green
                Write-Host "Mensagem: $($errorBody.detail)" -ForegroundColor Green
            } else {
                Write-Host "Status inesperado: $status" -ForegroundColor Yellow
                Write-Host "Mensagem: $($errorBody.detail)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "Nenhuma reserva CHECKED_OUT encontrada" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Erro ao listar reservas: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTeste concluido" -ForegroundColor Blue
