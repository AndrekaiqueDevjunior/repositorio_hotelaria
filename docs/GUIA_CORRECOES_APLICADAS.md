# GUIA DE CORREÇÕES APLICADAS - HOTEL CABO FRIO

## RESUMO EXECUTIVO

Este documento descreve as **causas raízes** identificadas e as **correções definitivas** aplicadas para resolver:

1. ✅ **Loop de renderização no Next.js** (página recarregando constantemente)
2. ✅ **Loop de containers no Docker** (erro "Bind for 0.0.0.0:8000 failed")

---

## PARTE 1 - NEXT.JS: CORREÇÕES APLICADAS

### PROBLEMA #1: Funções nas Dependências do useEffect
**Arquivo**: `frontend/contexts/AuthContext.js`

**Causa Raiz**:
- Funções `isAuthenticated` e `hasRole` eram recriadas a cada render
- Nova referência de função → useEffect detecta mudança → executa → re-render → loop infinito

**Correção Aplicada**:
```javascript
// ANTES (ERRADO)
const isAuthenticated = () => {
  return !!user
}

// DEPOIS (CORRETO)
const isAuthenticated = useCallback(() => {
  return !!user
}, [user])
```

**Técnica**: Usar `useCallback` para memoizar funções e estabilizar referências.

---

### PROBLEMA #2: Função como Dependência no Layout
**Arquivo**: `frontend/app/(dashboard)/layout.js`

**Causa Raiz**:
- `isAuthenticated()` (função) no array de dependências
- Função recriada → useEffect executa → `router.push()` → re-render → loop

**Correção Aplicada**:
```javascript
// ANTES (ERRADO)
useEffect(() => {
  if (!loading && !isAuthenticated()) {
    router.push('/login')
  }
}, [loading, isAuthenticated, router])  // ❌ função nas dependências

// DEPOIS (CORRETO)
const authenticated = isAuthenticated()  // ✅ valor booleano

useEffect(() => {
  if (!loading && !authenticated) {
    router.push('/login')
  }
}, [loading, authenticated, router])  // ✅ valor primitivo
```

**Técnica**: Extrair valor booleano antes do useEffect, usar valor primitivo nas dependências.

---

### PROBLEMA #3: Full Page Reload no Erro 401
**Arquivo**: `frontend/lib/api.js`

**Causa Raiz**:
- `window.location.href = '/'` força full page reload
- Destroi estado do React
- Em combinação com cookies, causa loop de auth check

**Correção Aplicada**:
```javascript
// ANTES (ERRADO)
if (error.response?.status === 401) {
  window.location.href = '/'  // ❌ full reload
}

// DEPOIS (CORRETO)
if (error.response?.status === 401) {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  // ✅ AuthContext/ProtectedRoute fazem redirecionamento suave
}
```

**Técnica**: Delegar redirecionamento para componentes React (client-side navigation).

---

### PROBLEMA #4: BaseURL Recalculada em Toda Requisição
**Arquivo**: `frontend/lib/api.js`

**Causa Raiz**:
- Interceptor recalculava `getApiBaseUrl()` em TODA requisição
- Leitura de `window.location` a cada request
- Possível inconsistência e loops

**Correção Aplicada**:
```javascript
// REMOVIDO do interceptor:
const currentBaseUrl = getApiBaseUrl()
if (currentBaseUrl !== API_BASE_URL) {
  API_BASE_URL = currentBaseUrl
  config.baseURL = currentBaseUrl
}

// ✅ BaseURL calculada apenas na inicialização do módulo
```

**Técnica**: Calcular baseURL uma única vez na inicialização, não em runtime.

---

## PARTE 2 - DOCKER: CORREÇÕES APLICADAS

### PROBLEMA #1: Conflito de Porta 8000
**Arquivo**: `docker-compose.yml`

**Causa Raiz Técnica**:
```
Docker tenta bind 0.0.0.0:8000 → porta ocupada no host →
Falha → Container removido → restart: unless-stopped →
Tenta novamente → LOOP INFINITO
```

**Erro Gerado**:
```
Error response from daemon: driver failed programming external connectivity 
on endpoint: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Correção Aplicada**:
```yaml
# ANTES (ERRADO)
backend:
  ports:
    - "8000:8000"  # ❌ expõe ao host

# DEPOIS (CORRETO - Arquitetura SaaS)
backend:
  expose:
    - "8000"  # ✅ apenas rede interna
```

**Mesma correção aplicada para**:
- `postgres` (porta 5432)
- `redis` (porta 6379)
- `frontend` (porta 3000)

**Arquitetura Resultante**:
```
Internet → Nginx (8080) → Backend (8000 interno)
                       → Frontend (3000 interno)
```

---

### PROBLEMA #2: Network com Active Endpoints
**Causa Raiz**:
- Container falha mas fica "attached" à rede
- Docker não limpa endpoint automaticamente
- Próxima tentativa: "network hotel_network has active endpoints"

**Correção**:
1. Script de limpeza: `docker-cleanup-completo.ps1`
2. Desconecta containers forçadamente antes de remover rede

---

### PROBLEMA #3: Container Names Hardcoded no Nginx
**Arquivo**: `nginx-proxy.conf`

**Causa Raiz**:
```nginx
# ANTES (ERRADO)
upstream backend {
    server app_hotel_cabo_frio-backend-1:8000;  # ❌ nome específico
}
```

- Nome muda se projeto muda
- Se container não existe → Nginx falha

**Correção Aplicada**:
```nginx
# DEPOIS (CORRETO)
upstream backend {
    server backend:8000;  # ✅ service name (DNS interno)
}
```

**Técnica**: Docker Compose resolve service names via DNS interno automaticamente.

---

## COMO USAR

### 1. Quando Docker Entrar em Estado Inconsistente

Execute o script de limpeza:

```powershell
.\docker-cleanup-completo.ps1
```

O script fará automaticamente:
1. ✅ Para todos os containers
2. ✅ Remove containers órfãos
3. ✅ Limpa rede com endpoints ativos
4. ✅ Valida portas no host
5. ✅ (Opcional) Remove volumes

### 2. Iniciar Sistema Limpo

```powershell
# Build sem cache
docker-compose build --no-cache

# Subir serviços
docker-compose up -d

# Verificar logs
docker-compose logs -f

# Acessar aplicação
# http://localhost:8080
```

### 3. Acesso com Ngrok/Cloudflare

```powershell
# Subir com profile ngrok
docker-compose --profile ngrok up -d

# URL ngrok: http://localhost:4040/status
```

---

## ARQUITETURA FINAL (SaaS Profissional)

```
┌─────────────────────────────────────────────────┐
│                  INTERNET                       │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
           ┌─────────────────┐
           │  Nginx (8080)   │ ◄─── ÚNICO PONTO DE ENTRADA
           └────────┬────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐      ┌──────────────┐
│ Backend:8000  │      │ Frontend:3000│
│  (INTERNO)    │      │   (INTERNO)  │
└───────┬───────┘      └──────────────┘
        │
   ┌────┴─────┐
   ▼          ▼
┌─────┐   ┌────────┐
│Redis│   │Postgres│
│:6379│   │  :5432 │
└─────┘   └────────┘
(INTERNO)  (INTERNO)
```

**Benefícios**:
- ✅ Sem conflito de portas
- ✅ Segurança: serviços internos isolados
- ✅ Escalabilidade: fácil adicionar load balancer
- ✅ Padrão de mercado (Netflix, Spotify, Airbnb)

---

## VALIDAÇÃO PÓS-CORREÇÃO

### Verificar Next.js Sem Loop
```bash
# Abrir DevTools do navegador
# Console deve mostrar:
# ✅ Sem loops de "Carregando..."
# ✅ Sem múltiplos "router.push"
# ✅ Requisições API únicas (sem duplicação)
```

### Verificar Docker Estável
```powershell
# Containers devem ficar UP
docker-compose ps

# Logs sem erros de bind
docker-compose logs backend

# Nginx deve responder
curl http://localhost:8080/health
```

---

## TROUBLESHOOTING

### Se Next.js ainda recarrega:
1. Limpar cache do navegador (Ctrl+Shift+Del)
2. Verificar extensões do navegador (desabilitar React DevTools)
3. Verificar console do navegador para loops de useEffect

### Se Docker ainda dá erro:
1. Executar `docker-cleanup-completo.ps1`
2. Verificar portas: `netstat -ano | findstr "8080"`
3. Reiniciar Docker Desktop
4. Verificar logs: `docker-compose logs -f`

---

## CONTATO / SUPORTE

**Sistema**: Hotel Real Cabo Frio
**Versão**: 2.0 (Corrigido)
**Data**: Janeiro 2026

**Arquivos Modificados**:
- ✅ `frontend/contexts/AuthContext.js`
- ✅ `frontend/app/(dashboard)/layout.js`
- ✅ `frontend/lib/api.js`
- ✅ `docker-compose.yml`
- ✅ `nginx-proxy.conf`
- ✅ `docker-cleanup-completo.ps1` (NOVO)

---

## PRÓXIMOS PASSOS RECOMENDADOS

1. **Testes de Carga**: Validar estabilidade com múltiplos usuários
2. **Monitoramento**: Adicionar Prometheus + Grafana
3. **CI/CD**: Automatizar deploy com GitHub Actions
4. **SSL/TLS**: Configurar certificados HTTPS
5. **Backup**: Automatizar backup do Postgres

---

**FIM DO GUIA**
