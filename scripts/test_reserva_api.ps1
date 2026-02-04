# Test script for reservation API
$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    nome_completo = "João Silva Teste"
    documento = "12345678901"
    email = "joao.teste@email.com"
    telefone = "22999887766"
    quarto_numero = "101"
    tipo_suite = "DUPLA"
    data_checkin = "2026-01-25"
    data_checkout = "2026-01-27"
    num_hospedes = 2
    num_criancas = 0
    observacoes = "Teste de reserva via API"
    metodo_pagamento = "na_chegada"
} | ConvertTo-Json

Write-Host "Testing reservation API..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:8080/api/v1/public/reservas" -ForegroundColor Yellow
Write-Host "Body: $body" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/public/reservas" -Method POST -Headers $headers -Body $body
    Write-Host "`nSuccess!" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 10)
} catch {
    Write-Host "`nError!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error Message: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
