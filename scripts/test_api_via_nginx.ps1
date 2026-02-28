# Teste de API via nginx
try {
    $response = Invoke-RestMethod -Uri 'http://localhost:8080/api/v1/dashboard/stats' -Method Get -TimeoutSec 10
    Write-Host 'API via nginx funcionando'
    Write-Host 'Response type:' $response.GetType().Name
} catch {
    Write-Host 'Erro API via nginx:' $_.Exception.Message
    $status = $_.Exception.Response.StatusCode
    Write-Host 'Status Code:' $status
}
