# Guia Bore - Alternativa Sem Limites

## 🎯 O que é Bore?

**Bore** é um túnel TCP moderno e gratuito, sem limites de bandwidth.

- ✅ Gratuito e open source
- ✅ Sem limites de bandwidth (diferente do ngrok)
- ✅ Sem necessidade de conta
- ✅ Executa no host Windows
- ✅ Simples e rápido

**GitHub:** https://github.com/ekzhang/bore

## 🚀 Instalação

### Opção 1: Via Cargo (Rust)

```powershell
# Instalar Rust (se não tiver)
winget install Rustlang.Rustup

# Instalar Bore
cargo install bore-cli
```

### Opção 2: Baixar Binário

1. Acesse: https://github.com/ekzhang/bore/releases
2. Baixe `bore-windows-amd64.exe`
3. Renomeie para `bore.exe`
4. Adicione ao PATH

## 🎯 Uso Rápido

```powershell
.\INICIAR_BORE_SIMPLES.ps1
```

**Resultado:**
```
[OK] SISTEMA PRONTO PARA ACESSO EXTERNO!

[SHARE] URLs para compartilhar:
   Aplicacao: http://bore.pub:12345
   API:       http://bore.pub:54321

[LOGIN] Credenciais de acesso:
   Email: admin@hotelreal.com.br
   Senha: admin123
```

## 📋 Como Funciona

```
Internet → bore.pub:PORT → localhost:PORT → Docker Container
         (HTTP)           (Host Windows)    (Container)
```

**Fluxo:**
1. Bore executa no host Windows
2. Conecta em `localhost:8000` e `localhost:3000`
3. Docker expõe essas portas para o host
4. Bore cria túnel público em `bore.pub`

## ⚠️ Importante

### HTTP vs HTTPS

- ⚠️ Bore usa **HTTP** (não HTTPS)
- Cookies configurados como `Secure=False`
- Ideal para demos, não para produção com dados sensíveis

### Portas Aleatórias

- URLs mudam a cada execução
- Portas geradas aleatoriamente (10000-60000)

## 🆚 Comparação

| Feature | Bore | ngrok | LocalTunnel |
|---------|------|-------|-------------|
| Bandwidth | ✅ Ilimitado | ❌ Limitado | ✅ Ilimitado |
| HTTPS | ❌ HTTP | ✅ HTTPS | ✅ HTTPS |
| Conta | ❌ Não | ⚠️ Opcional | ❌ Não |
| Docker | ✅ OK | ✅ OK | ❌ 503 |
| Estabilidade | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

## 🎯 Casos de Uso

### ✅ Bom para:
- Demos rápidas
- Testes de integração
- Desenvolvimento com equipe remota
- Evitar limites de bandwidth

### ❌ Não use para:
- Produção com dados sensíveis (sem HTTPS)
- Aplicações que requerem HTTPS obrigatório
- URLs permanentes

## 🔧 Troubleshooting

### Bore não instalado

```powershell
# Instalar Rust
winget install Rustlang.Rustup

# Reiniciar PowerShell

# Instalar Bore
cargo install bore-cli

# Verificar
bore --version
```

### Porta em uso

O script gera portas aleatórias automaticamente, evitando conflitos.

### Conexão recusada

```powershell
# Verificar se containers estão rodando
docker-compose ps

# Verificar logs
docker-compose logs backend
docker-compose logs frontend
```

## 🛑 Parar Bore

Pressione `Ctrl+C` no terminal onde executou o script.

## 🔄 Restaurar Localhost

```powershell
.\RESTAURAR_CONFIG_LOCAL.ps1
```

## 💡 Dicas

1. **URLs curtas:** Anote as URLs geradas no início
2. **Estabilidade:** Deixe janela do PowerShell aberta
3. **Testes:** Teste primeiro em `http://localhost:3000` antes de expor

## 📚 Links Úteis

- GitHub: https://github.com/ekzhang/bore
- Documentação: https://github.com/ekzhang/bore#readme
- Alternativas: Cloudflare Tunnel (HTTPS, mais complexo)

## 🎉 Pronto!

Bore é ideal quando você:
- Excedeu limite do ngrok
- LocalTunnel não funciona
- Precisa de algo simples e sem limites
