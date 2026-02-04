# Guia Completo: Ngrok com Autenticacao JWT + Cookies

## Arquitetura Atual do Sistema

**Frontend**: Next.js na porta 3000
**Backend**: FastAPI na porta 8000
**Autenticacao**: JWT em cookies HttpOnly + header Authorization (fallback)
**CORS**: Configurado para `allow_credentials=true`

---

## Opcao 1: Dois Tuneis Separados (RECOMENDADO)

### Vantagens
- Mais simples de configurar
- Sem necessidade de proxy reverso
- Cada servico tem sua propria URL publica
- Melhor para debugging

### Desvantagens
- Requer dois processos ngrok
- URLs diferentes para frontend e backend

### Comandos

```powershell
# Terminal 1 - Tunel para Backend
ngrok http 8000 --host-header="localhost:8000"

# Terminal 2 - Tunel para Frontend
ngrok http 3000 --host-header="localhost:3000"
```

### Resultado Esperado

```
Backend:  https://abc123.ngrok-free.app -> http://localhost:8000
Frontend: https://xyz789.ngrok-free.app -> http://localhost:3000
```

---

## Opcao 2: Tunel Unico com Proxy Reverso

### Vantagens
- Uma unica URL para o cliente
- Mais proximo de ambiente de producao
- Menos confusao para usuarios finais

### Desvantagens
- Requer configuracao de proxy (nginx ou node)
- Mais complexo para debugar
- Precisa rodar proxy local

### Comandos

```powershell
# 1. Iniciar proxy reverso (ver script abaixo)
node proxy-ngrok.js

# 2. Tunel para o proxy
ngrok http 9000 --host-header="localhost:9000"
```

---

## Configuracao Detalhada

### 1. Backend - Ajustes CORS

O backend ja esta configurado para detectar ngrok automaticamente.
Apenas certifique-se de adicionar as URLs do ngrok na variavel de ambiente:

**Arquivo**: `.env` (raiz do projeto)

```env
# URLs do ngrok (atualizar a cada nova sessao)
CORS_ORIGINS=http://localhost:3000,https://xyz789.ngrok-free.app,https://abc123.ngrok-free.app

# Configuracao de cookies para ngrok
COOKIE_DOMAIN=
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_HTTPONLY=true
```

**IMPORTANTE**: 
- `COOKIE_DOMAIN` vazio permite que o browser defina automaticamente
- `COOKIE_SECURE=true` obrigatorio para HTTPS (ngrok)
- `COOKIE_SAMESITE=none` permite cookies cross-origin

### 2. Frontend - Ajustes de API

**Arquivo**: `.env.local` (frontend)

```env
# URL do backend via ngrok
NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app/api/v1
```

**CRITICO**: Atualizar esta URL a cada nova sessao do ngrok, pois a URL muda.

### 3. Configuracao Automatica (Deteccao de Ngrok)

O sistema ja detecta ngrok automaticamente em:

**Backend** (`main.py:184-188`):
```python
# Ngrok
elif "ngrok" in origin or "ngrok" in host:
    cookie_domain = None  # Browser define automaticamente
    cookie_secure = True
    cookie_samesite = "none"
```

**Frontend** (`lib/api.js:44-49`):
```javascript
// Se esta sendo acessado via ngrok - FORCAR LOCALHOST
if (hostname.includes('ngrok')) {
    const baseUrl = 'http://localhost:8000/api/v1';
    console.log('[API] Ngrok detectado, forcando localhost:', baseUrl);
    return baseUrl;
}
```

**PROBLEMA IDENTIFICADO**: O frontend esta forcando localhost quando detecta ngrok.
Isso precisa ser corrigido para usar a URL do ngrok.

---

## Scripts Prontos

### Script 1: Iniciar Ngrok Dual (PowerShell)

**Arquivo**: `INICIAR_NGROK_DUAL.ps1`

```powershell
# Iniciar Ngrok com Dois Tuneis
# Uso: .\INICIAR_NGROK_DUAL.ps1

Write-Host "[INFO] Iniciando tuneis ngrok..." -ForegroundColor Cyan

# Verificar se ngrok esta instalado
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Ngrok nao encontrado. Instale em: https://ngrok.com/download" -ForegroundColor Red
    exit 1
}

# Verificar se servicos estao rodando
Write-Host "[INFO] Verificando servicos locais..." -ForegroundColor Yellow

$backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet
$frontendRunning = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet

if (-not $backendRunning) {
    Write-Host "[AVISO] Backend nao esta rodando na porta 8000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o backend primeiro: docker-compose up backend" -ForegroundColor Cyan
}

if (-not $frontendRunning) {
    Write-Host "[AVISO] Frontend nao esta rodando na porta 3000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o frontend primeiro: docker-compose up frontend" -ForegroundColor Cyan
}

# Iniciar tunel backend em background
Write-Host "[INFO] Iniciando tunel para backend (porta 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000 --host-header='localhost:8000'"

Start-Sleep -Seconds 2

# Iniciar tunel frontend em background
Write-Host "[INFO] Iniciando tunel para frontend (porta 3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 3000 --host-header='localhost:3000'"

Start-Sleep -Seconds 3

# Obter URLs via API do ngrok
Write-Host "`n[INFO] Obtendo URLs publicas..." -ForegroundColor Cyan

try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "TUNEIS NGROK ATIVOS" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    foreach ($tunnel in $tunnels.tunnels) {
        $port = $tunnel.config.addr -replace ".*:", ""
        $url = $tunnel.public_url
        
        if ($port -eq "8000") {
            Write-Host "`nBACKEND:" -ForegroundColor Yellow
            Write-Host "  URL Publica: $url" -ForegroundColor White
            Write-Host "  URL Local:   http://localhost:8000" -ForegroundColor Gray
        }
        elseif ($port -eq "3000") {
            Write-Host "`nFRONTEND:" -ForegroundColor Yellow
            Write-Host "  URL Publica: $url" -ForegroundColor White
            Write-Host "  URL Local:   http://localhost:3000" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "`n[IMPORTANTE] Atualize os arquivos .env:" -ForegroundColor Cyan
    Write-Host "1. Backend .env -> CORS_ORIGINS com as URLs acima" -ForegroundColor White
    Write-Host "2. Frontend .env.local -> NEXT_PUBLIC_API_URL com URL do backend" -ForegroundColor White
    Write-Host "`n[INFO] Dashboard ngrok: http://localhost:4040" -ForegroundColor Cyan
    
} catch {
    Write-Host "[AVISO] Nao foi possivel obter URLs automaticamente" -ForegroundColor Yellow
    Write-Host "[INFO] Acesse http://localhost:4040 para ver as URLs" -ForegroundColor Cyan
}

Write-Host "`n[INFO] Pressione Ctrl+C nas janelas do ngrok para encerrar" -ForegroundColor Gray
```

### Script 2: Proxy Reverso Node.js (Opcional)

**Arquivo**: `proxy-ngrok.js`

```javascript
const http = require('http');
const httpProxy = require('http-proxy');

const proxy = httpProxy.createProxyServer({});

const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, ngrok-skip-browser-warning');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Rotear para backend ou frontend
  if (req.url.startsWith('/api/')) {
    console.log(`[PROXY] Backend: ${req.method} ${req.url}`);
    proxy.web(req, res, { 
      target: 'http://localhost:8000',
      changeOrigin: true
    });
  } else {
    console.log(`[PROXY] Frontend: ${req.method} ${req.url}`);
    proxy.web(req, res, { 
      target: 'http://localhost:3000',
      changeOrigin: true,
      ws: true // WebSocket para hot reload
    });
  }
});

// WebSocket para Next.js hot reload
server.on('upgrade', (req, socket, head) => {
  console.log('[PROXY] WebSocket upgrade');
  proxy.ws(req, socket, head, { 
    target: 'http://localhost:3000',
    ws: true
  });
});

const PORT = 9000;
server.listen(PORT, () => {
  console.log(`[PROXY] Servidor rodando na porta ${PORT}`);
  console.log(`[PROXY] Frontend: http://localhost:3000 -> http://localhost:${PORT}`);
  console.log(`[PROXY] Backend:  http://localhost:8000 -> http://localhost:${PORT}/api/*`);
});
```

**Instalar dependencia**:
```powershell
docker-compose exec frontend npm install http-proxy
```

---

## Checklist de Validacao

### Pre-Requisitos

- [ ] Backend rodando em `http://localhost:8000`
- [ ] Frontend rodando em `http://localhost:3000`
- [ ] Ngrok instalado e autenticado
- [ ] Docker containers ativos

### Configuracao

- [ ] `.env` atualizado com URLs do ngrok em `CORS_ORIGINS`
- [ ] `.env` com `COOKIE_SECURE=true` e `COOKIE_SAMESITE=none`
- [ ] `.env.local` (frontend) com `NEXT_PUBLIC_API_URL` do ngrok
- [ ] Containers reiniciados apos mudancas no `.env`

### Testes de Autenticacao

1. **Teste de Login**
   ```
   URL: https://xyz789.ngrok-free.app/login
   Email: admin@hotelreal.com.br
   Senha: admin123
   ```
   - [ ] Login bem-sucedido
   - [ ] Cookie `hotel_auth_token` criado
   - [ ] Redirecionamento para dashboard

2. **Teste de Request Autenticada**
   ```
   URL: https://xyz789.ngrok-free.app (acessar qualquer pagina protegida)
   ```
   - [ ] Cookie enviado automaticamente
   - [ ] Dados carregados sem erro 401
   - [ ] Usuario permanece logado ao navegar

3. **Teste de Logout**
   ```
   Clicar em "Sair" no dashboard
   ```
   - [ ] Cookie removido
   - [ ] Redirecionamento para /login
   - [ ] Nao consegue acessar rotas protegidas

4. **Teste CORS**
   - [ ] Sem erros de CORS no console do browser
   - [ ] Header `Access-Control-Allow-Credentials: true` presente
   - [ ] Preflight OPTIONS funcionando

---

## Erros Comuns e Solucoes

### Erro 1: "CORS policy: credentials mode"

**Sintoma**: Erro no console do browser sobre CORS e credentials

**Causa**: `CORS_ORIGINS` nao inclui a URL do ngrok ou esta usando `*`

**Solucao**:
```env
# ERRADO
CORS_ORIGINS=*

# CORRETO
CORS_ORIGINS=https://xyz789.ngrok-free.app,https://abc123.ngrok-free.app
```

### Erro 2: Cookie nao esta sendo enviado

**Sintoma**: Requests retornam 401 mesmo apos login

**Causa**: Cookie com `SameSite=lax` ou `Secure=false` em HTTPS

**Solucao**:
```env
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

### Erro 3: "ngrok-skip-browser-warning"

**Sintoma**: Ngrok mostra tela de aviso antes de acessar

**Causa**: Ngrok free tier mostra aviso

**Solucao**: Header ja configurado em `lib/api.js:65`:
```javascript
'ngrok-skip-browser-warning': 'true'
```

### Erro 4: URLs do ngrok mudam a cada reinicio

**Sintoma**: Precisa reconfigurar `.env` toda vez

**Solucao**: 
- Usar ngrok pago para URLs fixas
- Ou criar script que atualiza `.env` automaticamente
- Ou usar dominio personalizado (ngrok paid)

### Erro 5: Frontend nao consegue conectar ao backend

**Sintoma**: Erro de rede ou timeout

**Causa**: `NEXT_PUBLIC_API_URL` incorreta ou backend nao acessivel

**Solucao**:
1. Verificar se backend esta rodando: `curl http://localhost:8000/health`
2. Verificar `.env.local`: `NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app/api/v1`
3. Reiniciar frontend: `docker-compose restart frontend`

---

## Boas Praticas e Seguranca

### 1. Uso Temporario

- Ngrok free tier e para TESTES, nao producao
- URLs expiram quando ngrok fecha
- Nao compartilhar URLs publicamente por muito tempo

### 2. Autenticacao

- Sistema ja usa JWT em cookies HttpOnly (seguro)
- Nao expor tokens em localStorage quando usar ngrok
- Sempre usar HTTPS (ngrok fornece automaticamente)

### 3. Rate Limiting

- Ngrok free tem limite de 40 conexoes/minuto
- Para testes com muitos usuarios, considerar plano pago

### 4. Logs

- Monitorar dashboard ngrok: `http://localhost:4040`
- Ver todas as requests em tempo real
- Debugar problemas de CORS/cookies

### 5. Variavel de Ambiente

- NUNCA commitar `.env` com URLs do ngrok
- Usar `.env.example` como template
- Documentar processo de configuracao

---

## Comandos Rapidos

### Verificar servicos locais
```powershell
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

### Reiniciar containers apos mudancas
```powershell
docker-compose restart backend frontend
```

### Ver logs em tempo real
```powershell
# Backend
docker-compose logs -f backend

# Frontend
docker-compose logs -f frontend
```

### Testar CORS manualmente
```powershell
curl -H "Origin: https://xyz789.ngrok-free.app" `
     -H "Access-Control-Request-Method: POST" `
     -H "Access-Control-Request-Headers: Content-Type" `
     -X OPTIONS `
     http://localhost:8000/api/v1/login -v
```

---

## Fluxo Completo de Configuracao

### Passo 1: Iniciar Sistema Local
```powershell
docker-compose up -d backend frontend
```

### Passo 2: Iniciar Ngrok
```powershell
.\INICIAR_NGROK_DUAL.ps1
```

### Passo 3: Copiar URLs
- Acesse `http://localhost:4040`
- Copie as URLs publicas geradas

### Passo 4: Atualizar Configuracao

**Backend** (`.env`):
```env
CORS_ORIGINS=http://localhost:3000,https://frontend-xyz.ngrok-free.app,https://backend-abc.ngrok-free.app
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
```

**Frontend** (`.env.local`):
```env
NEXT_PUBLIC_API_URL=https://backend-abc.ngrok-free.app/api/v1
```

### Passo 5: Reiniciar Containers
```powershell
docker-compose restart backend frontend
```

### Passo 6: Testar
- Acesse `https://frontend-xyz.ngrok-free.app`
- Faca login com `admin@hotelreal.com.br` / `admin123`
- Verifique se dashboard carrega corretamente

---

## Troubleshooting Avancado

### Debug de Cookies

Abra DevTools (F12) -> Application -> Cookies

Verificar:
- Nome: `hotel_auth_token`
- Domain: `.ngrok-free.app` ou vazio
- Secure: `true`
- HttpOnly: `true`
- SameSite: `None`

### Debug de CORS

Abra DevTools (F12) -> Network -> Selecione request

Verificar headers de resposta:
```
Access-Control-Allow-Origin: https://frontend-xyz.ngrok-free.app
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
```

### Debug de JWT

Backend logs:
```powershell
docker-compose logs backend | Select-String "JWT"
```

Verificar:
- Token sendo criado no login
- Token sendo validado em requests
- Erros de expiracao ou invalidade

---

## Conclusao

Este guia cobre todas as configuracoes necessarias para usar ngrok com seu sistema de gestao hoteleira, mantendo autenticacao JWT em cookies funcionando corretamente.

**Lembre-se**: URLs do ngrok mudam a cada sessao (free tier), entao voce precisara atualizar `.env` e `.env.local` sempre que reiniciar o ngrok.

Para ambiente de producao, considere:
- Ngrok pago com dominio fixo
- Cloudflare Tunnel (alternativa gratuita)
- Deploy em servidor real (AWS, Azure, DigitalOcean)
