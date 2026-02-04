# 🔒 Guia de Instalação SSL/HTTPS na VPS

## 📋 Pré-requisitos

1. **Domínio configurado** apontando para o IP da VPS (72.61.27.152)
2. **Portas abertas**: 80 (HTTP) e 443 (HTTPS)
3. **Nginx rodando** na VPS

---

## 🚀 Passo a Passo

### 1️⃣ Conectar na VPS

```bash
ssh root@72.61.27.152
```

### 2️⃣ Atualizar o sistema

```bash
apt update && apt upgrade -y
```

### 3️⃣ Instalar Certbot e plugin do Nginx

```bash
apt install certbot python3-certbot-nginx -y
```

### 4️⃣ Verificar configuração do Nginx

```bash
# Ver configuração atual
cat /opt/hotel/nginx/nginx.conf

# Testar configuração
nginx -t
```

### 5️⃣ Obter certificado SSL (substitua SEU_DOMINIO.com)

**IMPORTANTE:** Substitua `hotelrealcabofrio.com.br` pelo domínio real do hotel.

```bash
# Parar o Nginx temporariamente
docker-compose -f /opt/hotel/docker-compose.production.yml stop nginx

# Obter certificado
certbot certonly --standalone -d hotelrealcabofrio.com.br -d www.hotelrealcabofrio.com.br

# Ou se preferir usar o plugin do Nginx:
certbot --nginx -d hotelrealcabofrio.com.br -d www.hotelrealcabofrio.com.br
```

### 6️⃣ Configurar Nginx para HTTPS

Edite o arquivo de configuração do Nginx:

```bash
nano /opt/hotel/nginx/nginx.conf
```

Adicione a configuração HTTPS:

```nginx
server {
    listen 80;
    server_name hotelrealcabofrio.com.br www.hotelrealcabofrio.com.br;
    
    # Redirecionar HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hotelrealcabofrio.com.br www.hotelrealcabofrio.com.br;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/hotelrealcabofrio.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hotelrealcabofrio.com.br/privkey.pem;

    # Configurações SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Headers de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7️⃣ Atualizar docker-compose.production.yml

Edite o arquivo para mapear os certificados:

```bash
nano /opt/hotel/docker-compose.production.yml
```

Adicione os volumes no serviço nginx:

```yaml
nginx:
  image: nginx:alpine
  container_name: hotel_nginx_prod
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
    - /var/lib/letsencrypt:/var/lib/letsencrypt:ro
  depends_on:
    - backend
    - frontend
  networks:
    - hotel_network
  restart: unless-stopped
```

### 8️⃣ Reiniciar os serviços

```bash
cd /opt/hotel
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

### 9️⃣ Testar o certificado

```bash
# Testar configuração do Nginx
docker exec hotel_nginx_prod nginx -t

# Verificar se o site está acessível via HTTPS
curl -I https://hotelrealcabofrio.com.br
```

### 🔄 Renovação automática do certificado

O Certbot instala automaticamente um cron job para renovar os certificados. Verifique:

```bash
# Testar renovação
certbot renew --dry-run

# Ver status do timer de renovação
systemctl status certbot.timer
```

Para garantir que o Nginx recarregue após a renovação, crie um hook:

```bash
nano /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

Adicione:

```bash
#!/bin/bash
docker-compose -f /opt/hotel/docker-compose.production.yml restart nginx
```

Torne executável:

```bash
chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

---

## ✅ Verificação Final

1. **Acesse o site via HTTPS:** https://hotelrealcabofrio.com.br
2. **Verifique o certificado:** Clique no cadeado no navegador
3. **Teste redirecionamento HTTP → HTTPS:** http://hotelrealcabofrio.com.br deve redirecionar para HTTPS
4. **Teste SSL Labs:** https://www.ssllabs.com/ssltest/

---

## 🔧 Troubleshooting

### Erro: "Port 80 already in use"

```bash
# Parar o Nginx antes de obter o certificado
docker-compose -f /opt/hotel/docker-compose.production.yml stop nginx

# Obter certificado
certbot certonly --standalone -d seu-dominio.com

# Reiniciar
docker-compose -f /opt/hotel/docker-compose.production.yml up -d
```

### Erro: "Certificate not found"

Verifique se os certificados foram gerados:

```bash
ls -la /etc/letsencrypt/live/
```

### Nginx não inicia após configurar SSL

```bash
# Ver logs
docker logs hotel_nginx_prod

# Testar configuração
docker exec hotel_nginx_prod nginx -t
```

---

## 📝 Notas Importantes

1. **Domínio obrigatório:** Let's Encrypt requer um domínio válido apontando para o IP da VPS
2. **Portas abertas:** Certifique-se que as portas 80 e 443 estão abertas no firewall
3. **Renovação:** Os certificados Let's Encrypt são válidos por 90 dias e renovam automaticamente
4. **Backup:** Faça backup dos certificados em `/etc/letsencrypt/`

---

## 🎯 Qual é o domínio do Hotel?

Para prosseguir com a instalação, preciso saber:
- **Domínio principal:** (ex: hotelrealcabofrio.com.br)
- **Subdomínio www:** (ex: www.hotelrealcabofrio.com.br)

Execute os comandos acima substituindo `hotelrealcabofrio.com.br` pelo domínio real do hotel.
