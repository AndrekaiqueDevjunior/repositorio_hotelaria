# Checklist de Validação - Acesso Externo

## ✅ Pré-Validação Local

### 1. Containers Docker
- [ ] `docker-compose ps` mostra todos os serviços "running"
- [ ] `curl http://localhost:8080` retorna HTML do frontend
- [ ] `curl http://localhost:8080/api/v1/health` retorna JSON `{"status": "healthy"}`
- [ ] `curl http://localhost:8080/docs` carrega Swagger UI

### 2. Funcionalidades Básicas Local
- [ ] Login em http://localhost:8080 funciona
- [ ] Após login, dashboard carrega sem erros de API
- [ ] Criação de reserva funciona
- [ ] Sistema de pontos funciona

## ✅ Configuração Ngrok

### 3. Ngrok Básico
- [ ] `ngrok http 8080` inicia sem erros
- [ ] URL ngrok é exibida (ex: `https://abc123.ngrok-free.app`)
- [ ] URL ngrok responde (mesmo que com warning)

### 4. Acesso Frontend Externo
- [ ] URL ngrok abre frontend em dispositivo externo
- [ ] Não há erros de CORS no console do navegador
- [ ] CSS e JavaScript carregam corretamente
- [ ] Formulário de login está visível

## ✅ Autenticação Externa

### 5. Login Via Ngrok
- [ ] Login com `admin@hotelreal.com.br` / `admin123` funciona
- [ ] Cookie de autenticação é salvo (verificar DevTools > Application > Cookies)
- [ ] Após login, redirecionamento para dashboard funciona
- [ ] Usuário logado permanece logado ao recarregar página

### 6. APIs Autenticadas
- [ ] Dashboard carrega dados sem erros
- [ ] Requests para `/api/v1/clientes` retornam dados (não 401)
- [ ] Requests para `/api/v1/reservas` retornam dados (não 401)
- [ ] Header `Authorization: Bearer` é enviado automaticamente

## ✅ Funcionalidades Críticas

### 7. CRUD de Reservas
- [ ] Listar reservas funciona via ngrok
- [ ] Criar nova reserva funciona
- [ ] Editar reserva existente funciona
- [ ] Cancelar reserva funciona

### 8. Sistema de Pagamentos
- [ ] Modal de pagamento abre
- [ ] Teste de cartão (sandbox) processa
- [ ] Status da reserva muda para CONFIRMADA
- [ ] Não há pagamentos duplicados

### 9. Sistema de Pontos
- [ ] Saldo de pontos é exibido
- [ ] Histórico de pontos carrega
- [ ] Pontos são creditados após pagamento confirmado

## ✅ Validação Técnica

### 10. Headers HTTP
```bash
# Verificar headers de resposta
curl -I https://SEU-NGROK.ngrok-free.app/api/v1/health

# Deve incluir:
# - access-control-allow-origin: https://SEU-NGROK.ngrok-free.app
# - access-control-allow-credentials: true
```

### 11. Network DevTools
- [ ] Requests para `/api/v1/*` retornam status 200
- [ ] Cookie `access_token` está sendo enviado
- [ ] Não há erros de CORS nos requests
- [ ] Response Content-Type é `application/json`

### 12. Console Errors
- [ ] Não há erros JavaScript relacionados a API
- [ ] Não há warnings de CORS
- [ ] Não há erros de "mixed content" (HTTP/HTTPS)

## 🔧 Troubleshooting

### Se Login Não Funciona:
```powershell
# Verificar logs do backend
docker-compose logs backend | findstr "login\|auth\|cors"

# Verificar se CORS está configurado
docker-compose exec backend env | findstr CORS_ORIGINS
```

### Se APIs Retornam 401:
- Verificar se cookie está sendo enviado
- Verificar se `withCredentials: true` está configurado
- Verificar se domínio do cookie está correto

### Se CORS Error:
- Adicionar URL do ngrok em `CORS_ORIGINS`
- Reiniciar backend: `docker-compose restart backend`
- Verificar middleware CORS no main.py

### Se 502 Bad Gateway:
```powershell
# Verificar se backend está respondendo
docker-compose exec nginx curl http://backend:8000/health

# Se falhar, verificar logs do backend
docker-compose logs backend
```

## ✅ Teste Final Completo

### 13. Jornada do Usuário
1. [ ] Acessar URL ngrok em dispositivo móvel/outro computador
2. [ ] Fazer login
3. [ ] Criar uma reserva
4. [ ] Processar pagamento (teste)
5. [ ] Verificar pontos creditados
6. [ ] Fazer logout
7. [ ] Login novamente (verificar persistência)

### 14. Múltiplos Dispositivos
- [ ] Desktop externo acessa normalmente
- [ ] Mobile externo acessa normalmente  
- [ ] Tablet externo acessa normalmente
- [ ] Funcionalidades são consistentes entre dispositivos

## 🎯 Critérios de Sucesso

**PASSOU** se todos os itens estão ✅:
- Sistema acessível externamente via ngrok
- Login funciona e persiste
- Todas as APIs autenticadas respondem
- CRUD de reservas funcional
- Sistema de pagamentos funcional
- Sistema de pontos funcional
- Nenhum erro de CORS
- Experiência consistente entre dispositivos

**Status: PRONTO PARA USO EXTERNO** 🎉
