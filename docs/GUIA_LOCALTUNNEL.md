# Guia LocalTunnel - Acesso Remoto Temporário

## 🎯 Objetivo

Expor rapidamente o sistema de gestão hoteleira (frontend + backend) para acesso externo usando **LocalTunnel**, com autenticação JWT em cookies funcionando corretamente.

## ✨ O que é LocalTunnel?

LocalTunnel é uma ferramenta que cria túneis HTTPS para `localhost`, permitindo:

- ✅ Acesso externo sem configurar firewall/roteador
- ✅ HTTPS automático (necessário para cookies Secure)
- ✅ URLs públicas temporárias
- ✅ Grátis e sem necessidade de conta
- ✅ Ideal para demos e testes

## 🚀 Inicio Rápido

### 1. Pré-requisitos

**Node.js instalado no container frontend:**

O LocalTunnel será executado usando `npx` (vem com Node.js).

### 2. Iniciar Sistema

```powershell
# Execute o script de inicialização
.\INICIAR_LOCALTUNNEL.ps1
```

O script irá:
1. ✅ Verificar se containers estão rodando
2. ✅ Iniciar LocalTunnel para backend (porta 8000)
3. ✅ Iniciar LocalTunnel para frontend (porta 3000)
4. ✅ Gerar URLs públicas únicas
5. ✅ Atualizar variáveis de ambiente automaticamente
6. ✅ Reiniciar containers com nova configuração
7. ✅ Exibir URLs para compartilhar

### 3. Resultado Esperado

```
✅ SISTEMA PRONTO PARA ACESSO EXTERNO!

🌍 URLs para compartilhar:
   📱 Aplicação: https://hotel-app-202601031045.loca.lt
   🔌 API:       https://hotel-api-202601031045.loca.lt

🔑 Credenciais de acesso:
   Email: admin@hotelreal.com.br
   Senha: admin123
```

### 4. Compartilhar com Cliente

Envie a URL da aplicação para o cliente:
```
https://hotel-app-XXXXXX.loca.lt
```

**Primeira vez:** LocalTunnel pode mostrar página de aviso. Clique em **"Click to Continue"**.

## 📋 Como Funciona

### Fluxo Completo

```
Internet → LocalTunnel → Docker Container
         (HTTPS)         (HTTP localhost)

Cliente acessa: https://hotel-app-123.loca.lt
      ↓
LocalTunnel recebe e encaminha para: localhost:3000
      ↓
Container frontend responde
      ↓
LocalTunnel retorna resposta via HTTPS
```

### Configuração Automática

**Backend (.env.docker):**
```env
CORS_ORIGINS=https://hotel-api-XXX.loca.lt,https://hotel-app-XXX.loca.lt
FRONTEND_URL=https://hotel-app-XXX.loca.lt
COOKIE_SECURE=True
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=https://hotel-api-XXX.loca.lt/api/v1
```

### Autenticação

O sistema detecta automaticamente URLs do LocalTunnel (`loca.lt`) e configura cookies:
- `Secure=true` - HTTPS obrigatório ✅
- `HttpOnly=true` - JavaScript não acessa ✅
- `SameSite=None` - Cross-domain permitido ✅
- `Domain=` - Browser define automaticamente ✅

## 🔄 Restaurar Configuração Local

Após demo/testes, volte para configuração local:

```powershell
# Executar script de restauração
.\RESTAURAR_CONFIG_LOCAL.ps1
```

Isso irá:
1. Restaurar `CORS_ORIGINS` para `localhost`
2. Restaurar configuração de cookies para desenvolvimento
3. Reiniciar containers

## 🛠️ Comandos Úteis

### Verificar Status dos Containers

```powershell
docker-compose ps
```

### Ver Logs

```powershell
# Backend
docker-compose logs -f backend

# Frontend
docker-compose logs -f frontend

# Ambos
docker-compose logs -f
```

### Parar LocalTunnel

Pressione `Ctrl+C` na janela onde executou `INICIAR_LOCALTUNNEL.ps1`

### Matar Processos LocalTunnel Manualmente

```powershell
# PowerShell
Get-Process | Where-Object { $_.ProcessName -like "*localtunnel*" } | Stop-Process -Force
```

### Reiniciar Containers

```powershell
docker-compose restart backend frontend
```

## ⚠️ Problemas Comuns

### LocalTunnel mostra "This site can't be reached"

**Causa:** Tunnel não foi iniciado corretamente ou expirou.

**Solução:**
```powershell
# Parar script (Ctrl+C)
# Executar novamente
.\INICIAR_LOCALTUNNEL.ps1
```

### Página de aviso do LocalTunnel

**Sintoma:** Primeira vez acessando mostra página "Friendly Reminder".

**Solução:**
- É normal! LocalTunnel faz isso para evitar abuso
- Clique em **"Click to Continue"**
- Página só aparece na primeira vez

### Cookie não salva

**Causa:** HTTPS não está ativo ou configuração incorreta.

**Solução:**
1. Verificar se URL começa com `https://`
2. Verificar DevTools → Network → Response Headers
3. Deve ter: `Set-Cookie: hotel_auth_token=...; Secure; HttpOnly; SameSite=None`

### CORS Error

**Causa:** Backend não reconhece origem do frontend.

**Solução:**
```powershell
# Verificar arquivo .env.docker
cat backend\.env.docker | Select-String "CORS_ORIGINS"

# Deve conter as URLs do LocalTunnel
# Se não tiver, execute novamente:
.\INICIAR_LOCALTUNNEL.ps1
```

### Tunnel fecha sozinho

**Causa:** LocalTunnel gratuito pode ter limitações.

**Solução:**
- O script tem auto-restart embutido
- Se continuar caindo, considere usar Cloudflare Tunnel (mais estável)

## 🔒 Segurança

### O que está protegido

✅ HTTPS automático via LocalTunnel  
✅ Cookie HttpOnly (não acessível via JavaScript)  
✅ Cookie Secure (apenas HTTPS)  
✅ SameSite=None (CSRF protegido com HTTPS)  
✅ CORS restrito às URLs específicas  
✅ Token blacklist no logout  

### O que NÃO fazer

❌ Usar LocalTunnel para produção (apenas demos)  
❌ Compartilhar URLs publicamente (expiram)  
❌ Deixar sistema exposto 24/7  
❌ Usar para dados sensíveis reais  

## 📊 Comparação: LocalTunnel vs Cloudflare Tunnel

| Recurso | LocalTunnel | Cloudflare Tunnel |
|---------|-------------|-------------------|
| Setup | Instantâneo | Requer configuração |
| Estabilidade | Média | Alta |
| Velocidade | Boa | Excelente |
| URL | Aleatória | Customizável |
| Persistência | Temporária | Permanente |
| Custo | Grátis | Grátis |
| Ideal para | Demos rápidas | Produção/Staging |

## 🎯 Casos de Uso

### ✅ Bom para:

- Demonstrações rápidas para clientes
- Testes de autenticação remota
- Validação de funcionalidades
- Acesso temporário de desenvolvedores externos
- Prototipação e testes A/B

### ❌ Não recomendado para:

- Produção
- Dados sensíveis reais
- Aplicações 24/7
- Alta disponibilidade
- Compliance regulatório

## 📝 Checklist de Demo

Antes de compartilhar com cliente:

- [ ] Script `INICIAR_LOCALTUNNEL.ps1` executado com sucesso
- [ ] URLs públicas geradas e exibidas
- [ ] Containers backend e frontend rodando
- [ ] Testar login em `https://hotel-app-XXX.loca.lt`
- [ ] Verificar cookie no DevTools
- [ ] Confirmar que sessão persiste após refresh
- [ ] Compartilhar URL e credenciais com cliente
- [ ] Informar sobre página de aviso (primeira vez)

## 🔧 Troubleshooting Avançado

### Ver URLs ativas

```powershell
# Ler arquivo de URLs salvo
cat .localtunnel\urls.json | ConvertFrom-Json
```

### Verificar processos LocalTunnel

```powershell
Get-Process | Where-Object { $_.ProcessName -like "*node*" } | Format-Table Id, ProcessName, StartTime
```

### Testar conexão

```powershell
# Testar backend
curl https://hotel-api-XXX.loca.lt/health

# Esperado:
# { "status": "healthy", "version": "1.0.0" }
```

### Logs detalhados

```powershell
# Backend com detalhes
docker-compose logs --tail=100 backend

# Frontend com detalhes
docker-compose logs --tail=100 frontend
```

## 🎬 Exemplo de Sessão Completa

```powershell
# 1. Iniciar sistema
PS> .\INICIAR_LOCALTUNNEL.ps1

🚀 Iniciando LocalTunnel...
📦 Containers rodando
🔗 Iniciando tunnel para backend...
🔗 Iniciando tunnel para frontend...

✅ SISTEMA PRONTO!

🌍 URLs:
   Aplicação: https://hotel-app-202601031045.loca.lt
   API:       https://hotel-api-202601031045.loca.lt

# 2. Compartilhar URL com cliente
# Enviar: https://hotel-app-202601031045.loca.lt

# 3. Cliente acessa e faz login
# Email: admin@hotelreal.com.br
# Senha: admin123

# 4. Após demo, restaurar configuração local
PS> Ctrl+C  # Parar tunnels
PS> .\RESTAURAR_CONFIG_LOCAL.ps1

✅ Configuração local restaurada
🏠 Acesse: http://localhost:3000
```

## 📚 Referências

- [LocalTunnel Documentation](https://theboroer.github.io/localtunnel-www/)
- [LocalTunnel GitHub](https://github.com/localtunnel/localtunnel)
- [NPX Documentation](https://docs.npmjs.com/cli/v8/commands/npx)

## 💡 Dicas

1. **URLs mudam a cada execução**: Salve as URLs do arquivo `.localtunnel\urls.json`
2. **Página de aviso é normal**: Sempre aparece na primeira vez
3. **Sessão persiste**: Cookie funciona perfeitamente com LocalTunnel
4. **Use Cloudflare para longo prazo**: LocalTunnel é para testes rápidos
5. **Mantenha script rodando**: Não feche a janela do PowerShell

## 🆘 Suporte

**Problemas com LocalTunnel:**
- Verificar se Node.js está disponível: `npx --version`
- Reinstalar: `npm install -g localtunnel`

**Problemas com autenticação:**
- Consultar: `GUIA_AUTENTICACAO_COOKIE_JWT.md`
- Verificar logs: `docker-compose logs backend`

**Problemas com containers:**
- Verificar status: `docker-compose ps`
- Reconstruir: `docker-compose up -d --build`
