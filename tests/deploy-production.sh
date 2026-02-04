#!/bin/bash
# ============================================================
# SCRIPT DE DEPLOY PRODUÇÃO - HOTEL CABO FRIO
# ============================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificações pré-deploy
check_prerequisites() {
    log_info "Verificando pré-requisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker não encontrado. Instale Docker primeiro."
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose não encontrado. Instale Docker Compose primeiro."
        exit 1
    fi
    
    # Verificar arquivo .env.production
    if [ ! -f ".env.production" ]; then
        log_error "Arquivo .env.production não encontrado!"
        log_info "Copie .env.example para .env.production e configure as variáveis."
        exit 1
    fi
    
    # Verificar certificados SSL
    if [ ! -d "nginx/ssl" ]; then
        log_warning "Diretório nginx/ssl não encontrado!"
        log_info "Crie o diretório e adicione os certificados SSL:"
        log_info "  - nginx/ssl/cert.pem"
        log_info "  - nginx/ssl/key.pem"
        read -p "Deseja continuar sem SSL? (s/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "Pré-requisitos verificados!"
}

# Backup do estado atual
backup_current() {
    log_info "Fazendo backup do estado atual..."
    
    # Criar diretório de backup se não existir
    mkdir -p backup/pre-deploy
    
    # Backup do banco atual
    if docker-compose ps postgres | grep -q "Up"; then
        log_info "Backup do banco de dados atual..."
        docker-compose exec postgres pg_dump -U postgres hotel_cabo_frio > backup/pre-deploy/db_backup_$(date +%Y%m%d_%H%M%S).sql
        log_success "Backup do banco concluído"
    fi
    
    # Backup das imagens
    log_info "Salvando configurações atuais..."
    cp docker-compose.yml backup/pre-deploy/docker-compose.backup.yml
    cp .env backup/pre-deploy/.env.backup
    
    log_success "Backup concluído!"
}

# Build das imagens
build_images() {
    log_info "Construindo imagens Docker..."
    
    # Build backend
    log_info "Build backend..."
    docker-compose -f docker-compose.production.yml build --no-cache backend
    
    # Build frontend  
    log_info "Build frontend..."
    docker-compose -f docker-compose.production.yml build --no-cache frontend
    
    # Build celery
    log_info "Build celery worker..."
    docker-compose -f docker-compose.production.yml build --no-cache celery_worker
    
    log_success "Imagens construídas!"
}

# Deploy dos serviços
deploy_services() {
    log_info "Iniciando deploy dos serviços..."
    
    # Parar serviços atuais se existirem
    if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
        log_info "Parando serviços atuais..."
        docker-compose -f docker-compose.production.yml down
    fi
    
    # Iniciar serviços em ordem
    log_info "Iniciando banco de dados..."
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d postgres redis
    
    # Aguardar banco estar pronto
    log_info "Aguardando banco de dados..."
    sleep 30
    
    # Iniciar backend
    log_info "Iniciando backend..."
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d backend celery_worker
    
    # Aguardar backend
    log_info "Aguardando backend..."
    sleep 30
    
    # Iniciar frontend
    log_info "Iniciando frontend..."
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d frontend
    
    # Aguardar frontend
    log_info "Aguardando frontend..."
    sleep 20
    
    # Iniciar nginx
    log_info "Iniciando nginx..."
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d nginx
    
    # Iniciar backup
    log_info "Iniciando serviço de backup..."
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d backup
    
    log_success "Serviços iniciados!"
}

# Verificação pós-deploy
verify_deploy() {
    log_info "Verificando deploy..."
    
    # Verificar saúde dos serviços
    services=("postgres" "redis" "backend" "frontend" "nginx")
    
    for service in "${services[@]}"; do
        log_info "Verificando $service..."
        if docker-compose -f docker-compose.production.yml ps "$service" | grep -q "Up"; then
            log_success "$service está online"
        else
            log_error "$service não está online!"
            docker-compose -f docker-compose.production.yml logs "$service"
            return 1
        fi
    done
    
    # Testar API
    log_info "Testando API..."
    if curl -f -s http://localhost/health > /dev/null; then
        log_success "API respondendo"
    else
        log_error "API não está respondendo!"
        return 1
    fi
    
    # Testar frontend
    log_info "Testando frontend..."
    if curl -f -s http://localhost > /dev/null; then
        log_success "Frontend respondendo"
    else
        log_error "Frontend não está respondendo!"
        return 1
    fi
    
    log_success "Deploy verificado com sucesso!"
}

# Limpeza
cleanup() {
    log_info "Limpando imagens antigas..."
    
    # Remover imagens não utilizadas
    docker image prune -f
    
    # Remover volumes não utilizados (cuidado!)
    # docker volume prune -f
    
    log_success "Limpeza concluída!"
}

# Menu de rollback
rollback_menu() {
    log_warning "Menu de Rollback"
    echo "1) Restaurar banco de dados"
    echo "2) Voltar para configuração anterior"
    echo "3) Sair"
    read -p "Escolha uma opção: " -n 1 -r
    echo
    
    case $REPLY in
        1)
            log_info "Restaurando banco de dados..."
            # Implementar restauração do backup
            ;;
        2)
            log_info "Voltando para configuração anterior..."
            docker-compose down
            cp backup/pre-deploy/docker-compose.backup.yml docker-compose.yml
            cp backup/pre-deploy/.env.backup .env
            docker-compose up -d
            ;;
        3)
            exit 0
            ;;
        *)
            log_error "Opção inválida"
            ;;
    esac
}

# Main
main() {
    log_info "=== DEPLOY PRODUÇÃO - HOTEL CABO FRIO ==="
    echo
    
    # Verificar se é rollback
    if [ "${1:-}" = "rollback" ]; then
        rollback_menu
        exit 0
    fi
    
    # Executar steps
    check_prerequisites
    backup_current
    build_images
    deploy_services
    
    # Verificação
    if verify_deploy; then
        cleanup
        log_success "🚀 Deploy concluído com sucesso!"
        echo
        log_info "Acesse: https://hotelreal.com.br"
        log_info "Logs: docker-compose -f docker-compose.production.yml logs -f"
        log_info "Status: docker-compose -f docker-compose.production.yml ps"
    else
        log_error "❌ Falha no deploy!"
        log_info "Para rollback: ./deploy-production.sh rollback"
        exit 1
    fi
}

# Executar
main "$@"
