# Ngrok Quick Start - Guia Rapido

## Inicio Rapido (5 minutos)

### 1. Iniciar Sistema Local
```powershell
docker-compose up -d backend frontend
```

### 2. Iniciar Ngrok (Dois Tuneis)
```powershell
.\INICIAR_NGROK_DUAL.ps1
```

### 3. Copiar URLs
Acesse `http://localhost:4040` e copie as URLs geradas:
- Backend: `https://abc123.ngrok-free.app`
- Frontend: `https://xyz789.ngrok-free.app`

### 4. Configurar Backend
Edite `.env`:
```env
CORS_ORIGINS=http://localhost:3000,https://xyz789.ngrok-free.app,https://abc123.ngrok-free.app
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
```

### 5. Configurar Frontend
Crie `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app/api/v1
```

### 6. Reiniciar Containers
```powershell
docker-compose restart backend frontend
```

### 7. Testar
Acesse `https://xyz789.ngrok-free.app` e faca login:
- Email: `admin@hotelreal.com.br`
- Senha: `admin123`

---

## Validacao Automatica

```powershell
.\VALIDAR_NGROK.ps1
```

Este script verifica:
- Servicos locais rodando
- Tuneis ngrok ativos
- Configuracao de .env
- Endpoints respondendo

---

## Teste de Autenticacao

```powershell
.\TESTAR_AUTENTICACAO_NGROK.ps1
```

Testa:
- Health check
- Login
- Cookies
- CORS

---

## Troubleshooting Rapido

### Erro: "CORS policy"
**Solucao**: Adicione URL do frontend em `CORS_ORIGINS` no `.env`

### Erro: Cookie nao enviado
**Solucao**: Configure no `.env`:
```env
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

### Erro: 401 apos login
**Solucao**: Verifique `NEXT_PUBLIC_API_URL` no `frontend/.env.local`

### Erro: URLs mudam sempre
**Solucao**: Ngrok free muda URLs a cada sessao. Use ngrok pago para URLs fixas.

---

## Comandos Uteis

### Ver logs
```powershell
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Reiniciar servicos
```powershell
docker-compose restart backend frontend
```

### Parar ngrok
Pressione `Ctrl+C` nas janelas do ngrok

### Dashboard ngrok
`http://localhost:4040`

---

## Alternativa: Tunel Unico (Proxy)

```powershell
.\INICIAR_NGROK_PROXY.ps1
```

Uma unica URL para frontend e backend.

---

## Arquivos de Configuracao

- `.env.ngrok.example` - Template para backend
- `frontend/.env.local.ngrok.example` - Template para frontend
- `GUIA_NGROK_COMPLETO.md` - Documentacao completa

---

## Seguranca

- Ngrok free e apenas para TESTES
- URLs expiram quando ngrok fecha
- Nao compartilhar URLs publicamente
- Sempre usar HTTPS (ngrok fornece automaticamente)

---

## Suporte

Para documentacao completa, veja: `GUIA_NGROK_COMPLETO.md`
