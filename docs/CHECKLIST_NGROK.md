# Checklist de Configuracao Ngrok

## Pre-Requisitos

- [ ] Docker instalado e rodando
- [ ] Ngrok instalado (`ngrok --version`)
- [ ] Ngrok autenticado (`ngrok config add-authtoken SEU_TOKEN`)
- [ ] Backend rodando em `http://localhost:8000`
- [ ] Frontend rodando em `http://localhost:3000`

## Configuracao Inicial

### Backend (.env)

- [ ] `CORS_ORIGINS` inclui URLs do ngrok
- [ ] `COOKIE_SECURE=true`
- [ ] `COOKIE_SAMESITE=none`
- [ ] `COOKIE_DOMAIN=` (vazio)
- [ ] `COOKIE_HTTPONLY=true`

### Frontend (frontend/.env.local)

- [ ] `NEXT_PUBLIC_API_URL` aponta para backend ngrok
- [ ] URL termina com `/api/v1`

### Containers

- [ ] Containers reiniciados apos mudancas no .env
- [ ] Sem erros nos logs do backend
- [ ] Sem erros nos logs do frontend

## Tuneis Ngrok

- [ ] Tunel backend ativo (porta 8000)
- [ ] Tunel frontend ativo (porta 3000)
- [ ] Dashboard acessivel em `http://localhost:4040`
- [ ] URLs HTTPS geradas

## Testes de Funcionalidade

### 1. Health Check

- [ ] Backend health: `https://backend-url.ngrok-free.app/health`
- [ ] Resposta: `{"status": "healthy"}`

### 2. Login

- [ ] Acesso ao frontend: `https://frontend-url.ngrok-free.app`
- [ ] Pagina de login carrega sem erros
- [ ] Login com `admin@hotelreal.com.br` / `admin123`
- [ ] Redirecionamento para dashboard

### 3. Cookies

Abra DevTools (F12) > Application > Cookies:

- [ ] Cookie `hotel_auth_token` criado
- [ ] Domain: `.ngrok-free.app` ou vazio
- [ ] Secure: `true`
- [ ] HttpOnly: `true`
- [ ] SameSite: `None`

### 4. CORS

Abra DevTools (F12) > Console:

- [ ] Sem erros de CORS
- [ ] Sem erros "credentials mode"

Abra DevTools (F12) > Network > Selecione request:

- [ ] Header `Access-Control-Allow-Origin` presente
- [ ] Header `Access-Control-Allow-Credentials: true`

### 5. Navegacao

- [ ] Dashboard carrega dados
- [ ] Navegacao entre paginas funciona
- [ ] Usuario permanece logado
- [ ] Sem erros 401 em requests

### 6. Logout

- [ ] Botao "Sair" funciona
- [ ] Cookie removido
- [ ] Redirecionamento para /login
- [ ] Nao consegue acessar rotas protegidas

## Validacao Automatica

- [ ] Script `VALIDAR_NGROK.ps1` executado sem erros
- [ ] Script `TESTAR_AUTENTICACAO_NGROK.ps1` executado sem erros

## Problemas Comuns Resolvidos

- [ ] URLs do ngrok atualizadas em .env
- [ ] Containers reiniciados apos mudancas
- [ ] Sem cache do browser interferindo
- [ ] Ngrok nao mostra tela de aviso (header configurado)

## Documentacao

- [ ] URLs atuais documentadas
- [ ] Cliente informado sobre URLs temporarias
- [ ] Procedimento de atualizacao de URLs documentado

## Seguranca

- [ ] URLs ngrok nao commitadas no Git
- [ ] `.env` no `.gitignore`
- [ ] Cliente ciente que URLs sao temporarias
- [ ] Limite de uso do ngrok free conhecido

## Proximos Passos (Opcional)

- [ ] Considerar ngrok pago para URLs fixas
- [ ] Considerar Cloudflare Tunnel (alternativa gratuita)
- [ ] Planejar deploy em servidor real para producao

---

## Notas

- URLs do ngrok free mudam a cada sessao
- Atualizar .env e .env.local sempre que reiniciar ngrok
- Usar scripts de validacao antes de compartilhar com cliente
- Dashboard ngrok util para debug: `http://localhost:4040`
