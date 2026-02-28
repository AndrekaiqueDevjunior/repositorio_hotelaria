# Guia Serviços de Tunnel Ativos (2026)

## 🌐 Serviços Disponíveis para Acesso Externo

**serveo.com foi descontinuado** - use estas alternativas:

---

## ✅ 1. localtunnel.me (Recomendado)

**Site:** https://localtunnel.me

**Como usar:**
1. Acesse https://localtunnel.me
2. Digite: `192.168.15.20:3000`
3. Clique em "Create Tunnel"
4. Copie a URL gerada

**Exemplo:**
```
URL gerada: https://random-words.loca.lt
Compartilhe: https://random-words.loca.lt
```

**Vantagens:**
- ✅ Grátis
- ✅ Sem cadastro
- ✅ HTTPS automático
- ✅ Funciona imediatamente

---

## ✅ 2. ngrok.com

**Site:** https://ngrok.com

**Como usar:**
1. Crie conta gratuita
2. Baixe ngrok para Windows
3. Execute: `ngrok http 192.168.15.20:3000`
4. Copie a URL gerada

**Exemplo:**
```
URL gerada: https://abc123.ngrok.io
Compartilhe: https://abc123.ngrok.io
```

**Limitações:**
- ⚠️ 1GB grátis por mês
- ⚠️ Requer instalação

---

## ✅ 3. tunnelto.dev

**Site:** https://tunnelto.dev

**Como usar:**
1. Acesse https://tunnelto.dev
2. Digite: `192.168.15.20:3000`
3. Clique em "Create Tunnel"
4. Copie a URL gerada

**Vantagens:**
- ✅ Grátis
- ✅ Interface web simples
- ✅ Sem instalação

---

## ✅ 4. cloudflared (Avançado)

**Requer instalação mas muito estável**

**Instalação:**
```powershell
# Baixar cloudflared
winget install Cloudflare.cloudflared

# Configurar tunnel
cloudflared tunnel login
cloudflared tunnel create hotel-demo
cloudflared tunnel route dns hotel-demo seu-dominio.com
```

**Vantagens:**
- ✅ Muito estável
- ✅ URLs customizadas
- ✅ Da Cloudflare (confiável)

---

## ✅ 5. Bore (Sem Limites)

**Instalação via PowerShell:**
```powershell
# Requer Rust + Visual Studio Build Tools
cargo install bore-cli

# Usar
bore local 3000 --to bore.pub
```

**Vantagens:**
- ✅ Sem limites de bandwidth
- ✅ Open source
- ✅ Simples

---

## 🎯 Recomendação para Uso Imediato

### Opção A: localtunnel.me (Mais Rápido)

**Passos:**
1. Abra: https://localtunnel.me
2. Digite: `192.168.15.20:3000`
3. Copie URL gerada
4. Compartilhe

### Opção B: tunnelto.dev (Alternativa)

**Passos:**
1. Abra: https://tunnelto.dev
2. Digite: `192.168.15.20:3000`
3. Copie URL gerada
4. Compartilhe

---

## 📱 Como Compartilhar

**Exemplo com localtunnel.me:**
```
🌐 Sistema de Gestão Hoteleira
URL: https://abc123.loca.lt
Login: admin@hotelreal.com.br
Senha: admin123
```

---

## 🔧 Troubleshooting

### Se localtunnel.me não funcionar:
- Tente tunnelto.dev
- Verifique se o IP está correto: `192.168.15.20`
- Teste local primeiro: `http://192.168.15.20:3000`

### Se ngrok estiver no limite:
- Use localtunnel.me (sem limites)
- Espere reset mensal do ngrok

### Se nada funcionar:
- Verifique firewall do Windows
- Verifique firewall do roteador
- Use VPN como alternativa

---

## 📊 Comparação

| Serviço | Instalação | Limites | HTTPS | Recomendação |
|---------|------------|---------|-------|---------------|
| localtunnel.me | ❌ Não | ✅ Ilimitado | ✅ Sim | ⭐⭐⭐⭐⭐ |
| tunnelto.dev | ❌ Não | ✅ Ilimitado | ✅ Sim | ⭐⭐⭐⭐ |
| ngrok | ✅ Sim | ⚠️ 1GB/mês | ✅ Sim | ⭐⭐⭐ |
| cloudflared | ✅ Sim | ✅ Ilimitado | ✅ Sim | ⭐⭐⭐⭐ |
| Bore | ✅ Sim | ✅ Ilimitado | ❌ HTTP | ⭐⭐⭐ |

---

## 🎉 Pronto para Usar!

**Recomendação:** Use **localtunnel.me** agora mesmo!

1. Acesse: https://localtunnel.me
2. Digite: `192.168.15.20:3000`
3. Compartilhe a URL gerada

**Sistema pronto para acesso global!** 🚀
