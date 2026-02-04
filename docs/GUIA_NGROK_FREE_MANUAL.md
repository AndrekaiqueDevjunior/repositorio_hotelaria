# Guia ngrok FREE - Configuração Manual

## 🎯 Solução para ngrok FREE (1 Túnel Único)

Como o plano FREE do ngrok permite apenas **1 túnel**, usamos **Nginx como proxy reverso** para unificar Frontend + Backend em uma **única URL pública**.

## 📋 Passos Manuais

### 1. Rebuild das Imagens

```powershell
docker-compose build --no-cache backend frontend
```

### 2. Iniciar PostgreSQL e Redis

```powershell
docker-compose up -d postgres redis
```

Aguarde 10 segundos.

### 3. Iniciar Backend

```powershell
docker-compose up -d backend
```

Aguarde 12 segundos.

### 4. Iniciar Frontend

```powershell
docker-compose up -d frontend
```

Aguarde 12 segundos.

### 5. Iniciar Nginx Proxy

```powershell
docker-compose --profile ngrok up -d nginx-proxy
```

Aguarde 5 segundos.

### 6. Iniciar ngrok

```powershell
docker-compose --profile ngrok up -d ngrok
```

Aguarde 25 segundos.

### 7. Obter URL Pública

```powershell
Invoke-RestMethod "http://localhost:4040/api/tunnels"
```

Copie o valor de `public_url`. Exemplo: `https://abc123.ngrok-free.app`

### 8. Configurar Frontend

Edite `frontend\.env.local`:
```
NEXT_PUBLIC_API_URL=https://SUA-URL-NGROK.ngrok-free.app/api/v1
```

### 9. Configurar Backend

Edite `backend\.env.docker` e ajuste:
```
CORS_ORIGINS=https://SUA-URL-NGROK.ngrok-free.app,http://localhost:3000
FRONTEND_URL=https://SUA-URL-NGROK.ngrok-free.app
COOKIE_SECURE=True
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
```

### 10. Reiniciar para Aplicar

```powershell
docker-compose restart backend frontend
```

Aguarde 15 segundos.

### 11. Testar

```powershell
# Frontend
Invoke-WebRequest "https://SUA-URL-NGROK.ngrok-free.app" -UseBasicParsing

# Backend Health
Invoke-WebRequest "https://SUA-URL-NGROK.ngrok-free.app/health" -UseBasicParsing

# Login
$body = @{email="admin@hotelreal.com.br";password="admin123"} | ConvertTo-Json
Invoke-WebRequest "https://SUA-URL-NGROK.ngrok-free.app/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

## 🎯 Arquitetura Final

```
Internet
    ↓
ngrok (1 túnel FREE)
    ↓
Nginx Proxy Reverso (porta 80)
    ├── / → Frontend (porta 3000)
    ├── /api → Backend (porta 8000)
    └── /health → Backend Health
```

## ✅ URLs Finais

- **Frontend:** `https://SUA-URL.ngrok-free.app`
- **Backend API:** `https://SUA-URL.ngrok-free.app/api/v1`
- **Backend Health:** `https://SUA-URL.ngrok-free.app/health`

## 🔐 Login

- **Email:** `admin@hotelreal.com.br`
- **Senha:** `admin123`

## 📊 Dashboards

- **ngrok:** `http://localhost:4040`
- **Nginx:** `http://localhost:8080`

## 🔧 Comandos Úteis

### Ver Logs
```powershell
docker-compose logs -f ngrok
docker-compose logs -f nginx-proxy
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Ver Status
```powershell
docker-compose ps
docker-compose --profile ngrok ps
```

### Parar Tudo
```powershell
docker-compose down
```

### Limpar Completamente
```powershell
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker system prune -f
```

## ✨ Pronto!

Sistema completo rodando com **ngrok FREE** (1 túnel único) + **Nginx proxy reverso** unificando Frontend e Backend!

**Dados do PostgreSQL foram preservados!** 🎉
