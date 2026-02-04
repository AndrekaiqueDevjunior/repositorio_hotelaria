# AUDITORIA TÉCNICA: Sinergia Frontend ↔ Backend
## Sistema Hotel Real Cabo Frio - PMS

**Consultor**: Arquiteto Sênior de Software  
**Data**: 03/01/2026  
**Escopo**: Semântica, Estados, Idempotência, Contratos API  
**Versão**: 1.0

---

## 📋 RESUMO EXECUTIVO

### Diagnóstico Geral

| Aspecto | Status | Risco |
|---------|--------|-------|
| **Sinergia Frontend ↔ Backend** | ⚠️ PARCIAL | MÉDIO |
| **Semântica de Estados** | ❌ INCONSISTENTE | ALTO |
| **Idempotência** | ⚠️ PARCIAL | MÉDIO |
| **Autoridade do Backend** | ⚠️ VIOLADA | ALTO |
| **Cobertura de Endpoints** | ✅ BOA | BAIXO |

### Veredicto Final

# 🟡 OPERACIONAL COM RISCO

**Justificativa**: Sistema possui estrutura adequada mas frontend não respeita completamente as regras do backend, especialmente para check-in (bug crítico). Não há validação semântica completa antes de habilitar ações.

---

## 1️⃣ AUDITORIA DE SINERGIA FRONTEND ↔ BACKEND

### 1.1 Status Usados

**Backend define 5 estados de Reserva**:
```python
# reserva_repo.py
ESTADOS_VALIDOS = ["PENDENTE", "CONFIRMADA", "HOSPEDADO", "CHECKED_OUT", "CANCELADO"]
```

**Frontend reconhece**:
```javascript
// page.js - getStatusColor()
const statusColors = {
  'PENDENTE': 'bg-yellow-100 text-yellow-800',
  'CONFIRMADA': 'bg-green-100 text-green-800',
  'HOSPEDADO': 'bg-blue-100 text-blue-800',
  'CHECKED_OUT': 'bg-gray-100 text-gray-800',
  'CANCELADO': 'bg-red-100 text-red-800'
}
```

**Resultado**: ✅ CORRETO - Todos os 5 estados reconhecidos

---

### 1.2 Regras de Habilitação de Botões

#### BOTÃO CHECK-IN

**Regra do Backend** (`reserva_repo.py:181-188`):
```python
async def checkin(self, reserva_id: int):
    if reserva.status not in ("PENDENTE", "CONFIRMADA"):
        raise ValueError("Apenas reservas pendentes ou confirmadas podem fazer check-in")
```

**Regra do Validator** (`validators.py:97-119`):
```python
def validar_checkin(reserva):
    # Deve estar confirmada
    if reserva.status != "CONFIRMADA":
        raise HTTPException(400, "Check-in só pode ser feito em reservas confirmadas")
```

**Regra do Frontend** (`page.js:1305-1310`):
```javascript
disabled={
    checkinLoadingId === reserva.id || 
    reserva.status === 'HOSPEDADO' || 
    reserva.status === 'CHECKED_OUT' ||
    reserva.status === 'CANCELADO'
}
```

### ❌ INCONSISTÊNCIA CRÍTICA DETECTADA

| Aspecto | Backend | Frontend | Resultado |
|---------|---------|----------|-----------|
| Status PENDENTE | ⚠️ Aceita (repo) / ❌ Rejeita (validator) | ✅ Habilita | **PERIGOSO** |
| Status CONFIRMADA | ✅ Aceita | ✅ Habilita | OK |
| Pagamento aprovado | ✅ Valida no `confirmar()` | ❌ NÃO VALIDA | **BUG CRÍTICO** |
| Status HOSPEDADO | ❌ Rejeita | ❌ Desabilita | OK |
| Status CHECKED_OUT | ❌ Rejeita | ❌ Desabilita | OK |
| Status CANCELADO | ❌ Rejeita | ❌ Desabilita | OK |

**Problema**: Frontend habilita check-in para status `PENDENTE`, mas deveria exigir `CONFIRMADA` + pagamento aprovado.

---

#### BOTÃO CHECK-OUT

**Regra do Backend** (`reserva_repo.py:212-219`):
```python
async def checkout(self, reserva_id: int):
    if reserva.status != "HOSPEDADO":
        raise ValueError("Apenas reservas hospedadas podem fazer check-out")
```

**Regra do Frontend** (`page.js:1326-1329`):
```javascript
disabled={
    checkoutLoadingId === reserva.id || 
    reserva.status !== 'HOSPEDADO'
}
```

**Resultado**: ✅ CORRETO - Frontend respeita regra do backend

---

#### BOTÃO CANCELAR

**Regra do Backend** (`reserva_repo.py:309-317`):
```python
async def cancelar(self, reserva_id: int):
    if reserva.status not in ("PENDENTE", "CONFIRMADA", "HOSPEDADO"):
        raise ValueError("Apenas reservas pendentes, confirmadas ou hospedadas podem ser canceladas")
```

**Regra do Frontend** (`page.js:1347`):
```javascript
disabled={cancelLoadingId === reserva.id || !['PENDENTE', 'HOSPEDADO'].includes(reserva.status)}
```

### ❌ INCONSISTÊNCIA DETECTADA

| Status | Backend | Frontend | Resultado |
|--------|---------|----------|-----------|
| PENDENTE | ✅ Permite | ✅ Permite | OK |
| CONFIRMADA | ✅ Permite | ❌ **NÃO PERMITE** | **ERRO** |
| HOSPEDADO | ✅ Permite | ✅ Permite | OK |

**Problema**: Frontend não permite cancelar reserva `CONFIRMADA`, mas backend aceita.

---

#### BOTÃO PAGAR

**Regra do Backend**: Qualquer reserva não finalizada pode receber pagamento.

**Regra do Frontend** (`page.js:1297`):
```javascript
disabled={reserva.status === 'CANCELADO' || reserva.status === 'CHECKED_OUT'}
```

**Resultado**: ✅ CORRETO

---

### 1.3 Quadro Resumo de Sinergia

| Ação | Backend Permite | Frontend Habilita | Sinergia |
|------|-----------------|-------------------|----------|
| **Check-in PENDENTE** | ❌ (validator) | ✅ Sim | ❌ FALHA |
| **Check-in CONFIRMADA** | ✅ Sim | ✅ Sim | ✅ OK |
| **Check-in sem pagamento** | ❌ Não | ✅ Sim | ❌ FALHA CRÍTICA |
| **Checkout HOSPEDADO** | ✅ Sim | ✅ Sim | ✅ OK |
| **Checkout outros** | ❌ Não | ❌ Não | ✅ OK |
| **Cancelar PENDENTE** | ✅ Sim | ✅ Sim | ✅ OK |
| **Cancelar CONFIRMADA** | ✅ Sim | ❌ Não | ⚠️ RESTRITIVO |
| **Cancelar HOSPEDADO** | ✅ Sim | ✅ Sim | ✅ OK |
| **Pagar PENDENTE** | ✅ Sim | ✅ Sim | ✅ OK |
| **Pagar CONFIRMADA** | ✅ Sim | ✅ Sim | ✅ OK |

**Score de Sinergia**: 7/10 (70%)

---

## 2️⃣ SEMÂNTICA DE ESTADOS

### AÇÃO: CHECK-IN

```
┌─────────────────────────────────────────────────────────────┐
│ SEMÂNTICA CORRETA PARA CHECK-IN                             │
├─────────────────────────────────────────────────────────────┤
│ PERMITIDO SOMENTE SE:                                       │
│   ✓ reserva.status === "CONFIRMADA"                         │
│   ✓ EXISTS pagamento WHERE status IN (APROVADO, PAGO)       │
│   ✓ quarto.status === "LIVRE"                               │
│   ✓ data_atual >= checkin_previsto - 1 dia                  │
│                                                             │
│ PROIBIDO SE:                                                │
│   ✗ reserva.status === "PENDENTE"                           │
│   ✗ reserva.status === "HOSPEDADO"                          │
│   ✗ reserva.status === "CHECKED_OUT"                        │
│   ✗ reserva.status === "CANCELADO"                          │
│   ✗ nenhum pagamento aprovado                               │
│                                                             │
│ TRANSIÇÃO:                                                  │
│   CONFIRMADA → HOSPEDADO                                    │
│                                                             │
│ MENSAGEM AO USUÁRIO:                                        │
│   Se PENDENTE: "Aguardando pagamento para liberar check-in" │
│   Se sem pagamento: "Pagamento não aprovado"                │
│   Se OK: "Check-in disponível"                              │
└─────────────────────────────────────────────────────────────┘
```

**Status atual**: ❌ Frontend não valida pagamento aprovado

---

### AÇÃO: CHECK-OUT

```
┌─────────────────────────────────────────────────────────────┐
│ SEMÂNTICA CORRETA PARA CHECK-OUT                            │
├─────────────────────────────────────────────────────────────┤
│ PERMITIDO SOMENTE SE:                                       │
│   ✓ reserva.status === "HOSPEDADO"                          │
│   ✓ saldo_devedor <= 0 (conta paga)                         │
│                                                             │
│ PROIBIDO SE:                                                │
│   ✗ reserva.status !== "HOSPEDADO"                          │
│   ✗ saldo_devedor > 0 (backend bloqueia)                    │
│                                                             │
│ TRANSIÇÃO:                                                  │
│   HOSPEDADO → CHECKED_OUT                                   │
│                                                             │
│ MENSAGEM AO USUÁRIO:                                        │
│   Se não HOSPEDADO: "Check-in necessário antes do checkout" │
│   Se saldo devedor: "Realize o pagamento pendente"          │
│   Se OK: "Checkout disponível"                              │
└─────────────────────────────────────────────────────────────┘
```

**Status atual**: ✅ Frontend correto para status, ⚠️ não valida saldo devedor na UI

---

### AÇÃO: CANCELAR

```
┌─────────────────────────────────────────────────────────────┐
│ SEMÂNTICA CORRETA PARA CANCELAR                             │
├─────────────────────────────────────────────────────────────┤
│ PERMITIDO SOMENTE SE:                                       │
│   ✓ reserva.status IN (PENDENTE, CONFIRMADA, HOSPEDADO)     │
│                                                             │
│ PROIBIDO SE:                                                │
│   ✗ reserva.status === "CHECKED_OUT"                        │
│   ✗ reserva.status === "CANCELADO"                          │
│                                                             │
│ TRANSIÇÃO:                                                  │
│   PENDENTE → CANCELADO                                      │
│   CONFIRMADA → CANCELADO                                    │
│   HOSPEDADO → CANCELADO (com liberação de quarto)           │
│                                                             │
│ MENSAGEM AO USUÁRIO:                                        │
│   Se CHECKED_OUT: "Reserva já finalizada"                   │
│   Se CANCELADO: "Reserva já cancelada"                      │
│   Se OK: "Confirma cancelamento?"                           │
└─────────────────────────────────────────────────────────────┘
```

**Status atual**: ⚠️ Frontend não permite cancelar CONFIRMADA (mais restritivo)

---

### AÇÃO: PAGAR

```
┌─────────────────────────────────────────────────────────────┐
│ SEMÂNTICA CORRETA PARA PAGAR                                │
├─────────────────────────────────────────────────────────────┤
│ PERMITIDO SOMENTE SE:                                       │
│   ✓ reserva.status NOT IN (CANCELADO, CHECKED_OUT)          │
│                                                             │
│ PROIBIDO SE:                                                │
│   ✗ reserva.status === "CANCELADO"                          │
│   ✗ reserva.status === "CHECKED_OUT"                        │
│                                                             │
│ EFEITO COLATERAL:                                           │
│   Se APROVADO: reserva.status → CONFIRMADA                  │
│   Gera voucher automaticamente                              │
│                                                             │
│ MENSAGEM AO USUÁRIO:                                        │
│   Se já pago: Exibir status do pagamento anterior           │
│   Se CANCELADO: "Reserva cancelada - pagamento não aceito"  │
└─────────────────────────────────────────────────────────────┘
```

**Status atual**: ✅ Frontend correto

---

## 3️⃣ IDEMPOTÊNCIA

### 3.1 Análise por Operação

#### CREATE RESERVA

**Backend** (`reserva_routes.py:49-118`):
```python
@router.post("", status_code=201)
async def criar_reserva(
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    # ✅ Verifica idempotência
    if idempotency_key:
        cached = await check_idempotency(idempotency_key)
        if cached:
            return JSONResponse(content=cached["body"], status_code=cached["status_code"])
    
    # ✅ Lock Redis para evitar race condition
    async with redis_lock(lock_key, timeout=10):
        nova_reserva = await service.create(reserva)
```

**Frontend** (`page.js:658-721`):
```javascript
const handleSubmit = async (e) => {
    setLoading(true)  // ✅ Bloqueia durante request
    try {
        const res = await api.post('/reservas', payload)
        // ❌ NÃO ENVIA X-Idempotency-Key
    }
}
```

| Aspecto | Backend | Frontend | Resultado |
|---------|---------|----------|-----------|
| **Header Idempotency-Key** | ✅ Suporta | ❌ Não envia | ⚠️ INCOMPLETO |
| **Lock Redis** | ✅ Implementado | N/A | ✅ OK |
| **Bloqueia duplo clique** | N/A | ✅ setLoading(true) | ✅ OK |

---

#### CHECK-IN

**Backend** (`reserva_service.py:52-60`):
```python
async def checkin(self, reserva_id: int):
    # ❌ NÃO TEM PROTEÇÃO DE IDEMPOTÊNCIA
    return await self.reserva_repo.checkin(reserva_id)
```

**Frontend** (`page.js:518-552`):
```javascript
const handleCheckin = async () => {
    setCheckinLoadingId(selectedReserva.id)  // ✅ Bloqueia botão
    const res = await api.post(`/reservas/${selectedReserva.id}/checkin`, {...})
}
```

| Aspecto | Backend | Frontend | Resultado |
|---------|---------|----------|-----------|
| **Idempotência nativa** | ❌ Não | N/A | ⚠️ RISCO |
| **Validação de status** | ✅ Sim | ✅ Sim | ✅ OK |
| **Bloqueia duplo clique** | N/A | ✅ setCheckinLoadingId | ✅ OK |
| **Re-execução segura** | ⚠️ Atualiza para HOSPEDADO novamente | N/A | ⚠️ RISCO BAIXO |

**Nota**: Backend valida status antes, então re-execução falharia com erro 400.

---

#### CHECK-OUT

**Backend** (`reserva_service.py:63-117`):
```python
async def checkout(self, reserva_id: int):
    # ✅ PROTEÇÃO IMPLEMENTADA
    if reserva_atual.status == "CHECKED_OUT":
        print(f"Reserva {reserva_id} já está em CHECKED_OUT - retornando sem processar")
        return await self.reserva_repo.get_by_id(reserva_id)  # Idempotente!
    
    # ✅ Verifica se já creditou pontos
    transacao_existente = await db.transacaopontos.find_first(
        where={"reservaId": reserva_id, "tipo": "CREDITO", "origem": "CHECKOUT"}
    )
    
    if not transacao_existente:
        await self._creditar_pontos_checkout(reserva)  # Só credita uma vez
```

**Frontend** (`page.js:566-609`):
```javascript
const handleCheckout = async () => {
    setCheckoutLoadingId(selectedReserva.id)  // ✅ Bloqueia botão
}
```

| Aspecto | Backend | Frontend | Resultado |
|---------|---------|----------|-----------|
| **Idempotência nativa** | ✅ Sim (verifica status) | N/A | ✅ EXCELENTE |
| **Proteção pontos duplicados** | ✅ Sim | N/A | ✅ EXCELENTE |
| **Bloqueia duplo clique** | N/A | ✅ setCheckoutLoadingId | ✅ OK |

---

#### PAGAMENTO

**Backend** (`pagamento_service.py:16-113`):
```python
async def create(self, dados: PagamentoCreate):
    # ⚠️ NÃO TEM PROTEÇÃO DE IDEMPOTÊNCIA EXPLÍCITA
    pagamento = await self.pagamento_repo.create(dados)
    cielo_response = await self.cielo_api.criar_pagamento_cartao(...)
```

**Frontend** (`page.js`):
```javascript
const handlePagamento = async () => {
    setPagamentoLoading(true)  // ✅ Bloqueia
}
```

| Aspecto | Backend | Frontend | Resultado |
|---------|---------|----------|-----------|
| **Idempotência nativa** | ❌ Não | N/A | ❌ RISCO ALTO |
| **Bloqueia duplo clique** | N/A | ✅ setPagamentoLoading | ✅ OK |
| **Risco real** | Pagamento duplicado na Cielo | N/A | ❌ CRÍTICO |

### 🚨 RISCO DE PAGAMENTO DUPLICADO

Se usuário clicar duas vezes rapidamente (antes do loading bloquear), ou se houver timeout e retry, pode gerar **cobranças duplicadas** no cartão.

**Solução recomendada**:
```python
# Backend
@router.post("")
async def criar_pagamento(
    pagamento: PagamentoCreate,
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    if idempotency_key:
        cached = await check_idempotency(idempotency_key)
        if cached:
            return cached
```

```javascript
// Frontend
const handlePagamento = async () => {
    const idempotencyKey = crypto.randomUUID()
    const res = await api.post('/pagamentos', payload, {
        headers: { 'X-Idempotency-Key': idempotencyKey }
    })
}
```

---

### 3.2 Quadro Resumo Idempotência

| Operação | Backend Idempotente | Frontend Protege | Risco Real |
|----------|---------------------|------------------|------------|
| **Criar Reserva** | ✅ Com header | ⚠️ Não envia header | BAIXO |
| **Check-in** | ⚠️ Parcial (valida status) | ✅ Loading | BAIXO |
| **Check-out** | ✅ Total | ✅ Loading | NENHUM |
| **Pagamento** | ❌ Não | ✅ Loading | **ALTO** |
| **Cancelar** | ⚠️ Parcial | ✅ Loading | BAIXO |

---

## 4️⃣ AUTORIDADE DO BACKEND

### 4.1 Princípio: Backend é a Única Fonte da Verdade

**Violações encontradas**:

#### VIOLAÇÃO 1: Frontend Decide Check-in

```javascript
// page.js:1305-1310 - FRONTEND DECIDE SEM CONSULTAR BACKEND
disabled={
    checkinLoadingId === reserva.id || 
    reserva.status === 'HOSPEDADO' || 
    reserva.status === 'CHECKED_OUT' ||
    reserva.status === 'CANCELADO'
}
// ❌ Não verifica pagamento
// ❌ Não verifica quarto
// ❌ Não verifica data
```

**Correto seria**:
```javascript
// Opção 1: Chamar endpoint de validação
const { pode_checkin, motivo } = await api.get(`/reservas/${id}/pode-checkin`)

// Opção 2: Backend retorna ações disponíveis junto com reserva
const reserva = await api.get(`/reservas/${id}`)
// reserva.acoes_disponiveis = { checkin: true, checkout: false, ... }
```

---

#### VIOLAÇÃO 2: Frontend Assume Fluxo Feliz no Pagamento

```javascript
// page.js - handlePagamento
const res = await api.post('/pagamentos', payload)
if (res.data) {
    toast.success('Pagamento processado!')
    // ❌ Não verifica se reserva foi CONFIRMADA
    // ❌ Não verifica se voucher foi gerado
}
```

**Correto seria**:
```javascript
const res = await api.post('/pagamentos', payload)
if (res.data.success && res.data.status === 'APROVADO') {
    // Buscar reserva atualizada para confirmar
    const reservaAtualizada = await api.get(`/reservas/${reservaId}`)
    if (reservaAtualizada.status === 'CONFIRMADA') {
        toast.success('Pagamento aprovado! Reserva confirmada.')
    }
}
```

---

#### VIOLAÇÃO 3: Estado Local vs Estado do Servidor

```javascript
// Frontend mantém estado local que pode ficar desatualizado
const [reservas, setReservas] = useState([])

// Após ação, atualiza todo o estado
await loadReservas()  // ✅ Correto - busca do servidor

// MAS: Entre ações, estado pode estar desatualizado
// Se outro usuário cancelou a reserva, frontend não sabe
```

---

### 4.2 Onde Backend Está Permissivo Demais

#### PERMISSIVIDADE 1: Check-in Aceita PENDENTE

```python
# reserva_repo.py:187-188
if reserva.status not in ("PENDENTE", "CONFIRMADA"):
    raise ValueError("...")
# ⚠️ ACEITA PENDENTE - deveria aceitar só CONFIRMADA
```

**vs Validator**:
```python
# validators.py:101
if reserva.status != "CONFIRMADA":
    raise HTTPException(400, "Check-in só pode ser feito em reservas confirmadas")
# ✅ Mais correto
```

**Problema**: Há inconsistência entre `reserva_repo` e `validators`. O validator é mais restritivo, mas não é usado no fluxo de check-in.

---

#### PERMISSIVIDADE 2: Cancelar Reserva HOSPEDADO

```python
# reserva_repo.py:315-316
if reserva.status not in ("PENDENTE", "CONFIRMADA", "HOSPEDADO"):
    raise ValueError("...")
# ⚠️ Permite cancelar hóspede que está NO HOTEL
```

**Risco**: Hóspede poderia ser "cancelado" enquanto está no quarto.

---

### 4.3 Quadro de Autoridade

| Decisão | Quem Decide Atualmente | Quem Deveria Decidir |
|---------|------------------------|----------------------|
| Habilitar check-in | ❌ Frontend (parcial) | Backend |
| Habilitar checkout | ✅ Frontend (correto) | Backend |
| Habilitar cancelar | ⚠️ Frontend (restritivo) | Backend |
| Habilitar pagar | ✅ Frontend (correto) | Backend |
| Validar pagamento | ✅ Backend | Backend |
| Calcular pontos | ✅ Backend | Backend |
| Gerar voucher | ✅ Backend | Backend |

---

## 5️⃣ GAP ANALYSIS: Endpoints Backend vs Frontend

### RESERVAS

| Endpoint | Método | Frontend Usa | UI Existe | Valida Erro | Loading |
|----------|--------|--------------|-----------|-------------|---------|
| `GET /reservas` | Listar | ✅ | ✅ | ✅ | ✅ |
| `POST /reservas` | Criar | ✅ | ✅ | ✅ | ✅ |
| `GET /reservas/{id}` | Obter | ✅ | ✅ | ✅ | ⚠️ |
| `PATCH /reservas/{id}` | Atualizar | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `POST /reservas/{id}/checkin` | Check-in | ✅ | ✅ | ✅ | ✅ |
| `POST /reservas/{id}/checkout` | Checkout | ✅ | ✅ | ✅ | ✅ |
| `PATCH /reservas/{id}/cancelar` | Cancelar | ✅ | ✅ | ✅ | ✅ |
| `POST /reservas/{id}/confirmar` | Confirmar | ❌ | ❌ | N/A | N/A |
| `GET /reservas/export/csv` | Exportar | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `GET /reservas/export/pdf` | Exportar | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `GET /reservas/cliente/{id}` | Por cliente | ❌ | ❌ | N/A | N/A |

**Gaps**:
- ❌ `POST /reservas/{id}/confirmar` - Não existe UI (confirmação é automática pós-pagamento)
- ❌ `GET /reservas/cliente/{id}` - Não existe UI para ver reservas de um cliente

---

### PAGAMENTOS

| Endpoint | Método | Frontend Usa | UI Existe | Valida Erro | Loading |
|----------|--------|--------------|-----------|-------------|---------|
| `GET /pagamentos` | Listar | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `POST /pagamentos` | Criar | ✅ | ✅ | ✅ | ✅ |
| `GET /pagamentos/{id}` | Obter | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `GET /pagamentos/reserva/{id}` | Por reserva | ✅ | ✅ | ✅ | ⚠️ |
| `GET /pagamentos/{id}/status` | Status PIX | ✅ | ✅ | ✅ | ✅ |
| `POST /pagamentos/{id}/confirmar-pix` | Confirmar PIX | ✅ | ✅ | ✅ | ✅ |
| `POST /pagamentos/{id}/cancelar` | Cancelar | ❌ | ❌ | N/A | N/A |
| `POST /pagamentos/webhook/cielo` | Webhook | N/A | N/A | N/A | N/A |

**Gaps**:
- ❌ `POST /pagamentos/{id}/cancelar` - Sem UI para cancelar/estornar pagamento

---

### PONTOS

| Endpoint | Método | Frontend Usa | UI Existe | Valida Erro | Loading |
|----------|--------|--------------|-----------|-------------|---------|
| `GET /pontos/saldo/{id}` | Saldo | ✅ | ✅ | ✅ | ✅ |
| `GET /pontos/historico/{id}` | Histórico | ✅ | ✅ | ✅ | ✅ |
| `POST /pontos/ajustes` | Ajustar | ✅ | ✅ | ✅ | ✅ |
| `POST /pontos/convites` | Gerar convite | ✅ | ✅ | ✅ | ✅ |
| `POST /pontos/convites/{codigo}/uso` | Usar convite | ✅ | ✅ | ✅ | ✅ |
| `GET /pontos/estatisticas` | Estatísticas | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

---

### QUARTOS

| Endpoint | Método | Frontend Usa | UI Existe | Valida Erro | Loading |
|----------|--------|--------------|-----------|-------------|---------|
| `GET /quartos` | Listar | ✅ | ✅ | ✅ | ✅ |
| `POST /quartos` | Criar | ✅ | ✅ | ✅ | ✅ |
| `PUT /quartos/{numero}` | Atualizar | ✅ | ✅ | ✅ | ✅ |
| `DELETE /quartos/{numero}` | Excluir | ✅ | ✅ | ✅ | ✅ |
| `GET /quartos/disponiveis/periodo` | Disponíveis | ✅ | ✅ | ✅ | ✅ |
| `GET /quartos/{numero}/historico` | Histórico | ✅ | ✅ | ✅ | ⚠️ |

---

### ANTIFRAUDE

| Endpoint | Método | Frontend Usa | UI Existe | Valida Erro | Loading |
|----------|--------|--------------|-----------|-------------|---------|
| `GET /antifraude/analisar/cliente/{id}` | Analisar | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `GET /antifraude/estatisticas` | Estatísticas | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `GET /antifraude/transacoes-suspeitas` | Suspeitas | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

**Gaps**:
- ⚠️ Dashboard de antifraude incompleto no frontend

---

### VOUCHERS

| Endpoint | Método | Frontend Usa | UI Existe | Valida Erro | Loading |
|----------|--------|--------------|-----------|-------------|---------|
| `GET /vouchers/reserva/{id}` | Por reserva | ✅ | ✅ | ✅ | ✅ |
| `GET /public/reservas/{codigo}` | Validar público | ✅ | ✅ | ✅ | ✅ |

---

### 5.1 Resumo de Cobertura

```
┌──────────────────────────────────────────────────────┐
│         COBERTURA DE ENDPOINTS                       │
├──────────────────────────────────────────────────────┤
│ Reservas       │ 8/11 endpoints │ 73% cobertura    │
│ Pagamentos     │ 6/8 endpoints  │ 75% cobertura    │
│ Pontos         │ 5/6 endpoints  │ 83% cobertura    │
│ Quartos        │ 6/6 endpoints  │ 100% cobertura   │
│ Antifraude     │ 1/3 endpoints  │ 33% cobertura    │
│ Vouchers       │ 2/2 endpoints  │ 100% cobertura   │
├──────────────────────────────────────────────────────┤
│ TOTAL          │ 28/36 endpoints│ 78% cobertura    │
└──────────────────────────────────────────────────────┘
```

---

## 6️⃣ DIAGNÓSTICO FINAL DE RISCO

### Classificação

# 🟡 OPERACIONAL COM RISCO

### Justificativa Técnica

| Critério | Avaliação | Peso | Score |
|----------|-----------|------|-------|
| **Bug crítico check-in** | ❌ Não funciona corretamente | 30% | 0 |
| **Semântica de estados** | ⚠️ Parcialmente correta | 20% | 10 |
| **Idempotência** | ⚠️ Pagamento não protegido | 20% | 10 |
| **Autoridade backend** | ⚠️ Violada em alguns pontos | 15% | 8 |
| **Cobertura endpoints** | ✅ 78% cobertura | 15% | 12 |

**Score Final**: 40/100 = **OPERACIONAL COM RISCO**

---

### Riscos Reais em Produção

| Risco | Probabilidade | Impacto | Severidade |
|-------|---------------|---------|------------|
| **Check-in desabilitado para reserva paga** | ALTA | ALTO | 🔴 CRÍTICO |
| **Pagamento duplicado** | MÉDIA | ALTO | 🔴 CRÍTICO |
| **Check-in em reserva PENDENTE** | BAIXA | MÉDIO | 🟡 MODERADO |
| **Não cancelar CONFIRMADA** | BAIXA | BAIXO | 🟢 BAIXO |
| **Estado desatualizado** | MÉDIA | BAIXO | 🟢 BAIXO |

---

## 7️⃣ PLANO DE CORREÇÃO

### P0 - CRÍTICO (Bloqueia operação)

#### P0-001: Corrigir Lógica Check-in Frontend
**Esforço**: 4h | **Impacto**: CRÍTICO

**Arquivo**: `frontend/app/(dashboard)/reservas/page.js:1305-1310`

**Código atual**:
```javascript
disabled={
    checkinLoadingId === reserva.id || 
    reserva.status === 'HOSPEDADO' || 
    reserva.status === 'CHECKED_OUT' ||
    reserva.status === 'CANCELADO'
}
```

**Código corrigido**:
```javascript
// Função auxiliar para validar check-in
const podeRealizarCheckin = (reserva) => {
    // Estados que bloqueiam
    if (['HOSPEDADO', 'CHECKED_OUT', 'CANCELADO', 'PENDENTE'].includes(reserva.status)) {
        return false;
    }
    
    // Só CONFIRMADA com pagamento aprovado
    if (reserva.status !== 'CONFIRMADA') {
        return false;
    }
    
    // Verificar pagamento aprovado
    const temPagamentoAprovado = reserva.pagamentos?.some(
        p => ['APROVADO', 'PAGO', 'CONFIRMADO', 'CAPTURED', 'AUTHORIZED'].includes(p.status)
    );
    
    return temPagamentoAprovado;
};

// No botão
disabled={
    checkinLoadingId === reserva.id || 
    !podeRealizarCheckin(reserva)
}
```

---

#### P0-002: Backend Incluir Pagamentos na Listagem
**Esforço**: 2h | **Impacto**: CRÍTICO

**Arquivo**: `backend/app/repositories/reserva_repo.py`

**Adicionar include**:
```python
async def list_all(self, ...):
    registros = await self.db.reserva.find_many(
        where=where_conditions,
        include={
            "pagamentos": True  # ← ADICIONAR
        },
        ...
    )
```

**Serializer**:
```python
def _serialize_reserva(self, reserva) -> Dict[str, Any]:
    return {
        ...,
        "pagamentos": [
            {
                "id": p.id,
                "status": p.status,
                "valor": float(p.valor) if p.valor else 0
            } for p in (reserva.pagamentos or [])
        ]
    }
```

---

#### P0-003: Idempotência em Pagamentos
**Esforço**: 4h | **Impacto**: CRÍTICO

**Backend** (`pagamento_routes.py`):
```python
@router.post("", response_model=PagamentoResponse)
async def criar_pagamento(
    pagamento: PagamentoCreate,
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    ...
):
    # Verificar idempotência
    if idempotency_key:
        cached = await check_idempotency(f"pag:{idempotency_key}")
        if cached:
            return JSONResponse(content=cached["body"], status_code=cached["status_code"])
    
    # Criar pagamento
    resultado = await service.create(pagamento)
    
    # Cachear resultado
    if idempotency_key:
        await store_idempotency_result(f"pag:{idempotency_key}", resultado, status_code=201)
    
    return resultado
```

**Frontend**:
```javascript
const handlePagamento = async () => {
    const idempotencyKey = crypto.randomUUID()
    
    const res = await api.post('/pagamentos', payload, {
        headers: { 'X-Idempotency-Key': idempotencyKey }
    })
}
```

---

### P1 - IMPORTANTE (Corrigir em 1 semana)

#### P1-001: Validação Check-in no Backend
**Esforço**: 2h | **Impacto**: ALTO

**Arquivo**: `backend/app/repositories/reserva_repo.py:181-188`

**Corrigir**:
```python
async def checkin(self, reserva_id: int):
    reserva = await self.db.reserva.find_unique(
        where={"id": reserva_id},
        include={"pagamentos": True}
    )
    
    # VALIDAÇÃO 1: Status deve ser CONFIRMADA
    if reserva.status != "CONFIRMADA":
        raise ValueError(f"Check-in requer status CONFIRMADA. Status atual: {reserva.status}")
    
    # VALIDAÇÃO 2: Deve ter pagamento aprovado
    pagamentos_aprovados = [
        p for p in reserva.pagamentos
        if p.status in ("APROVADO", "PAGO", "CONFIRMADO")
    ]
    
    if not pagamentos_aprovados:
        raise ValueError("Check-in requer pagamento aprovado")
    
    # ... resto do código
```

---

#### P1-002: Corrigir Botão Cancelar para CONFIRMADA
**Esforço**: 1h | **Impacto**: BAIXO

**Arquivo**: `frontend/app/(dashboard)/reservas/page.js:1347`

**Corrigir**:
```javascript
disabled={
    cancelLoadingId === reserva.id || 
    !['PENDENTE', 'CONFIRMADA', 'HOSPEDADO'].includes(reserva.status)
}
```

---

#### P1-003: Endpoint de Ações Disponíveis
**Esforço**: 4h | **Impacto**: MÉDIO

**Novo endpoint** (`reserva_routes.py`):
```python
@router.get("/{reserva_id}/acoes")
async def obter_acoes_disponiveis(reserva_id: int, ...):
    """
    Retorna quais ações estão disponíveis para a reserva.
    Frontend usa isso para habilitar/desabilitar botões.
    """
    reserva = await service.get_by_id(reserva_id)
    
    from app.core.state_validators import get_acoes_disponiveis
    
    return get_acoes_disponiveis(
        status_reserva=reserva["status"],
        status_pagamento=...,  # Buscar último pagamento
        status_hospedagem=...  # Buscar hospedagem
    )
```

---

### P2 - DESEJÁVEL (Backlog)

#### P2-001: Adicionar Validação de Saldo na UI de Checkout
**Esforço**: 2h | **Impacto**: BAIXO

Mostrar saldo devedor antes de permitir checkout.

---

#### P2-002: Dashboard Antifraude Completo
**Esforço**: 8h | **Impacto**: BAIXO

Implementar UI para todos os endpoints de antifraude.

---

#### P2-003: Polling/WebSocket para Estado Atualizado
**Esforço**: 8h | **Impacto**: MÉDIO

Manter estado do frontend sincronizado com backend.

---

### 7.1 Resumo do Plano

| ID | Descrição | Prioridade | Esforço | Impacto |
|----|-----------|------------|---------|---------|
| P0-001 | Corrigir lógica check-in frontend | P0 | 4h | CRÍTICO |
| P0-002 | Include pagamentos na listagem | P0 | 2h | CRÍTICO |
| P0-003 | Idempotência em pagamentos | P0 | 4h | CRÍTICO |
| P1-001 | Validação check-in backend | P1 | 2h | ALTO |
| P1-002 | Corrigir botão cancelar | P1 | 1h | BAIXO |
| P1-003 | Endpoint ações disponíveis | P1 | 4h | MÉDIO |
| P2-001 | Validação saldo UI | P2 | 2h | BAIXO |
| P2-002 | Dashboard antifraude | P2 | 8h | BAIXO |
| P2-003 | Polling/WebSocket | P2 | 8h | MÉDIO |

**Total P0**: 10h (1-2 dias)  
**Total P1**: 7h (1 dia)  
**Total P2**: 18h (2-3 dias)

---

## 📊 CONCLUSÃO

### O Que Está Correto

1. ✅ **Estados reconhecidos** - Frontend conhece todos os 5 estados
2. ✅ **Checkout idempotente** - Backend protege contra duplicação
3. ✅ **Crédito de pontos protegido** - Não credita duas vezes
4. ✅ **Botão checkout correto** - Só habilita para HOSPEDADO
5. ✅ **Loading states** - Frontend bloqueia durante requests
6. ✅ **Cobertura de endpoints** - 78% dos endpoints têm UI

### O Que Está Incorreto

1. ❌ **Check-in não valida pagamento** - BUG CRÍTICO
2. ❌ **Pagamento não é idempotente** - RISCO DE COBRANÇA DUPLICADA
3. ❌ **Frontend decide check-in** - Viola autoridade do backend
4. ❌ **Cancelar CONFIRMADA bloqueado** - Mais restritivo que backend

### O Que Está Perigoso

1. 🔴 **Check-in em PENDENTE** - Backend aceita, deveria rejeitar
2. 🔴 **Pagamento duplicado** - Sem proteção de idempotência
3. 🟡 **Estado local desatualizado** - Pode causar conflitos

### Recomendação Final

**Antes de produção**:
1. Implementar P0-001, P0-002, P0-003 (10h)
2. Testar fluxo completo: criar → pagar → check-in → check-out
3. Validar que pagamento duplicado não é possível

**Score de prontidão para produção**: **40%** (requer correções críticas)

---

**FIM DA AUDITORIA**
