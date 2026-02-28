# NGROK - Domínio Fixo Configurado

## Domínio Configurado
**jacoby-unshifted-kylie.ngrok-free.dev**

## Arquivos de Configuração Atualizados
- ✅ `.env` - Variáveis NGROK_URL e NEXT_PUBLIC_NGROK_URL
- ✅ `.NGROK_URL_CURRENT.txt` - URL atual do sistema
- ❌ Removidas todas as referências ao "sublenticulate"

## Scripts Disponíveis

### 1. INICIAR_NGROK_DOMINIO_FIXO.ps1
```powershell
./INICIAR_NGROK_DOMINIO_FIXO.ps1
```
- Atualiza arquivos de configuração
- Inicia proxy reverso na porta 9000
- Inicia ngrok com domínio fixo
- Exibe URLs de acesso

### 2. PARAR_NGROK_DOMINIO.ps1
```powershell
./PARAR_NGROK_DOMINIO.ps1
```
- Para todos os processos ngrok
- Para proxy reverso
- Limpa arquivos temporários

### 3. VERIFICAR_NGROK_DOMINIO.ps1
```powershell
./VERIFICAR_NGROK_DOMINIO.ps1
```
- Verifica configuração dos arquivos
- Confirma processos ativos
- Testa conexão com o domínio

## Arquitetura de Proxy Reverso

```
Internet → Ngrok (jacoby-unshifted-kylie.ngrok-free.dev)
         ↓
    Proxy Reverso (Porta 9000)
         ↓
    ┌─────────────────┬─────────────────┐
    │   Frontend     │    Backend      │
    │ (Porta 3000)   │  (Porta 8000)   │
    └─────────────────┴─────────────────┘
```

## URLs de Acesso

- **Sistema Completo**: https://jacoby-unshifted-kylie.ngrok-free.dev
- **Dashboard Ngrok**: http://localhost:4040
- **Frontend Local**: http://localhost:3000
- **Backend Local**: http://localhost:8000
- **Proxy Local**: http://localhost:9000

## Funcionamento

1. **Proxy Reverso**: Roda na porta 9000 e direciona:
   - `/api/*` → Backend (porta 8000)
   - Demais URLs → Frontend (porta 3000)

2. **Ngrok**: Expõe a porta 9000 para internet com domínio fixo

3. **Frontend**: Acessa backend via `/api/*` que passa pelo proxy

## Autenticação

Use as credenciais padrão:
- **Email**: admin@hotelreal.com.br
- **Senha**: admin123

## Troubleshooting

### Se o domínio não responder:
1. Verifique se o ngrok está rodando: `Get-Process ngrok`
2. Confirme o proxy está ativo: `Get-Process node`
3. Execute verificação: `./VERIFICAR_NGROK_DOMINIO.ps1`

### Se necessário reiniciar:
1. Pare tudo: `./PARAR_NGROK_DOMINIO.ps1`
2. Aguarde 10 segundos
3. Inicie novamente: `./INICIAR_NGROK_DOMINIO_FIXO.ps1`

## Importante

- O domínio é fixo e não muda a cada reinicialização
- Mantenha o authtoken do ngrok atualizado em `.env`
- O proxy garante que frontend e backend funcionem juntos
- CORS configurado para permitir acesso externo
