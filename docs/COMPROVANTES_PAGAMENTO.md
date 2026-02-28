# 🧾 **SISTEMA DE COMPROVANTES DE PAGAMENTO**

## ✅ **O QUE JÁ EXISTE NO SISTEMA**

### **1. Voucher (Comprovante de Reserva)**
- ✅ **Arquivo**: `backend/app/api/v1/voucher_routes.py`
- ✅ **Endpoint**: `GET /vouchers/{codigo}/pdf`
- ✅ **Funcionalidade**: Gera PDF completo com dados da reserva
- ✅ **Conteúdo**: Cliente, quarto, datas, valor, código de barras

### **2. Comprovantes de Pagamento Manual**
- ✅ **Arquivo**: `backend/app/api/v1/pagamento_manual_routes.py`
- ✅ **Endpoint**: `POST /pagamento-manual/registrar`
- ✅ **Retorno**: Dados completos do comprovante
```json
{
  "comprovantes": {
    "payment_id": "24bc8366-fc31-4d6c-8555-17049a836a07",
    "authorization_code": "123456",
    "tid": "0223103744208",
    "proof_of_sale": "12345678901234567890",
    "status": "APPROVED",
    "amount": 20000
  }
}
```

### **3. Consulta de Comprovantes**
- ✅ **Endpoint**: `POST /pagamento-manual/consultar-comprovante`
- ✅ **Validação**: Consulta API Cielo por PaymentId ou TID
- ✅ **Ajuda**: `GET /pagamento-manual/ajuda-codigos`

---

## 🎯 **OPÇÕES DE COMPROVANTE DISPONÍVEIS**

### **Opção 1: Voucher PDF (Mais Completo)**
```bash
# Gerar voucher após pagamento
GET /vouchers/{codigo}/pdf
```

**Contém:**
- 🏨 **Dados do Hotel**: Nome, endereço, CNPJ
- 👤 **Dados do Cliente**: Nome, documento, contato
- 🏠 **Dados da Reserva**: Quarto, check-in/checkout, diárias
- 💰 **Valores**: Diária, total, forma de pagamento
- 📊 **Código de Barras**: Para validação rápida
- ✅ **Assinatura**: Campo para assinatura no check-in

### **Opção 2: Dados do Comprovante Cielo**
```bash
# Após pagamento manual
POST /pagamento-manual/registrar
```

**Contém:**
- 🧾 **PaymentId**: UUID único da transação
- 🔖 **AuthorizationCode**: Código de 6 dígitos
- 🎫 **TID**: ID da transação na maquininha
- 📋 **ProofOfSale**: NSU do comprovante
- ✅ **Status**: APPROVED/DECLINED
- 💵 **Amount**: Valor em centavos

### **Opção 3: Comprovante Simplificado**
```bash
# Consultar por PaymentId ou TID
POST /pagamento-manual/consultar-comprovante
```

---

## 📱 **COMO USAR NO FRONTEND**

### **1. Após Pagamento Aprovado**
```javascript
// Gerar voucher completo
const response = await api.get(`/vouchers/${reserva.codigo_reserva}/pdf`)
// Download automático do PDF
window.open(response.data.url, '_blank')
```

### **2. Mostrar Dados do Comprovante**
```javascript
// Após pagamento manual
const pagamento = await api.post('/pagamento-manual/registrar', dados)

// Exibir comprovante
setComprovante({
  payment_id: pagamento.comprovantes.payment_id,
  authorization_code: pagamento.comprovantes.authorization_code,
  tid: pagamento.comprovantes.tid,
  status: pagamento.comprovantes.status,
  valor: pagamento.comprovantes.amount / 100
})
```

### **3. Validar Comprovante**
```javascript
// Consultar antes de registrar
const validacao = await api.post('/pagamento-manual/consultar-comprovante', {
  payment_id: "24bc8366-fc31-4d6c-8555-17049a836a07"
})

if (validacao.success) {
  // Pagamento válido, pode registrar
}
```

---

## 🖨️ **EXEMPLO DE PDF GERADO**

### **Layout do Voucher:**
```
🏨 HOTEL REAL CABO FRIO
📍 Av. do Sol, 100 - Cabo Frio - RJ
📞 (22) 9999-9999 | 🌐 www.hotelreal.com.br

═════════════════════════════════════════════════════════
                        🎫 COMPROVANTE DE RESERVA
═════════════════════════════════════════════════════════

CÓDIGO: ABC123XYZ
DATA EMISSÃO: 17/01/2026 14:30

👤 DADOS DO HÓSPEDE
Nome: João da Silva
Documento: 123.456.789-00
Telefone: (22) 9999-8888
Email: joao@email.com

🏠 DADOS DA RESERVA
Quarto: 201 - Suíte Luxo
Check-in: 20/01/2026 14:00
Check-out: 22/01/2026 12:00
Diárias: 2

💰 VALORES
Diária: R$ 200,00
Total: R$ 400,00
Forma: Cartão de Crédito

📊 CÓDIGO DE BARRAS
████████████████████████████████████████
████████████████████████████████████████
████████████████████████████████████████

✅ ASSINATURA DO HÓSPEDE
_________________________________________

📌 Instruções:
- Apresente este voucher no check-in
- Válido apenas para a reserva identificada
- Não transferível
```

---

## 🔧 **COMO GERAR COMPROVANTE AGORA**

### **Passo 1: Fazer Pagamento**
```bash
# Pagamento online ou manual
curl -X POST "http://localhost:8000/api/v1/pagamentos" \
  -d '{"reserva_id": 1, "valor": 200, "metodo": "credit_card"}'
```

### **Passo 2: Gerar Voucher**
```bash
# Obter PDF do voucher
curl -X GET "http://localhost:8000/api/v1/vouchers/ABC123/pdf" \
  -o voucher.pdf
```

### **Passo 3: Consultar Comprovante**
```bash
# Validar dados na Cielo
curl -X POST "http://localhost:8000/api/v1/pagamento-manual/consultar-comprovante" \
  -d '{"payment_id": "24bc8366-fc31-4d6c-8555-17049a836a07"}'
```

---

## 🎯 **QUAL COMPROVANTE USAR?**

| Situação | Comprovante Ideal | Quando Usar |
|----------|------------------|------------|
| **Check-in** | 📄 **Voucher PDF** | Para apresentar na recepção |
| **Conferência** | 🧾 **Dados Cielo** | Para validar pagamento |
| **Disputa** | 📋 **Consulta API** | Para comprovar transação |
| **Relatório** | 📊 **Export PDF** | Para auditoria |

---

## 🚀 **PRÓXIMAS MELHORIAS**

1. **QR Code** no voucher para validação rápida
2. **Email automático** com comprovante
3. **SMS** com código de confirmação
4. **Histórico** de comprovantes por cliente
5. **Integração** com impressoras térmicas

---

**Status**: ✅ **SISTEMA DE COMPROVANTES FUNCIONAL**  
**Recomendação**: **Usar Voucher PDF para check-in + Dados Cielo para validação**

O sistema já tem tudo necessário para emitir comprovantes profissionais!
