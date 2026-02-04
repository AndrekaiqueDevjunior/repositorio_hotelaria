# ============================================================
# Script PowerShell - Iniciar Sistema com Docker
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HOTEL CABO FRIO - DOCKER SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker esta instalado
Write-Host "Verificando Docker..." -ForegroundColor Yellow
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue

if (-not $dockerInstalled) {
    Write-Host "ERRO: Docker nao encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, instale o Docker Desktop:" -ForegroundColor White
    Write-Host "  https://www.docker.com/products/docker-desktop" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "OK Docker encontrado!" -ForegroundColor Green
Write-Host ""

# Verificar se Docker esta rodando
Write-Host "Verificando se Docker esta rodando..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "OK Docker esta rodando!" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Docker nao esta rodando!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, inicie o Docker Desktop e tente novamente." -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host ""

# Verificar se arquivo .env existe
if (-not (Test-Path ".env")) {
    Write-Host "Arquivo .env nao encontrado!" -ForegroundColor Yellow
    Write-Host "Criando .env a partir do exemplo..." -ForegroundColor Gray
    
    if (Test-Path "env.docker.example") {
        Copy-Item "env.docker.example" ".env"
        Write-Host "OK Arquivo .env criado!" -ForegroundColor Green
        Write-Host ""
        Write-Host "IMPORTANTE: Edite o arquivo .env com suas configuracoes!" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "ERRO: Arquivo env.docker.example nao encontrado!" -ForegroundColor Red
        exit 1
    }
}

# Menu de opcoes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ESCOLHA UMA OPCAO:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Iniciar sistema completo (Backend + Frontend + PostgreSQL)" -ForegroundColor White
Write-Host "2. Iniciar com pgAdmin (gerenciamento de banco)" -ForegroundColor White
Write-Host "3. Parar todos os containers" -ForegroundColor White
Write-Host "4. Reiniciar sistema" -ForegroundColor White
Write-Host "5. Ver logs" -ForegroundColor White
Write-Host "6. Limpar tudo (CUIDADO: remove volumes!)" -ForegroundColor White
Write-Host "7. Status dos containers" -ForegroundColor White
Write-Host "0. Sair" -ForegroundColor White
Write-Host ""

$opcao = Read-Host "Digite o numero da opcao"

switch ($opcao) {
    "1" {
        Write-Host ""
        Write-Host "Iniciando sistema completo..." -ForegroundColor Yellow
        Write-Host ""
        docker-compose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Acessos:" -ForegroundColor Yellow
            Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
            Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
            Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
            Write-Host "  PostgreSQL: localhost:5432" -ForegroundColor White
            Write-Host ""
            Write-Host "Para ver os logs:" -ForegroundColor Gray
            Write-Host "  docker-compose logs -f" -ForegroundColor Gray
            Write-Host ""
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "Iniciando sistema com pgAdmin..." -ForegroundColor Yellow
        Write-Host ""
        docker-compose --profile tools up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Acessos:" -ForegroundColor Yellow
            Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
            Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
            Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
            Write-Host "  pgAdmin:   http://localhost:5050" -ForegroundColor White
            Write-Host "  PostgreSQL: localhost:5432" -ForegroundColor White
            Write-Host ""
            Write-Host "Credenciais pgAdmin:" -ForegroundColor Yellow
            Write-Host "  Email:    admin@hotel.com" -ForegroundColor Gray
            Write-Host "  Senha:    admin123" -ForegroundColor Gray
            Write-Host ""
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "Parando todos os containers..." -ForegroundColor Yellow
        docker-compose down
        Write-Host ""
        Write-Host "OK Containers parados!" -ForegroundColor Green
        Write-Host ""
    }
    
    "4" {
        Write-Host ""
        Write-Host "Reiniciando sistema..." -ForegroundColor Yellow
        docker-compose restart
        Write-Host ""
        Write-Host "OK Sistema reiniciado!" -ForegroundColor Green
        Write-Host ""
    }
    
    "5" {
        Write-Host ""
        Write-Host "Exibindo logs (Ctrl+C para sair)..." -ForegroundColor Yellow
        Write-Host ""
        docker-compose logs -f
    }
    
    "6" {
        Write-Host ""
        Write-Host "ATENCAO: Esta operacao vai remover TODOS os dados!" -ForegroundColor Red
        $confirma = Read-Host "Tem certeza? (digite SIM para confirmar)"
        
        if ($confirma -eq "SIM") {
            Write-Host ""
            Write-Host "Removendo containers, volumes e imagens..." -ForegroundColor Yellow
            docker-compose down -v --rmi all
            Write-Host ""
            Write-Host "OK Tudo removido!" -ForegroundColor Green
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "Operacao cancelada." -ForegroundColor Gray
            Write-Host ""
        }
    }
    
    "7" {
        Write-Host ""
        Write-Host "Status dos containers:" -ForegroundColor Yellow
        Write-Host ""
        docker-compose ps
        Write-Host ""
    }
    
    "0" {
        Write-Host ""
        Write-Host "Saindo..." -ForegroundColor Gray
        Write-Host ""
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "Opcao invalida!" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host ""
Write-Host "Pressione qualquer tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
