# Teste de acesso à página de login
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8080/login' -UseBasicParsing -TimeoutSec 10
    Write-Host 'Pagina login acessivel - Status:' $response.StatusCode
    Write-Host 'Content-Type:' $response.Headers['Content-Type']
    
    # Verificar se contém elementos de login
    $content = $response.Content
    if ($content -like '*email*' -and $content -like '*password*') {
        Write-Host 'Formulario de login encontrado'
    } else {
        Write-Host 'Formulario de login nao encontrado'
    }
} catch {
    Write-Host 'Erro ao acessar pagina de login:' $_.Exception.Message
}
