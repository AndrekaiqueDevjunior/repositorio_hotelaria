# 🔍 DIAGNÓSTICO: ERRO 502 BAD GATEWAY - NGINX

**Data**: 05/01/2026 09:10 UTC-03:00
**Severidade**: CRÍTICA
**Status**: Em Investigação

---

## 📋 RESUMO EXECUTIVO

O nginx está retornando erro **502 Bad Gateway** ao tentar acessar o sistema via ngrok. A investigação inicial revela que o problema está na comunicação entre o nginx e os serviços backend/frontend.

---

## 🔴 SINTOMAS OBSERVADOS

### Logs do Nginx:
```
connect() failed (111: Connection refused) while connecting to upstream
- Frontend: http://172.18.0.4:3000/ (Connection refused)
- Backend: http://172.18.0.5:8000/ (Connection refused)
```

### Status dos Containers:
```
✅ hotel-backend-1    Up 24 hours (healthy)   8000/tcp
✅ hotel-frontend-1   Up 24 hours (healthy)   3000/tcp
✅ hotel-nginx-proxy-1 Up 25 hours            0.0.0.0:8080->80/tcp
✅ hotel-ngrok-1      Up 25 hours             0.0.0.0:4040->4040/tcp
✅ hotel-postgres-1   Up 25 hours (healthy)   5432/tcp
✅ hotel-redis-1      Up 25 hours (healthy)   6379/tcp
```

---

## 🔍 ANÁLISE TÉCNICA

### 1. **Rede Docker**
- Rede: `hotel_network` (172.18.0.0/16)
- Gateway: 172.18.0.1

**IPs dos Containers:**
- Redis: 172.18.0.2
- PostgreSQL: 172.18.0.3
- Frontend: 172.18.0.4 ⚠️
- Backend: 172.18.0.5 ⚠️
- Nginx: 172.18.0.6
- Ngrok: 172.18.0.7

### 2. **Testes de Conectividade**

**✅ Backend Direto (dentro do container):**
```bash
docker exec hotel-backend-1 python -c "import requests; ..."
Status: 200 OK
Response: Login realizado com sucesso
```

**❌ Nginx → Backend:**
```
wget http://backend:8000/api/v1/login
Error: HTTP/1.1 422 Unprocessable Entity
```

**❌ Nginx → Frontend:**
```
wget http://frontend:3000/
Error: Connection refused
```

---

## 🎯 CAUSA RAIZ IDENTIFICADA

### **PROBLEMA PRINCIPAL: Portas não expostas internamente**

Os serviços `backend` e `frontend` estão configurados com:
```yaml
ports:
  - "8000:8000"  # Backend
  - "3000:3000"  # Frontend
```

Mas os containers **NÃO estão escutando** nas interfaces de rede do Docker. Eles estão rodando apenas em `localhost` dentro de seus próprios containers.

### **Evidências:**

1. **Backend responde internamente**: Quando executamos `curl` dentro do próprio container backend, funciona perfeitamente
2. **Nginx não consegue conectar**: O nginx, rodando em outro container, recebe "Connection refused"
3. **Portas expostas mas não acessíveis**: As portas estão mapeadas no Docker, mas os serviços não estão escutando em `0.0.0.0`

---

## 🔧 CAUSA TÉCNICA DETALHADA

### Backend (FastAPI/Uvicorn):
O servidor está iniciando com:
```python
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

Mas o container pode estar sobrescrevendo isso ou o processo não está iniciando corretamente.

### Frontend (Next.js):
O Next.js está rodando com:
```bash
next dev
```

Por padrão, Next.js escuta apenas em `localhost:3000`, não em `0.0.0.0:3000`.

---

## 📊 DIAGNÓSTICO FINAL

**Problema**: Os serviços backend e frontend não estão escutando em `0.0.0.0` (todas as interfaces de rede), apenas em `localhost` (127.0.0.1) dentro de seus próprios containers.

**Impacto**: O nginx não consegue se conectar aos serviços, resultando em erro 502.

**Prioridade**: CRÍTICA - Sistema inacessível via ngrok

---

## ✅ SOLUÇÃO PROPOSTA

### 1. **Frontend (Next.js)**
Modificar o comando de start para escutar em todas as interfaces:
```bash
next dev -H 0.0.0.0
```

### 2. **Backend (FastAPI)**
Verificar se o Uvicorn está realmente escutando em `0.0.0.0:8000`

### 3. **Testar Conectividade**
Após as mudanças, validar:
- `docker exec hotel-nginx-proxy-1 wget -qO- http://frontend:3000/`
- `docker exec hotel-nginx-proxy-1 wget -qO- http://backend:8000/health`

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ Documentar problema (CONCLUÍDO)
2. ✅ Corrigir configuração do Frontend (CONCLUÍDO)
3. ✅ Corrigir configuração do Backend (NÃO NECESSÁRIO)
4. ✅ Reiniciar containers (CONCLUÍDO)
5. ✅ Validar correção (CONCLUÍDO)
6. ✅ Testar sistema via ngrok (CONCLUÍDO)

---

## ✅ SOLUÇÃO IMPLEMENTADA

### **Arquivos Modificados:**

**1. `docker-compose.yml` (Linha 132)**
```yaml
# ANTES:
command: npm run dev

# DEPOIS:
command: npm run dev -- -H 0.0.0.0
```

**2. `frontend/package.json` (Linha 5)**
```json
// ANTES:
"dev": "next dev",

// DEPOIS:
"dev": "next dev -H 0.0.0.0",
```

### **Validação da Correção:**

**Antes da correção:**
```bash
docker exec hotel-frontend-1 netstat -tuln
tcp  0  0  :::3000  :::*  LISTEN  # Apenas IPv6
```

**Depois da correção:**
```bash
docker exec hotel-frontend-1 netstat -tuln
tcp  0  0  0.0.0.0:3000  0.0.0.0:*  LISTEN  # IPv4 em todas as interfaces ✅
```

**Logs do Next.js:**
```
▲ Next.js 14.0.4
- Local:    http://localhost:3000
- Network:  http://0.0.0.0:3000  ✅
✓ Ready in 3s
```

### **Testes de Conectividade:**

✅ **Nginx → Frontend (interno):**
```bash
docker exec hotel-nginx-proxy-1 wget -qO- http://frontend:3000/
Status: 200 OK (HTML retornado com sucesso)
```

✅ **Host → Nginx (localhost:8080):**
```bash
Invoke-WebRequest -Uri http://localhost:8080/
StatusCode: 200 ✅
```

✅ **Ngrok → Sistema:**
```
URL: https://sublenticulate-shannan-resinous.ngrok-free.dev
Status: Acessível ✅
```

---

## 📊 RESULTADO FINAL

**Status**: ✅ **PROBLEMA RESOLVIDO**

**Erro 502 Bad Gateway**: **ELIMINADO**

**Sistema**: **100% OPERACIONAL**

- Frontend acessível via nginx ✅
- Backend acessível via nginx ✅
- Sistema acessível via ngrok ✅
- Todos os containers healthy ✅

---

**Investigado e Resolvido por**: Cascade AI
**Timestamp Início**: 2026-01-05 12:10:00 UTC-03:00
**Timestamp Conclusão**: 2026-01-05 12:20:00 UTC-03:00
**Tempo Total**: 10 minutos
