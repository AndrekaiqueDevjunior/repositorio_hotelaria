# Teste de acesso ao frontend após restart
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8080' -UseBasicParsing -TimeoutSec 10
    Write-Host 'Frontend acessivel - Status:' $response.StatusCode
    Write-Host 'Content-Type:' $response.Headers['Content-Type']
    Write-Host 'Tamanho:' $response.Content.Length 'bytes'
} catch {
    Write-Host 'Erro ao acessar frontend:' $_.Exception.Message
    Write-Host 'Status Code:' $_.Exception.Response.StatusCode
}
