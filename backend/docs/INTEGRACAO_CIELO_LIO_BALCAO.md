# 🏨 Integração Cielo LIO para Pagamento no Balcão - Hotel Cabo Frio

## 📋 Resumo da Documentação Cielo

### 🔍 Como Validar Pagamento no Balcão

A Cielo oferece duas soluções principais para pagamento presencial no balcão:

#### 1. **Cielo LIO On - Máquina Inteligente**
- **Tecnologia**: Android com touchscreen + impressora integrada
- **Conectividade**: Wi-Fi + 4G (venda em qualquer lugar)
- **Pagamentos aceitos**: 
  - Débito e Crédito (à vista e parcelado)
  - PIX e QR Code
  - Voucher
  - Pagamento por aproximação (NFC)
  - Mais de 80 bandeiras

#### 2. **Formas de Integração**

**A) Integração via Deep Link (Recomendado para Hotel)**
```javascript
// JSON do pedido
const pedido = {
  "accessToken": "SEU_ACCESS_TOKEN",
  "clientID": "SEU_CLIENT_ID", 
  "reference": "RESERVA-RCF-202601-AB4526",
  "email": "cliente@email.com",
  "installments": 1,
  "items": [{
    "name": "Hospedagem Suite Premium",
    "quantity": 3,
    "sku": "SUITE-PREMIUM-3DIAS",
    "unitOfMeasure": "unidade",
    "unitPrice": 15000  // R$ 150,00 em centavos
  }],
  "paymentCode": "CREDITO_AVISTA",  // ou DEBITO_AVISTA, PIX_QRCODE
  "value": "15000"
}

// Converter para Base64 e chamar
const base64 = btoa(JSON.stringify(pedido))
const uri = `lio://payment?request=${base64}&urlCallback=hotel://response`
```

**B) Integração Remota via API REST**
```bash
# Criar pedido
POST https://api.cielo.com.br/order-management/v1/orders
Headers:
  Client-ID: seu_client_id
  Access-Token: seu_access_token  
  Merchant-ID: seu_merchant_id

Body:
{
  "number": "RCF-202601-AB4526",
  "reference": "RESERVA-RCF-202601-AB4526",
  "payment_code": "CREDITO_AVISTA",
  "status": "DRAFT",
  "items": [{
    "sku": "SUITE-PREMIUM-3DIAS",
    "name": "Hospedagem Suite Premium",
    "unit_price": 15000,
    "quantity": 3,
    "unit_of_measure": "EACH"
  }],
  "price": 45000
}
```

## 🎯 **Implementação Sugerida para o Hotel**

### **Fluxo de Pagamento no Balcão:**

1. **Check-in → Identificar Reserva**
   - Sistema busca reserva pendente de pagamento
   - Exibe: "Pagamento na chegada: R$ XXX,XX"

2. **Iniciar Pagamento Cielo LIO**
   - Frontend abre app Cielo LIO via Deep Link
   - Envia dados da reserva como referência

3. **Processamento na Máquina**
   - Cliente insere/cartão aproxima
   - Validação biométrica/senha
   - Autorização online em tempo real

4. **Retorno Automático**
   - App Cielo LIO retorna para sistema do hotel
   - Dados: authorization_code, payment_id, status

5. **Confirmação no Sistema**
   - Atualiza status do pagamento
   - Confirma reserva automaticamente
   - Libera check-in

### **Códigos de Pagamento Disponíveis:**

```javascript
// Cartões
"CREDITO_AVISTA"     // Crédito à vista
"CREDITO_PARCELADO_LOJA"  // Crédito parcelado loja  
"CREDITO_PARCELADO_EMISSOR" // Crédito parcelado emissor
"DEBITO_AVISTA"      // Débito à vista

// Pix/QR Code
"PIX_QRCODE"         // PIX QR Code
"PIX"               // PIX dinâmico

// Vouchers
"VOUCHER_ALIMENTACAO" // Vale alimentação
"VOUCHER_REFEICAO"   // Vale refeição
"VOUCHER_COMBUSTIVEL" // Vale combustível

// Outros
"CASH"              // Dinheiro
```

### **Dados de Retorno Importantes:**

```json
{
  "createdAt": "Jan 20, 2026 11:53:00 AM",
  "id": "ba583f85-9252-48b5-8fed-12719ff058b9",
  "status": "PAID",
  "paidAmount": 15000,
  "payments": [{
    "authCode": "140126",
    "brand": "Visa", 
    "cieloCode": "799871",
    "installments": 0,
    "mask": "424242-4242",
    "merchantCode": "0000000000000003",
    "terminal": "69000007",
    "paymentFields": {
      "primaryProductName": "CREDITO",
      "secondaryProductName": "A VISTA",
      "statusCode": "1",
      "authorizationCode": "140126"
    }
  }]
}
```

## 🔧 **Pré-requisitos para Implementação**

### **1. Credenciais Necessárias:**
- Client-ID (Portal Desenvolvedores Cielo)
- Access Token (gerado automaticamente)
- Merchant ID (número do estabelecimento)
- Terminal Cielo LIO On ativo

### **2. Hardware:**
- Cielo LIO On (máquina inteligente)
- Conexão Wi-Fi ou 4G estável
- Android 8+ (integrado na máquina)

### **3. Software:**
- App customizado na Cielo Store OU
- Integração via Deep Link do sistema existente

## 📊 **Benefícios para o Hotel**

### **✅ Vantagens Operacionais:**
- **Validação em tempo real** - Sem risco de fraude
- **Integração automática** - Atualiza sistema do hotel
- **Múltiplas formas de pagamento** - 80+ bandeiras aceitas
- **Mobilidade** - Atendimento no quarto ou recepção
- **Conciliação automática** - Relatórios integrados

### **✅ Benefícios Financeiros:**
- **Taxas competitivas** - Cielo tem as melhores do mercado
- **Redução de erros** - Processo automatizado
- **Segurança PCI-DSS** - Dados mascarados automaticamente
- **Estornos simplificados** - Cancelamento integrado

### **✅ Experiência do Cliente:**
- **Agilidade no check-in** - Pagamento rápido
- **Múltiplas opções** - PIX, aproximação, parcelado
- **Comprovante digital** - Recebido por e-mail
- **Processo transparente** - Cliente vê aprovação na hora

## 🚀 **Próximos Passos**

### **Fase 1 - Setup (1-2 semanas)**
1. [ ] Solicitar Cielo LIO On para o hotel
2. [ ] Criar conta no Portal Desenvolvedores
3. [ ] Gerar credenciais (Client-ID, Access Token)
4. [ ] Configurar ambiente sandbox para testes

### **Fase 2 - Desenvolvimento (2-3 semanas)**
1. [ ] Implementar integração Deep Link no frontend
2. [ ] Criar endpoint para receber retorno Cielo
3. [ ] Atualizar schema Pagamento com campos LIO
4. [ ] Desenvolver fluxo de pagamento no balcão

### **Fase 3 - Testes (1 semana)**
1. [ ] Testes em ambiente sandbox
2. [ ] Validação de todos os payment codes
3. [ ] Teste de estorno e cancelamento
4. [ ] Homologação com Cielo

### **Fase 4 - Produção (1 semana)**
1. [ ] Migração para ambiente produção
2. [ ] Treinamento da equipe
3. [ ] Go-live com acompanhamento
4. [ ] Monitoramento e ajustes

## 📞 **Suporte Cielo**
- **Portal Desenvolvedores**: desenvolvedores.cielo.com.br
- **Documentação LIO**: https://developercielo.github.io/manual/cielo-lio
- **Help Desk**: devcielo.zendesk.com
- **Exemplo Código**: https://github.com/cielolabsbr/SampleAutomacaoComercial1.2

---

## 🎯 **Conclusão**

A integração com Cielo LIO On é a solução ideal para pagamento no balcão do Hotel Cabo Frio, oferecendo:

- ✅ **Validação segura** em tempo real
- ✅ **Integração completa** com o sistema atual  
- ✅ **Mobilidade** para atendimento no hotel
- ✅ **Múltiplas formas** de pagamento
- ✅ **Conformidade** PCI-DSS automática

Com a credencial Merchant ID já configurada no sistema, o hotel está pronto para iniciar a implementação.
