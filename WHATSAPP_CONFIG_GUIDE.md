# Guia de Configuração - WhatsApp Notificações

## 📱 Integração WhatsApp para Resgates de Prêmios

Quando um cliente resgata um prêmio, o sistema envia automaticamente uma notificação via WhatsApp para o número configurado com todos os detalhes do resgate.

---

## 🔧 Configuração do Twilio

### **Passo 1: Criar Conta no Twilio**

1. Acesse: https://www.twilio.com/try-twilio
2. Crie uma conta gratuita (trial)
3. Verifique seu número de telefone

### **Passo 2: Obter Credenciais**

No Dashboard do Twilio (https://console.twilio.com/):

1. **Account SID**: Copie o SID da conta
2. **Auth Token**: Copie o token de autenticação
3. **WhatsApp Sandbox**: Ative o WhatsApp Sandbox

### **Passo 3: Configurar WhatsApp Sandbox**

1. Acesse: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Siga as instruções para conectar seu WhatsApp ao sandbox
3. Envie a mensagem de ativação para o número do Twilio
4. Copie o número do sandbox (formato: `whatsapp:+14155238886`)

---

## ⚙️ Configuração no Sistema

### **Arquivo `.env`**

Adicione as seguintes variáveis ao arquivo `.env` do backend:

```bash
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_NOTIFICACAO_NUMERO=+5511968029600
```

**Descrição das variáveis:**
- `TWILIO_ACCOUNT_SID`: SID da sua conta Twilio
- `TWILIO_AUTH_TOKEN`: Token de autenticação
- `TWILIO_WHATSAPP_FROM`: Número WhatsApp do Twilio (sandbox ou número próprio)
- `WHATSAPP_NOTIFICACAO_NUMERO`: Seu número para receber notificações (formato: +55DDXXXXXXXXX)

---

## 📦 Instalação

### **1. Instalar Dependência**

A biblioteca Twilio já foi adicionada ao `requirements.txt`:

```bash
twilio==8.10.0
```

### **2. Instalar no Docker**

```bash
# Reconstruir o container backend
docker-compose build backend

# Ou instalar diretamente no container rodando
docker exec hotel_backend pip install twilio==8.10.0
```

### **3. Reiniciar Backend**

```bash
docker restart hotel_backend
```

---

## 📨 Formato da Mensagem

Quando um prêmio é resgatado, a seguinte mensagem é enviada:

```
🎁 *NOVO RESGATE DE PRÊMIO*

👤 *Cliente:* João Silva
📱 *Telefone:* +5511987654321
📍 *Endereço:* Rua Exemplo, 123 - Cabo Frio/RJ

🏆 *Prêmio:* Voucher R$ 50,00
⭐ *Pontos usados:* 500
🔑 *Código do resgate:* RES-000001

📦 *Mensagem do cliente:*
"Olá, me chamo João Silva, acumulei 500 pontos e resgatei o prêmio Voucher R$ 50,00.

Eu moro em Rua Exemplo, 123 - Cabo Frio/RJ.

O código do resgate é RES-000001.

Gostaria de saber como vai ser feita a entrega do item. Enviam via Correios?"

---
⚠️ *Ação necessária:* Entre em contato com o cliente para combinar a entrega.
```

---

## 🧪 Teste de Envio

### **Teste Manual via Python**

```python
# Dentro do container backend
docker exec -it hotel_backend python

# No Python shell:
from app.services.whatsapp_service import get_whatsapp_service
import asyncio

async def test():
    service = get_whatsapp_service()
    result = await service.enviar_notificacao_resgate_premio(
        cliente_nome="João Teste",
        cliente_telefone="+5511987654321",
        cliente_endereco="Rua Teste, 123",
        premio_nome="Prêmio Teste",
        pontos_usados=100,
        codigo_resgate="RES-TEST"
    )
    print(result)

asyncio.run(test())
```

### **Teste via Endpoint**

Faça um resgate de prêmio normal através da API:

```bash
POST /api/v1/premios/resgatar
{
  "cliente_id": 1,
  "premio_id": 1
}
```

Se configurado corretamente, você receberá a notificação no WhatsApp.

---

## 🔍 Logs e Monitoramento

### **Verificar Logs**

```bash
# Ver logs do backend
docker logs hotel_backend | grep -i whatsapp

# Ver logs em tempo real
docker logs -f hotel_backend | grep -i whatsapp
```

### **Mensagens de Log**

**Sucesso:**
```
INFO: WhatsApp Service inicializado com sucesso
INFO: Notificação WhatsApp enviada - Resgate: 1, SID: SMxxxxxxxx
```

**Aviso (não configurado):**
```
WARNING: Twilio não configurado. Defina TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN no .env
WARNING: Falha ao enviar WhatsApp - Resgate: 1, Erro: Serviço WhatsApp não configurado
```

**Erro:**
```
ERROR: Erro ao enviar notificação WhatsApp: [detalhes do erro]
```

---

## 💰 Custos

### **Conta Trial (Gratuita)**
- ✅ Mensagens ilimitadas para números verificados
- ✅ Sandbox WhatsApp incluído
- ⚠️ Mensagens incluem prefixo "Sent from your Twilio trial account"

### **Conta Paga**
- **WhatsApp Business API**: ~$0.005 por mensagem (varia por país)
- **Número próprio**: ~$1.00/mês
- **Sem prefixo trial**

**Estimativa para 100 resgates/mês:**
- Trial: **Grátis** (com prefixo)
- Paga: **~$0.50/mês** (sem prefixo)

---

## 🔒 Segurança

### **Boas Práticas**

1. **Nunca commitar credenciais**
   ```bash
   # .gitignore já deve incluir:
   .env
   .env.local
   ```

2. **Usar variáveis de ambiente**
   - Produção: Definir no servidor/Docker
   - Desenvolvimento: Arquivo `.env` local

3. **Rotacionar tokens periodicamente**
   - Trocar `AUTH_TOKEN` a cada 90 dias
   - Revogar tokens antigos no Twilio Console

---

## 🚨 Troubleshooting

### **Erro: "Twilio não configurado"**
**Causa:** Variáveis de ambiente não definidas  
**Solução:** Adicionar `TWILIO_ACCOUNT_SID` e `TWILIO_AUTH_TOKEN` no `.env`

### **Erro: "Unable to create record"**
**Causa:** Número de destino não verificado (conta trial)  
**Solução:** Verificar o número no Twilio Console ou usar conta paga

### **Erro: "Invalid 'To' Phone Number"**
**Causa:** Formato de número incorreto  
**Solução:** Usar formato internacional: `+5511968029600`

### **Mensagem não chega**
**Checklist:**
1. ✅ Twilio configurado corretamente?
2. ✅ Número conectado ao sandbox?
3. ✅ Logs mostram "enviado com sucesso"?
4. ✅ Verificar status da mensagem no Twilio Console

---

## 📞 Suporte

- **Twilio Docs**: https://www.twilio.com/docs/whatsapp
- **Twilio Console**: https://console.twilio.com/
- **Status Twilio**: https://status.twilio.com/

---

## ✅ Checklist de Configuração

- [ ] Conta Twilio criada
- [ ] WhatsApp Sandbox ativado
- [ ] Número conectado ao sandbox
- [ ] Credenciais copiadas
- [ ] Variáveis adicionadas ao `.env`
- [ ] Biblioteca `twilio` instalada
- [ ] Backend reiniciado
- [ ] Teste de envio realizado
- [ ] Mensagem recebida no WhatsApp

---

**Status:** ✅ Implementação completa  
**Prioridade:** 🟡 Opcional (melhora UX)  
**Impacto:** Notificação automática de resgates  
**Custo:** Gratuito (trial) ou ~$0.50/mês (produção)
