# Guia Acesso Externo Internet

## 🌐 Problema: Acesso de Fora da Rede Local

**ERR_CONNECTION_TIMED_OUT** acontece quando você tenta acessar de outra rede.

## 🎯 3 Soluções para Acesso Global

### 1. VPN (Mais Simples)

**Como funciona:**
- Instale VPN no seu celular/dispositivo externo
- Conecte na mesma rede do seu computador
- Acesse como se estivesse na rede local

**Passos:**
1. Instale VPN (ex: AnyDesk, TeamViewer, VPN do Windows)
2. No celular, conecte na VPN do seu PC
3. Acesse: `http://192.168.15.20:3000`

**Vantagens:**
- ✅ Sem instalar nada novo
- ✅ Usa rede existente
- ✅ Totalmente grátis

---

### 2. Serviços Online Gratuitos

#### Opção A: serveo.com (Recomendado)

**Site:** https://serveo.com

**Passos:**
1. Acesse https://serveo.com
2. Clique em "Start"
3. Digite: `192.168.15.20:3000`
4. Copie a URL gerada
5. Compartilhe a URL

**Exemplo:**
```
URL gerada: https://abc123.serveo.net
Compartilhe: https://abc123.serveo.net
```

#### Opção B: localtunnel.me

**Site:** https://localtunnel.me

**Passos:**
1. Acesse https://localtunnel.me
2. Digite: `192.168.15.20:3000`
3. Copie a URL gerada

#### Opção C: ngrok.com

**Site:** https://ngrok.com

**Limitação:** 1GB grátis por mês

---

### 3. Instalar Ferramentas (Avançado)

#### Bore (Sem Limites)

**Requisitos:** Rust + Visual Studio Build Tools

**Instalação:**
```powershell
# Instalar Rust
winget install Rustlang.Rustup

# Instalar Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools

# Instalar Bore
cargo install bore-cli

# Executar
.\INICIAR_SERVIDOR_EXTERNO_INTERNET.ps1
```

---

## 📋 Status Atual do Sistema

**✅ Sistema configurado:**
- Frontend: `http://192.168.15.20:3000`
- Backend: `http://192.168.15.20:8000`
- CORS: `*` (permite qualquer origem)
- Login: `admin@hotelreal.com.br` / `admin123`

## 🎯 Recomendação

**Para uso imediato:**
1. Use **serveo.com** (mais simples)
2. Ou use **VPN** se já tiver configurada

**Para uso frequente:**
- Instale **Bore** (sem limites)

## 📱 Como Compartilhar

**Exemplo com serveo.com:**
```
🌐 Acesso ao Sistema Hotel
URL: https://abc123.serveo.net
Login: admin@hotelreal.com.br
Senha: admin123
```

## 🔧 Troubleshooting

### Se VPN não funcionar:
- Verifique se o celular está realmente conectado na VPN
- Teste ping: `ping 192.168.15.20`

### Se serveo.com não funcionar:
- Verifique se o IP está correto: `192.168.15.20`
- Teste local primeiro: `http://192.168.15.20:3000`

### Se nada funcionar:
- Verifique firewall do Windows
- Verifique firewall do roteador
- Use localhost para testes: `http://localhost:3000`

## 🎉 Pronto para Uso!

**Escolha a opção mais fácil para você:**
1. **VPN** - Se já tiver
2. **serveo.com** - Se quiser rápido e grátis
3. **Bore** - Se precisar sem limites

O sistema está funcionando, só precisa expor para internet! 🚀
