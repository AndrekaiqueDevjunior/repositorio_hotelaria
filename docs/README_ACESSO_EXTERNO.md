# Acesso Externo - Guia Rápido

## 🎯 Acesso Externo com LocalTunnel

**LocalTunnel** é a solução recomendada para expor o sistema para acesso externo.

### ✨ Vantagens

- ⚡ Setup instantâneo (1 comando)
- 🆓 Sem necessidade de conta/configuração
- 🔒 HTTPS automático
- 🎯 Ideal para demos e testes
- 🚀 Funciona imediatamente

### 🚀 Como Usar

```powershell
.\INICIAR_LOCALTUNNEL.ps1
```

**Resultado esperado:**
```
[OK] SISTEMA PRONTO PARA ACESSO EXTERNO!

[SHARE] URLs para compartilhar:
   Aplicacao: https://hotel-app-202601031045.loca.lt
   API:       https://hotel-api-202601031045.loca.lt

[LOGIN] Credenciais de acesso:
   Email: admin@hotelreal.com.br
   Senha: admin123
```

📖 **Documentação completa:** `GUIA_LOCALTUNNEL.md`

---

## � Passos para Usar

### 1. Executar Script

```powershell
.\INICIAR_LOCALTUNNEL.ps1
```

### 2. Aguardar Inicialização

O script irá:
1. ✅ Verificar containers Docker
2. ✅ Iniciar tunnels para backend e frontend
3. ✅ Gerar URLs públicas
4. ✅ Configurar variáveis de ambiente
5. ✅ Reiniciar containers

### 3. Compartilhar URL

```
URL para compartilhar: https://hotel-app-XXXXXX.loca.lt
Senha do tunnel: [seu IP público]
Login: admin@hotelreal.com.br / admin123
```

### 4. Parar Tunnels

Pressione `Ctrl+C` na janela do PowerShell.

### 5. Restaurar Configuração Local

```powershell
.\RESTAURAR_CONFIG_LOCAL.ps1
```

---

## 🔒 Autenticação Funcionando

LocalTunnel detecta automaticamente URLs `loca.lt` e configura cookies corretamente:

### Como funciona:

1. Login envia JWT em cookie HttpOnly
2. Cookie configurado com:
   - `Secure=true` (HTTPS apenas)
   - `HttpOnly=true` (JavaScript não acessa)
   - `SameSite=None` (cross-domain permitido)
3. Sessão persiste após refresh
4. Logout remove cookie automaticamente

📖 **Documentação completa:** `GUIA_AUTENTICACAO_COOKIE_JWT.md`

---

## 🛠️ Scripts Disponíveis

### LocalTunnel
```powershell
.\INICIAR_LOCALTUNNEL.ps1      # Iniciar tunnels
.\RESTAURAR_CONFIG_LOCAL.ps1   # Voltar para localhost
```

### Docker
```powershell
docker-compose up -d            # Iniciar containers
docker-compose down             # Parar containers
docker-compose logs -f          # Ver logs
docker-compose restart          # Reiniciar
```

---

## ⚠️ Importante

### LocalTunnel
- URLs mudam a cada execução
- Pode mostrar página de aviso na primeira vez (clicar "Continue")
- Ideal para demos de 1-2 horas
- Não usar para produção

---

## 🎯 Casos de Uso

### 📱 Demo Rápida (30 min - 2 horas)
→ **Use LocalTunnel**
```powershell
.\INICIAR_LOCALTUNNEL.ps1
```

### 🧪 Testes de Integração Externa
→ **Use LocalTunnel**
- Rápido de configurar
- Descartável

### 🎓 Apresentação/Aula
→ **Use LocalTunnel**
- Sem configuração prévia
- Funciona imediatamente

---

## 📝 Checklist de Demo

Antes de compartilhar com cliente:

- [ ] Containers rodando (`docker-compose ps`)
- [ ] Script de tunnel executado
- [ ] URL pública gerada e acessível
- [ ] Login testado
- [ ] Cookie verificado no DevTools
- [ ] Sessão persiste após refresh
- [ ] Credenciais prontas para compartilhar

---

## 🆘 Solução de Problemas

### Cookie não salva
```powershell
# Verificar configuração
cat backend\.env.docker | Select-String "COOKIE"

# Deve ter:
# COOKIE_SECURE=True
# COOKIE_SAMESITE=none
```

### CORS Error
```powershell
# Verificar origens permitidas
cat backend\.env.docker | Select-String "CORS_ORIGINS"

# Deve conter URL do tunnel
```

### Tunnel não conecta
```powershell
# Parar e reiniciar
Ctrl+C
.\INICIAR_LOCALTUNNEL.ps1
```

### Containers não respondem
```powershell
# Reiniciar containers
docker-compose restart

# Ver logs
docker-compose logs -f backend
```

---

## 📚 Documentação

- `GUIA_LOCALTUNNEL.md` - LocalTunnel detalhado
- `GUIA_AUTENTICACAO_COOKIE_JWT.md` - Autenticação completa
- `DOCKER.md` - Comandos Docker

---

## 💡 Dica Pro

**Desenvolvimento diário:**
```powershell
docker-compose up -d
# Acesse: http://localhost:3000
```

**Demo rápida:**
```powershell
.\INICIAR_LOCALTUNNEL.ps1
# Compartilhe a URL gerada
```

**Após demo:**
```powershell
Ctrl+C
.\RESTAURAR_CONFIG_LOCAL.ps1
```

---

## 🎉 Pronto para Usar!

Use LocalTunnel para expor o sistema rapidamente para demos e testes.
