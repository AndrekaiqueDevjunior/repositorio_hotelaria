# 🚀 Deploy Produção - Hotel Real Cabo Frio

## 📋 Checklist Pré-Deploy

### ✅ **Configurações Obrigatórias**

1. **Variáveis de Ambiente**
   ```bash
   # Copiar e configurar
   cp .env.example .env.production
   # Editar com chaves reais
   ```

2. **Certificados SSL**
   ```bash
   # Criar diretório
   mkdir -p nginx/ssl
   
   # Adicionar certificados:
   # - nginx/ssl/cert.pem
   # - nginx/ssl/key.pem
   ```

3. **Banco de Dados Produção**
   - Configurar DATABASE_URL real
   - Testar conexão
   - Migrar dados se necessário

4. **Cielo API**
   - Obter chaves de produção
   - Substituir chaves sandbox
   - Testar integração

## 🔧 **Comandos de Deploy**

### Deploy Completo
```bash
# Executar deploy completo
./deploy-production.sh

# Verificar status
docker-compose -f docker-compose.production.yml ps

# Verificar logs
docker-compose -f docker-compose.production.yml logs -f
```

### Rollback
```bash
# Menu de rollback
./deploy-production.sh rollback
```

### Manutenção
```bash
# Reiniciar serviço específico
docker-compose -f docker-compose.production.yml restart backend

# Verificar saúde
curl https://hotelreal.com.br/health

# Backup manual
docker-compose -f docker-compose.production.yml exec backup /backup.sh
```

## 📊 **Monitoramento**

### Logs Importantes
```bash
# Backend
docker-compose -f docker-compose.production.yml logs -f backend

# Frontend
docker-compose -f docker-compose.production.yml logs -f frontend

# Nginx
docker-compose -f docker-compose.production.yml logs -f nginx

# Banco
docker-compose -f docker-compose.production.yml logs -f postgres
```

### Health Checks
- API: `https://hotelreal.com.br/health`
- Frontend: `https://hotelreal.com.br`
- Docs: `https://hotelreal.com.br/docs` (admin only)

## 🔒 **Segurança Implementada**

### ✅ **Configurado**
- Chaves secretas fortes (64+ caracteres)
- JWT seguro
- Cookies HTTPOnly + Secure
- Headers de segurança (HSTS, X-Frame-Options, etc.)
- CORS restrito
- HTTPS obrigatório
- Rate limiting implícito via nginx

### ⚠️ **Verificar**
- Firewall do servidor
- Monitoramento de acessos
- Backup externo
- Plano de disaster recovery

## 📈 **Performance**

### Otimizações
- Gunicorn com 4 workers
- Nginx com gzip
- Cache estático (1 ano)
- Redis para cache/sessões
- Connection pooling

### Monitorar
- CPU/Memory usage
- Response time API
- Database connections
- Error rates

## 🗄️ **Backup**

### Automático
- Backup diário às 2AM
- Retenção 30 dias
- Compressão gzip
- Verificação de integridade

### Manual
```bash
# Backup imediato
docker-compose -f docker-compose.production.yml exec backup /backup.sh

# Listar backups
ls -la backup/

# Restaurar (em caso de emergência)
docker-compose -f docker-compose.production.yml exec postgres psql -U hotel_user -d hotel_cabo_frio_prod < backup/hotel_backup_YYYYMMDD_HHMMSS.sql
```

## 🚨 **Troubleshooting**

### Problemas Comuns

#### **API não responde**
```bash
# Verificar backend
docker-compose -f docker-compose.production.yml logs backend

# Reiniciar backend
docker-compose -f docker-compose.production.yml restart backend
```

#### **Frontend branco**
```bash
# Verificar build
docker-compose -f docker-compose.production.yml logs frontend

# Reconstruir frontend
docker-compose -f docker-compose.production.yml build --no-cache frontend
```

#### **SSL Error**
```bash
# Verificar certificados
ls -la nginx/ssl/

# Testar nginx config
docker-compose -f docker-compose.production.yml exec nginx nginx -t
```

#### **Database Connection**
```bash
# Verificar postgres
docker-compose -f docker-compose.production.yml logs postgres

# Testar conexão
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U hotel_user
```

### Emergência
1. **Parar tudo**: `docker-compose -f docker-compose.production.yml down`
2. **Restaurar backup**: Verificar seção Backup
3. **Rollback**: `./deploy-production.sh rollback`
4. **Contato**: Equipe de infraestrutura

## 📞 **Suporte**

### Contatos
- **DevOps**: [email/telefone]
- **Database**: [email/telefone]  
- **Segurança**: [email/telefone]

### Documentação
- API Docs: `https://hotelreal.com.br/docs`
- Repositório: [link repo]
- Monitoramento: [link dashboard]

---

## ⚡ **Quick Start**

```bash
# 1. Configurar ambiente
cp .env.example .env.production
# Editar .env.production com valores reais

# 2. Adicionar certificados SSL
mkdir -p nginx/ssl
# Adicionar cert.pem e key.pem

# 3. Executar deploy
./deploy-production.sh

# 4. Verificar
curl https://hotelreal.com.br/health
```

**Status**: ✅ Ready for Production
