# Guia de Autenticação JWT com Cookies HttpOnly

## 📋 Visão Geral

Sistema de autenticação JWT baseado em **cookies HttpOnly**, sem uso de localStorage, seguindo boas práticas de segurança e compatível com:

- ✅ Desenvolvimento local (localhost)
- ✅ Acesso remoto via Cloudflare Tunnel
- ✅ Frontend e Backend em domínios diferentes
- ✅ HTTPS obrigatório em produção
- ✅ Persistência de sessão após refresh

## 🏗️ Arquitetura Implementada

### Backend (FastAPI)

**Cookie Configuration:**
- `HttpOnly = true` - Impede acesso via JavaScript
- `Secure = true` - Apenas HTTPS (produção)
- `SameSite = none` - Permite cross-origin (Cloudflare Tunnel)
- `Domain = .seudominio.dev` - Compartilhado entre subdomínios

**Endpoints:**
- `POST /auth/login` - Define cookie com JWT
- `POST /auth/logout` - Remove cookie
- `GET /auth/me` - Valida sessão via cookie

**Middleware de Autenticação:**
- Lê JWT do cookie automaticamente
- Fallback para header `Authorization: Bearer <token>`
- Valida token e injeta usuário no contexto

### Frontend (Next.js)

**Configuração Axios:**
- `withCredentials: true` - Envia cookies automaticamente
- Remove uso de localStorage
- Cookies gerenciados pelo navegador

**AuthContext:**
- `checkAuth()` - Chama `/auth/me` para validar sessão
- `login()` - Recebe cookie automaticamente
- `logout()` - Remove cookie via endpoint

## 🔧 Configuração para Desenvolvimento Local

### 1. Backend (.env ou .env.docker)

```env
# Cookie Configuration
COOKIE_NAME=hotel_auth_token
COOKIE_DOMAIN=.localhost
COOKIE_SECURE=False
COOKIE_SAMESITE=lax
COOKIE_HTTPONLY=True
COOKIE_MAX_AGE=604800

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### 2. Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Iniciar Sistema (Docker)

```powershell
# Iniciar containers
docker-compose up -d

# Verificar logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. Testar Localmente

1. Acesse: `http://localhost:3000`
2. Faça login com: `admin@hotelreal.com.br` / `admin123`
3. Cookie será salvo automaticamente
4. Refresh da página mantém sessão

## 🌐 Configuração para Cloudflare Tunnel

### 1. Criar Cloudflare Tunnel

```bash
# Instalar cloudflared
# Windows: https://github.com/cloudflare/cloudflared/releases

# Autenticar
cloudflared tunnel login

# Criar tunnel
cloudflared tunnel create hotel-demo

# Criar arquivo de configuração
```

### 2. Arquivo config.yml do Cloudflare Tunnel

```yaml
tunnel: <TUNNEL_ID>
credentials-file: C:\Users\<USER>\.cloudflared\<TUNNEL_ID>.json

ingress:
  # Frontend
  - hostname: app-demo.seudominio.dev
    service: http://localhost:3000
    
  # Backend API
  - hostname: api-demo.seudominio.dev
    service: http://localhost:8000
    
  # Catchall
  - service: http_status:404
```

### 3. Configurar DNS no Cloudflare

No painel do Cloudflare, adicione registros CNAME:

- `app-demo.seudominio.dev` → `<TUNNEL_ID>.cfargotunnel.com`
- `api-demo.seudominio.dev` → `<TUNNEL_ID>.cfargotunnel.com`

### 4. Atualizar Variáveis de Ambiente

**Backend (.env.docker):**

```env
# Cookie Configuration - PRODUÇÃO
COOKIE_NAME=hotel_auth_token
COOKIE_DOMAIN=.seudominio.dev
COOKIE_SECURE=True
COOKIE_SAMESITE=none
COOKIE_HTTPONLY=True
COOKIE_MAX_AGE=604800

# CORS Configuration - PRODUÇÃO
CORS_ORIGINS=https://app-demo.seudominio.dev,https://api-demo.seudominio.dev
FRONTEND_URL=https://app-demo.seudominio.dev
```

**Frontend (.env.local):**

```env
NEXT_PUBLIC_API_URL=https://api-demo.seudominio.dev/api/v1
```

### 5. Reiniciar Sistema

```powershell
# Parar containers
docker-compose down

# Reconstruir com novas variáveis
docker-compose up -d --build

# Iniciar Cloudflare Tunnel
cloudflared tunnel run hotel-demo
```

### 6. Testar Remotamente

1. Acesse: `https://app-demo.seudominio.dev`
2. Faça login
3. Cookie será salvo com `Secure=true; SameSite=None`
4. Sessão persiste após refresh
5. Cliente remoto consegue acessar

## 🔍 Verificação de Configuração

### Browser DevTools (F12)

**1. Verificar Cookie (Application → Cookies):**
```
Name: hotel_auth_token
Value: eyJ0eXAiOiJKV1QiLCJh...
Domain: .seudominio.dev
Path: /
Secure: ✓
HttpOnly: ✓
SameSite: None
```

**2. Network → Request Headers:**
```
Cookie: hotel_auth_token=eyJ0eXAiOiJKV1Qi...
Origin: https://app-demo.seudominio.dev
```

**3. Network → Response Headers:**
```
Set-Cookie: hotel_auth_token=...; Secure; HttpOnly; SameSite=None
Access-Control-Allow-Origin: https://app-demo.seudominio.dev
Access-Control-Allow-Credentials: true
```

### Console Logs

**Login bem-sucedido:**
```
🔐 [AuthContext] Iniciando login...
✅ [AuthContext] Resposta recebida: { success: true, tokenType: 'cookie' }
🍪 [AuthContext] JWT armazenado em cookie HttpOnly
✅ [AuthContext] Atualizando state do usuário...
🎉 [AuthContext] Login bem-sucedido!
```

**Verificação automática:**
```
🌐 [API] Usando configuração: https://api-demo.seudominio.dev/api/v1
✅ [AuthContext] Sessão válida, usuário autenticado
```

## ❌ Problemas Comuns e Soluções

### Cookie não é salvo

**Causa:** `COOKIE_DOMAIN` incorreto ou `SameSite` incompatível

**Solução:**
- Local: `COOKIE_DOMAIN=.localhost` e `COOKIE_SAMESITE=lax`
- Produção: `COOKIE_DOMAIN=.seudominio.dev` e `COOKIE_SAMESITE=none`
- Sempre use ponto inicial no domínio: `.seudominio.dev`

### Erro CORS

**Causa:** `allow_origins=["*"]` com `allow_credentials=True`

**Solução:**
- Especificar origens explícitas em `CORS_ORIGINS`
- Nunca usar `*` quando cookies estão habilitados
- Incluir protocolo: `https://app-demo.seudominio.dev`

### Cookie não é enviado

**Causa:** `withCredentials: false` no axios

**Solução:**
```javascript
// lib/api.js
export const api = axios.create({
  withCredentials: true,  // OBRIGATÓRIO
  // ...
});
```

### Sessão perde após refresh

**Causa:** Frontend usando localStorage

**Solução:**
- Remover `localStorage.getItem('token')`
- Usar endpoint `/auth/me` para verificar sessão
- Cookie é enviado automaticamente

### HTTPS required em produção

**Causa:** Cookie com `Secure=true` só funciona em HTTPS

**Solução:**
- Cloudflare Tunnel fornece HTTPS automaticamente
- Local: usar `COOKIE_SECURE=False`
- Produção: usar `COOKIE_SECURE=True`

## 🔒 Segurança

### O que está protegido

✅ JWT em cookie HttpOnly (não acessível via JavaScript)  
✅ Cookie com flag Secure (apenas HTTPS)  
✅ SameSite=None com HTTPS (CSRF protegido)  
✅ CORS restrito a domínios específicos  
✅ Token blacklist no logout  
✅ Refresh token para renovação

### O que evitar

❌ `localStorage.setItem('token', ...)` - Vulnerável a XSS  
❌ `allow_origins=["*"]` com credentials  
❌ Cookie sem `HttpOnly` flag  
❌ `SameSite=lax` em produção cross-domain  
❌ Domínio sem ponto inicial (`.seudominio.dev`)

## 📊 Fluxo de Autenticação

```
┌─────────────┐                  ┌─────────────┐
│  Frontend   │                  │   Backend   │
│  (Next.js)  │                  │  (FastAPI)  │
└──────┬──────┘                  └──────┬──────┘
       │                                │
       │  POST /auth/login              │
       │  { email, password }           │
       ├───────────────────────────────>│
       │                                │
       │  200 OK                        │
       │  Set-Cookie: hotel_auth_token  │
       │  { success: true, user: {...} }│
       │<───────────────────────────────┤
       │                                │
       │  [Navegador salva cookie]      │
       │                                │
       │  GET /auth/me                  │
       │  Cookie: hotel_auth_token      │
       ├───────────────────────────────>│
       │                                │
       │  200 OK                        │
       │  { id, nome, email, perfil }   │
       │<───────────────────────────────┤
       │                                │
       │  [Sessão autenticada]          │
       │                                │
       │  POST /auth/logout             │
       │  Cookie: hotel_auth_token      │
       ├───────────────────────────────>│
       │                                │
       │  200 OK                        │
       │  Set-Cookie: [delete]          │
       │<───────────────────────────────┤
       │                                │
       │  [Cookie removido]             │
       │                                │
```

## 🧪 Testes

### Teste 1: Login Local

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hotelreal.com.br","password":"admin123"}' \
  -c cookies.txt -v
```

### Teste 2: Verificar Sessão

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -b cookies.txt -v
```

### Teste 3: Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt -c cookies.txt -v
```

## 📝 Checklist de Deploy

- [ ] Variáveis de ambiente configuradas (.env.docker)
- [ ] CORS_ORIGINS com domínios corretos
- [ ] COOKIE_DOMAIN com ponto inicial (.seudominio.dev)
- [ ] COOKIE_SECURE=True em produção
- [ ] COOKIE_SAMESITE=none em produção
- [ ] Frontend com NEXT_PUBLIC_API_URL correto
- [ ] Cloudflare Tunnel configurado e rodando
- [ ] DNS CNAME configurado no Cloudflare
- [ ] Containers reconstruídos (docker-compose up -d --build)
- [ ] Teste de login remoto funcionando
- [ ] Cookie visível no DevTools
- [ ] Sessão persiste após refresh

## 🎯 Resultado Final

Após implementação completa:

1. **Desenvolvimento:** Login funciona em `localhost` com cookies lax
2. **Produção:** Login funciona via Cloudflare Tunnel com cookies secure
3. **Persistência:** Sessão mantida após refresh da página
4. **Segurança:** JWT em cookie HttpOnly, inacessível via JavaScript
5. **Compatibilidade:** Funciona em desktop, mobile, qualquer navegador

## 📚 Referências

- [MDN - Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)
- [OWASP - Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [FastAPI - Cookie Parameters](https://fastapi.tiangolo.com/tutorial/cookie-params/)
- [Axios - withCredentials](https://axios-http.com/docs/req_config)
- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
