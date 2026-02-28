# 🚀 Deploy em Produção - VPS

Guia completo para deploy do sistema Hotel Cabo Frio em VPS com Docker.

---

## 📋 Pré-requisitos

### Na sua máquina local:
- Git configurado
- Acesso SSH à VPS: `ssh root@72.61.27.152`

### Na VPS (será instalado):
- Ubuntu 20.04+ / Debian 11+
- Docker & Docker Compose
- Nginx
- Certbot (Let's Encrypt)

---

## 🔧 Parte 1: Preparar VPS

### 1.1 Conectar na VPS

```bash
ssh root@72.61.27.152
```

### 1.2 Atualizar sistema

```bash
apt update && apt upgrade -y
```

### 1.3 Instalar Docker

```bash
# Instalar dependências
apt install -y apt-transport-https ca-certificates curl software-properties-common

# Adicionar repositório Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Verificar instalação
docker --version
```

### 1.4 Instalar Docker Compose

```bash
# Baixar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permissão de execução
chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker-compose --version
```

### 1.5 Instalar Nginx (no host)

```bash
apt install -y nginx
systemctl enable nginx
systemctl start nginx
```

### 1.6 Instalar Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

---

## 📦 Parte 2: Clonar e Configurar Projeto

### 2.1 Criar diretório e clonar repositório

```bash
# Criar diretório para aplicação
mkdir -p /opt/hotel
cd /opt/hotel

# Clonar repositório (substitua pela URL real)
git clone https://github.com/SEU_USUARIO/app_hotel_cabo_frio.git .
```

### 2.2 Configurar variáveis de ambiente

```bash
# Copiar exemplo para produção
cp .env.production.example .env.production

# Editar com nano ou vim
nano .env.production
```

**Valores OBRIGATÓRIOS para alterar:**

```bash
# Gerar chaves seguras
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -base64 16)
DB_PASSWORD=$(openssl rand -base64 16)
REDIS_PASSWORD=$(openssl rand -base64 16)

# Configurar DATABASE_URL com a senha gerada
DATABASE_URL=postgresql://hotel_user:SENHA_GERADA@postgres:5432/hotel_cabo_frio_prod

# Configurar Redis URLs com a senha gerada
REDIS_URL=redis://:SENHA_REDIS@redis:6379/0
CELERY_BROKER_URL=redis://:SENHA_REDIS@redis:6379/1
CELERY_RESULT_BACKEND=redis://:SENHA_REDIS@redis:6379/2

# Configurar domínio (substitua hotelreal.com.br pelo seu domínio)
CORS_ORIGINS=https://hotelreal.com.br,https://www.hotelreal.com.br
FRONTEND_URL=https://hotelreal.com.br
NEXT_PUBLIC_API_URL=https://hotelreal.com.br/api/v1
COOKIE_DOMAIN=.hotelreal.com.br

# Configurar credenciais Cielo (obter no portal Cielo)
CIELO_MERCHANT_ID=seu_merchant_id_real
CIELO_MERCHANT_KEY=sua_merchant_key_real
```

### 2.3 Criar diretórios necessários

```bash
mkdir -p backup uploads
chmod +x scripts/backup.sh
```

---

## 🐳 Parte 3: Subir Aplicação com Docker

### 3.1 Build das imagens

```bash
cd /opt/hotel
docker-compose -f docker-compose.production.yml build --no-cache
```

### 3.2 Iniciar serviços

```bash
# Subir todos os serviços
docker-compose -f docker-compose.production.yml up -d

# Verificar status
docker-compose -f docker-compose.production.yml ps

# Ver logs
docker-compose -f docker-compose.production.yml logs -f
```

### 3.3 Verificar saúde dos serviços

```bash
# Verificar backend
curl http://localhost:8000/health

# Verificar frontend
curl http://localhost:3000

# Verificar logs de migrations
docker-compose -f docker-compose.production.yml logs backend | grep -i prisma
```

---

## 🌐 Parte 4: Configurar Nginx no Host

### 4.1 Copiar configuração Nginx

```bash
# Copiar configuração principal
cp nginx/nginx.conf /etc/nginx/nginx.conf

# Copiar configuração do site
cp nginx/conf.d/default.conf /etc/nginx/sites-available/hotel

# Criar link simbólico
ln -sf /etc/nginx/sites-available/hotel /etc/nginx/sites-enabled/hotel

# Remover configuração padrão
rm -f /etc/nginx/sites-enabled/default
```

### 4.2 Ajustar configuração para seu domínio

```bash
nano /etc/nginx/sites-available/hotel
```

Altere `hotelreal.com.br` para seu domínio real.

### 4.3 Testar e recarregar Nginx

```bash
# Testar configuração
nginx -t

# Recarregar Nginx
systemctl reload nginx
```

---

## 🔒 Parte 5: Configurar SSL com Certbot

### 5.1 Configurar DNS

**ANTES de executar Certbot**, configure seu DNS:

```
Tipo A: hotelreal.com.br → 72.61.27.152
Tipo A: www.hotelreal.com.br → 72.61.27.152
```

Aguarde propagação DNS (pode levar até 24h, mas geralmente 5-30 minutos).

### 5.2 Obter certificado SSL

```bash
# Executar Certbot
certbot --nginx -d hotelreal.com.br -d www.hotelreal.com.br

# Seguir instruções interativas:
# - Email: seu-email@exemplo.com
# - Aceitar termos: Y
# - Compartilhar email: N (opcional)
# - Redirect HTTP para HTTPS: 2 (Sim)
```

### 5.3 Testar renovação automática

```bash
# Testar renovação (dry-run)
certbot renew --dry-run

# Certbot já configura renovação automática via cron/systemd
```

### 5.4 Verificar SSL

Acesse: `https://hotelreal.com.br` (substitua pelo seu domínio)

---

## ✅ Parte 6: Verificação Final

### 6.1 Checklist de verificação

```bash
# 1. Todos os containers rodando
docker-compose -f docker-compose.production.yml ps

# 2. Backend respondendo
curl https://hotelreal.com.br/api/v1/health

# 3. Frontend carregando
curl -I https://hotelreal.com.br

# 4. SSL válido
curl -I https://hotelreal.com.br | grep -i "HTTP/2 200"

# 5. Backup funcionando
docker-compose -f docker-compose.production.yml logs backup

# 6. Verificar backups criados
ls -lh backup/
```

### 6.2 Testar funcionalidades

1. **Login**: `https://hotelreal.com.br/login`
   - Email: `admin@hotelreal.com.br`
   - Senha: (valor de `ADMIN_PASSWORD` no `.env.production`)

2. **API Docs** (se DEBUG=True): `https://hotelreal.com.br/docs`

3. **Criar reserva teste**

4. **Testar pagamento** (com valor baixo em produção Cielo)

---

## 🔄 Parte 7: Atualizações e Manutenção

### 7.1 Atualizar aplicação

```bash
cd /opt/hotel

# Pull das alterações
git pull origin main

# Rebuild e restart
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# Aplicar migrations (se houver)
docker-compose -f docker-compose.production.yml exec backend prisma migrate deploy
```

### 7.2 Ver logs

```bash
# Logs de todos os serviços
docker-compose -f docker-compose.production.yml logs -f

# Logs de um serviço específico
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f frontend
docker-compose -f docker-compose.production.yml logs -f postgres
```

### 7.3 Backup manual

```bash
# Executar backup manualmente
docker-compose -f docker-compose.production.yml exec backup /backup.sh

# Baixar backup para máquina local
scp root@72.61.27.152:/opt/hotel/backup/hotel_backup_*.sql.gz ./
```

### 7.4 Restaurar backup

```bash
# Descompactar backup
gunzip backup/hotel_backup_YYYYMMDD_HHMMSS.sql.gz

# Restaurar no banco
docker-compose -f docker-compose.production.yml exec -T postgres psql -U hotel_user -d hotel_cabo_frio_prod < backup/hotel_backup_YYYYMMDD_HHMMSS.sql
```

### 7.5 Reiniciar serviços

```bash
# Reiniciar todos
docker-compose -f docker-compose.production.yml restart

# Reiniciar serviço específico
docker-compose -f docker-compose.production.yml restart backend
docker-compose -f docker-compose.production.yml restart frontend
```

### 7.6 Parar aplicação

```bash
# Parar todos os serviços
docker-compose -f docker-compose.production.yml down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker-compose -f docker-compose.production.yml down -v
```

---

## 🐛 Troubleshooting

### Problema: Backend não inicia

```bash
# Ver logs detalhados
docker-compose -f docker-compose.production.yml logs backend

# Verificar DATABASE_URL
docker-compose -f docker-compose.production.yml exec backend env | grep DATABASE_URL

# Testar conexão com banco
docker-compose -f docker-compose.production.yml exec postgres psql -U hotel_user -d hotel_cabo_frio_prod -c "SELECT 1;"
```

### Problema: Frontend retorna 502

```bash
# Verificar se backend está respondendo
curl http://localhost:8000/health

# Verificar logs do Nginx
tail -f /var/log/nginx/error.log

# Verificar se portas estão expostas
netstat -tlnp | grep -E ':(8000|3000)'
```

### Problema: Migrations falhando

```bash
# Verificar status das migrations
docker-compose -f docker-compose.production.yml exec backend prisma migrate status

# Forçar regeneração do Prisma Client
docker-compose -f docker-compose.production.yml exec backend prisma generate

# Aplicar migrations manualmente
docker-compose -f docker-compose.production.yml exec backend prisma migrate deploy
```

### Problema: SSL não funciona

```bash
# Verificar certificados
certbot certificates

# Renovar certificado
certbot renew --force-renewal

# Verificar configuração Nginx
nginx -t
```

---

## 📊 Monitoramento

### Recursos do sistema

```bash
# Uso de disco
df -h

# Uso de memória
free -h

# Containers e uso de recursos
docker stats

# Espaço usado por Docker
docker system df
```

### Limpeza de espaço

```bash
# Remover imagens não utilizadas
docker image prune -a

# Remover volumes não utilizados
docker volume prune

# Limpeza completa (CUIDADO!)
docker system prune -a --volumes
```

---

## 🔐 Segurança

### Firewall (UFW)

```bash
# Instalar UFW
apt install -y ufw

# Configurar regras
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Ativar firewall
ufw enable

# Verificar status
ufw status
```

### Fail2ban (proteção contra brute force)

```bash
# Instalar
apt install -y fail2ban

# Configurar
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
nano /etc/fail2ban/jail.local

# Ativar
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 📞 Suporte

- **Logs da aplicação**: `/opt/hotel/`
- **Logs do Nginx**: `/var/log/nginx/`
- **Backups**: `/opt/hotel/backup/`

---

## ✨ Checklist Final de Deploy

- [ ] VPS configurada com Docker e Docker Compose
- [ ] Nginx instalado no host
- [ ] Repositório clonado em `/opt/hotel`
- [ ] `.env.production` configurado com valores reais
- [ ] Containers rodando (`docker-compose ps`)
- [ ] Backend respondendo em `http://localhost:8000/health`
- [ ] Frontend respondendo em `http://localhost:3000`
- [ ] DNS configurado apontando para VPS
- [ ] Nginx configurado e testado (`nginx -t`)
- [ ] SSL configurado com Certbot
- [ ] HTTPS funcionando (`https://seudominio.com.br`)
- [ ] Login admin funcionando
- [ ] Backup automático ativo
- [ ] Firewall configurado (UFW)

---

**🎉 Deploy concluído com sucesso!**
