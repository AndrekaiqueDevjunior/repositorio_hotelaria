# ✅ Checklist de Produção - Hotel Cabo Frio

## 📦 Arquivos Criados para Produção

### Arquivos na Raiz
- [x] `docker-compose.production.yml` - Compose de produção sem `target: production`
- [x] `.env.production.example` - Template de variáveis (versionável)
- [x] `DEPLOY_VPS.md` - Documentação completa de deploy

### Estrutura Nginx
- [x] `nginx/nginx.conf` - Configuração principal do Nginx
- [x] `nginx/conf.d/default.conf` - Configuração do site (será copiada para host)

### Scripts
- [x] `scripts/backup.sh` - Script de backup automático do PostgreSQL

### Dependências
- [x] `backend/requirements.txt` - Adicionado `gunicorn==21.2.0`

### Configuração Git
- [x] `.gitignore` - Atualizado para:
  - Ignorar `.env.production` (secrets)
  - Não ignorar `nginx/` (configs versionadas)
  - Não ignorar `backend/prisma/migrations/` (migrations versionadas)

---

## 🔍 Validações Realizadas

### Docker Compose Production
- [x] Sem `target: production` (Dockerfiles são single-stage)
- [x] Usa `prisma migrate deploy` (seguro para produção)
- [x] Usa `gunicorn` para backend (produção)
- [x] Usa `npm run build && npm start` para frontend (produção)
- [x] Health checks configurados
- [x] Logging configurado (json-file com rotação)
- [x] Volumes persistentes (postgres_data_prod, redis_data_prod)
- [x] Rede isolada (hotel_network)
- [x] Restart policy: `unless-stopped`
- [x] Redis com senha (via REDIS_PASSWORD)
- [x] Backup automático diário

### Variáveis de Ambiente
- [x] `.env.production.example` com todos os campos necessários
- [x] Instruções claras para gerar chaves seguras
- [x] Placeholders para credenciais Cielo
- [x] Configurações de CORS/Cookie para produção
- [x] DATABASE_URL formatada corretamente

### Nginx
- [x] Configuração principal (`nginx.conf`) otimizada
- [x] Gzip habilitado
- [x] Security headers configurados
- [x] Upstream para backend (localhost:8000)
- [x] Upstream para frontend (localhost:3000)
- [x] Proxy pass para `/api/v1`, `/health`, `/_next`, `/uploads`
- [x] Preparado para Certbot (location /.well-known/acme-challenge/)

### Backup
- [x] Script `backup.sh` com compressão
- [x] Retenção configurável (BACKUP_RETENTION_DAYS)
- [x] Limpeza automática de backups antigos
- [x] Logs detalhados

---

## 🚀 Comandos de Deploy

### Na VPS (após seguir DEPLOY_VPS.md)

```bash
# 1. Clonar repositório
cd /opt/hotel
git clone <repo-url> .

# 2. Configurar .env.production
cp .env.production.example .env.production
nano .env.production  # Editar com valores reais

# 3. Build e subida
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# 4. Verificar
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs -f

# 5. Configurar Nginx no host
cp nginx/nginx.conf /etc/nginx/nginx.conf
cp nginx/conf.d/default.conf /etc/nginx/sites-available/hotel
ln -sf /etc/nginx/sites-available/hotel /etc/nginx/sites-enabled/hotel
nginx -t && systemctl reload nginx

# 6. Configurar SSL
certbot --nginx -d hotelreal.com.br -d www.hotelreal.com.br
```

---

## ⚠️ Pontos de Atenção

### Antes do Deploy
1. **DNS configurado** - Domínio apontando para IP da VPS
2. **Credenciais Cielo** - Obter no portal Cielo (modo produção)
3. **Gerar senhas fortes** - Usar `openssl rand -hex 32`
4. **Backup do .env.production** - Guardar em local seguro (não commitar!)

### Após Deploy
1. **Testar login admin** - Verificar ADMIN_PASSWORD
2. **Testar pagamento** - Usar valor baixo em produção
3. **Verificar backups** - Checar pasta `backup/`
4. **Monitorar logs** - Primeiras 24h acompanhar logs
5. **Configurar firewall** - UFW com portas 22, 80, 443

---

## 🔧 Troubleshooting Rápido

### Backend não inicia
```bash
docker-compose -f docker-compose.production.yml logs backend
docker-compose -f docker-compose.production.yml exec backend env | grep DATABASE_URL
```

### Frontend 502
```bash
curl http://localhost:8000/health
curl http://localhost:3000
tail -f /var/log/nginx/error.log
```

### Migrations falhando
```bash
docker-compose -f docker-compose.production.yml exec backend prisma migrate status
docker-compose -f docker-compose.production.yml exec backend prisma generate
docker-compose -f docker-compose.production.yml exec backend prisma migrate deploy
```

---

## 📊 Monitoramento

```bash
# Recursos
docker stats
df -h
free -h

# Logs
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f frontend
docker-compose -f docker-compose.production.yml logs -f postgres

# Backups
ls -lh backup/
```

---

## ✨ Status: PRONTO PARA DEPLOY

Todos os arquivos necessários foram criados e validados. O sistema está pronto para ser deployado na VPS seguindo o guia `DEPLOY_VPS.md`.
