# Setup Completo - Ngrok + Docker + Autenticação

## Pré-requisitos

1. **Ngrok instalado**: https://ngrok.com/download
2. **Docker Desktop rodando**
3. **PowerShell como administrador**

## Passo 1: Iniciar Sistema Docker

```powershell
# Parar containers existentes
docker-compose down --remove-orphans

# Rebuild para garantir mudanças
docker-compose build --no-cache

# Iniciar sistema completo
docker-compose up -d

# Verificar se todos os serviços estão rodando
docker-compose ps
```

**Aguardar até todos os serviços estarem "healthy" ou "running".**

## Passo 2: Testar Localmente

Antes de expor externamente, validar que funciona localmente:

```powershell
# Testar nginx (deve mostrar frontend)
curl http://localhost:8080

# Testar API via nginx (deve retornar JSON)
curl http://localhost:8080/api/v1/health

# Testar login no browser
# Ir para: http://localhost:8080
# Fazer login com: admin@hotelreal.com.br / admin123
```

## Passo 3: Expor com Ngrok

```powershell
# COMANDO PRINCIPAL - EXPOR PORTA ÚNICA DO NGINX
ngrok http 8080

# Com configurações extras (recomendado)
ngrok http 8080 --host-header=rewrite

# Para conta free (evitar warning browser)
ngrok http 8080 --host-header=rewrite --bind-tls=true
```

## Passo 4: Configurar CORS (se necessário)

Se houver erro de CORS com ngrok, adicionar no `.env`:

```bash
# Adicionar no backend/.env
CORS_ORIGINS=https://SEU-SUBDOMINIO.ngrok-free.app

# Ou no docker-compose.yml na seção backend/environment:
CORS_ORIGINS=https://SEU-SUBDOMINIO.ngrok-free.app
```

**IMPORTANTE**: Substitua `SEU-SUBDOMINIO` pela URL real do ngrok.

## Passo 5: Testar Externamente

1. **Copiar URL do ngrok** (ex: `https://abc123.ngrok-free.app`)
2. **Abrir em navegador externo** (outro dispositivo/rede)
3. **Clicar "Visit Site"** se aparecer aviso do ngrok
4. **Fazer login**: `admin@hotelreal.com.br` / `admin123`
5. **Testar funcionalidades**: reservas, pagamentos, pontos

## Arquitetura Final

```
Internet
  ↓
Ngrok HTTPS (exemplo: abc123.ngrok-free.app)
  ↓
Nginx (localhost:8080)
  ├── /        → Frontend Next.js (:3000)
  ├── /api     → Backend FastAPI (:8000)
  ├── /docs    → Swagger API
  └── /health  → Health check
```

## Comandos de Diagnóstico

```powershell
# Verificar containers rodando
docker-compose ps

# Logs em tempo real
docker-compose logs -f

# Logs específicos
docker-compose logs nginx
docker-compose logs backend
docker-compose logs frontend

# Testar conectividade interna
docker-compose exec nginx curl http://backend:8000/health
docker-compose exec nginx curl http://frontend:3000

# Verificar portas ocupadas
netstat -an | findstr :8080
netstat -an | findstr :3000
netstat -an | findstr :8000
```

## Solução de Problemas

### Erro: "Connection Refused"
```powershell
# Verificar se containers estão up
docker-compose ps

# Restart completo
docker-compose down && docker-compose up -d
```

### Erro: "CORS Policy"
```bash
# Verificar variável de ambiente
docker-compose exec backend env | grep CORS_ORIGINS

# Se não estiver definida, adicionar no docker-compose.yml
```

### Erro 502 Bad Gateway
```powershell
# Verificar se backend está respondendo
curl http://localhost:8080/api/v1/health

# Se não responder, verificar logs do backend
docker-compose logs backend
```

### Frontend não carrega
```powershell
# Verificar se frontend está buildando
docker-compose logs frontend

# Verificar se Next.js está rodando na porta 3000
docker-compose exec frontend ps aux
```

## Comandos para Parar

```powershell
# Parar ngrok (Ctrl+C no terminal)
# Parar containers
docker-compose down

# Limpeza completa (se necessário)
docker-compose down --volumes --remove-orphans
docker system prune -f
```

## URLs Importantes

- **Local**: http://localhost:8080
- **Ngrok**: https://SEU-SUBDOMINIO.ngrok-free.app  
- **API Docs**: https://SEU-SUBDOMINIO.ngrok-free.app/docs
- **Health**: https://SEU-SUBDOMINIO.ngrok-free.app/health
- **Login**: admin@hotelreal.com.br / admin123
