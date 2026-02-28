# Pagamento Manual Maquininha - Guia de Implementação

## 📋 Overview

Sistema implementado para registrar pagamentos feitos na maquininha (POS) fora do sistema, com validação real na API Cielo.

## 🔧 Configuração

### 1) Credenciais Cielo (Produção)

No arquivo `.env`:
```bash
CIELO_MERCHANT_ID=1fbbf5bb-5d2d-4ca3-a9df-7f1f6f29a9b6
CIELO_MERCHANT_KEY=BQILMLUUAWUXXCHLBZQJNSPNNOAYVNSPRCZVFRZL
CIELO_MODE=production  # Mudar para produção
```

### 2) URLs da API Cielo

- **Produção**: `https://api.cieloecommerce.cielo.com.br/`
- **Consulta Produção**: `https://apiquery.cieloecommerce.cielo.com.br/`
- **Sandbox**: `https://apisandbox.cieloecommerce.cielo.com.br/`

## 🚀 Fluxo de Implementação

### Passo 1: Cliente paga na maquininha
```
Cliente → Cartão na maquininha
Maquininha → "APROVADO - Código: 123456"
Maquininha → Imprime comprovante com:
- PaymentId: 24bc8366-fc31-4d6c-8555-17049a836a07
- TID: 0223103744208
- AuthorizationCode: 123456
- ProofOfSale: 674532
```

### Passo 2: Recepcionista consulta no sistema
```
Recepcionista → Admin → "Consultar Comprovante"
├─ Digita: PaymentId ou TID
└─ Sistema → Valida na Cielo (produção)
```

### Passo 3: Sistema valida
```
GET https://apiquery.cieloecommerce.cielo.com.br/1/sales/{PaymentId}
Headers:
  MerchantId: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  MerchantKey: 0123456789012345678901234567890123456789

Resposta:
{
  "Payment": {
    "PaymentId": "24bc8366-fc31-4d6c-8555-17049a836a07",
    "Status": 2,  // 2 = Aprovado
    "AuthorizationCode": "123456",
    "Tid": "0223103744208",
    "ProofOfSale": "674532",
    "Amount": 85000  // Valor em centavos
  }
}
```

### Passo 4: Registrar pagamento
```
POST /api/v1/pagamentos/registrar-manual-maquininha
{
  "reserva_id": 123,
  "codigo_autorizacao": "24bc8366-fc31-4d6c-8555-17049a836a07",  // PaymentId
  "valor": 850.00,
  "metodo": "credit_card"
}
```

### Passo 5: Sistema processa
```
1. ✅ Valida reserva
2. ✅ Consulta PaymentId na Cielo (produção)
3. ✅ Verifica Status = 2 (Aprovado)
4. ✅ Cria pagamento com status APROVADO
5. ✅ Confirma reserva automaticamente
6. ✅ Gera voucher
```

## 📚 Endpoints Implementados

### 1) Registrar Pagamento Manual
```http
POST /api/v1/pagamentos/registrar-manual-maquininha
```

**Request:**
```json
{
  "reserva_id": 123,
  "codigo_autorizacao": "24bc8366-fc31-4d6c-8555-17049a836a07",
  "valor": 850.00,
  "metodo": "credit_card"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Pagamento registrado e confirmado",
  "pagamento_id": 456,
  "voucher": {
    "codigo": "HR-20250117-000001"
  },
  "comprovantes": {
    "payment_id": "24bc8366-fc31-4d6c-8555-17049a836a07",
    "authorization_code": "123456",
    "tid": "0223103744208",
    "proof_of_sale": "674532",
    "status": 2,
    "amount": 85000
  }
}
```

### 2) Consultar Comprovante
```http
POST /api/v1/pagamentos/consultar-comprovante
```

**Request:**
```json
{
  "payment_id": "24bc8366-fc31-4d6c-8555-17049a836a07"
}
```

**Response:**
```json
{
  "found": true,
  "payment_id": "24bc8366-fc31-4d6c-8555-17049a836a07",
  "authorization_code": "123456",
  "tid": "0223103744208",
  "proof_of_sale": "674532",
  "status": 2,
  "status_text": "Aprovado",
  "amount": 85000,
  "captured_amount": 85000,
  "captured_date": "2025-01-17T14:30:00"
}
```

### 3) Ajuda sobre Códigos
```http
GET /api/v1/pagamentos/ajuda-codigos
```

**Response:**
```json
{
  "titulo": "Como registrar pagamento da maquininha",
  "passos": [
    "1. Cliente paga na maquininha",
    "2. Pegue o comprovante da maquininha",
    "3. Use um destes códigos:",
    "   - PaymentId: UUID (ex: 24bc8366-fc31-4d6c-8555-17049a836a07)",
    "   - TID: Número da transação (ex: 0223103744208)",
    "   - AuthorizationCode: NÃO pode ser consultado",
    "4. Digite o código no sistema",
    "5. Sistema valida na Cielo e registra"
  ]
}
```

## ⚠️ Limitações Importantes

### ❌ O que NÃO funciona
- **Busca por AuthorizationCode**: Cielo não oferece consulta direta pelo código de 6 dígitos
- **Listar vendas recentes**: Não existe endpoint para últimas transações
- **Integração direta com maquininha**: Apenas webhook (se configurado)

### ✅ O que funciona
- **Consulta por PaymentId**: `GET /1/sales/{PaymentId}`
- **Consulta por TID**: `GET /1/sales/tid/{Tid}`
- **Webhook automático**: Se configurado no suporte Cielo
- **Validação em tempo real**: Produção ou Sandbox

## 🛠️ Arquivos Modificados

### Backend
- `cielo_service.py`: Adicionado consulta por TID e URLs de produção
- `pagamento_repo.py`: Método `create_manual()` para pagamentos já feitos
- `pagamento_manual_routes.py`: Novos endpoints para registro manual
- `main.py`: Include das novas rotas
- `.env`: Configurado para produção

## 📝 Como Usar na Prática

### Para o Recepcionista
1. **Cliente paga** na maquininha
2. **Pegue o comprovante** impresso
3. **Use o PaymentId** (UUID) ou **TID** do comprovante
4. **Digite no sistema** no campo "Consultar Comprovante"
5. **Sistema valida** e mostra os dados
6. **Clique em "Registrar Pagamento"**
7. **Reserva confirmada** automaticamente

### Exemplo de Comprovante
```
COMPROVANTE DE PAGAMENTO
========================
Hotel Real Cabo Frio
Data: 17/01/2025 14:30
Valor: R$ 850,00

PaymentId: 24bc8366-fc31-4d6c-8555-17049a836a07
TID: 0223103744208
AuthorizationCode: 123456
ProofOfSale: 674532
Status: APROVADO
```

## 🔍 Testes

### Sandbox (Testes)
```bash
# Mudar para sandbox
CIELO_MODE=sandbox

# Testar com PaymentId simulado
curl -X POST http://localhost:8000/api/v1/pagamentos/consultar-comprovante \
  -H "Content-Type: application/json" \
  -d '{"payment_id": "CIELO_SANDBOX_20250117_1"}'
```

### Produção
```bash
# Já configurado no .env
CIELO_MODE=production

# Usar PaymentId real da maquininha
curl -X POST http://seusite.com/api/v1/pagamentos/consultar-comprovante \
  -H "Content-Type: application/json" \
  -d '{"payment_id": "24bc8366-fc31-4d6c-8555-17049a836a07"}'
```

## 🎯 Benefícios

- ✅ **Comprovação real**: Validado na API Cielo produção
- ✅ **Sem refatoração**: Não mexe nos endpoints existentes
- ✅ **Auditável**: Fica registrado quem registrou e quando
- ✅ **Automático**: Confirma reserva e gera voucher
- ✅ **Seguro**: Usa credenciais reais da Cielo

## 📞 Suporte

Em caso de problemas:
1. Verifique as credenciais no `.env`
2. Confirme que `CIELO_MODE=production`
3. Teste com um PaymentId real
4. Verifique os logs do backend

---

**Status**: ✅ IMPLEMENTADO E TESTADO
