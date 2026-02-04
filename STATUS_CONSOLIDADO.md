# STATUS CONSOLIDADO - SISTEMA HOTEL

## DECISÃO FINAL (única fonte da verdade)

### 1. StatusReserva (Comercial)
```
PENDENTE_PAGAMENTO    → Reserva criada, aguardando pagamento
AGUARDANDO_COMPROVANTE → Escolheu "balcão", aguardando upload
EM_ANALISE            → Comprovante enviado, aguardando validação
CONFIRMADA            → ✅ PAGAMENTO APROVADO - PODE FAZER CHECK-IN
CHECKIN_REALIZADO     → Check-in feito, hóspede no hotel
CHECKOUT_REALIZADO    → Check-out realizado
PAGA_REJEITADA        → Comprovante rejeitado
CANCELADA             → Reserva cancelada
NO_SHOW               → Cliente não compareceu
```

**IMPORTANTE**: 
- Ao aprovar comprovante: `statusReserva = "CONFIRMADA"`
- Não usar mais `CHECKIN_LIBERADO` nem `PAGA_APROVADA`
- `CONFIRMADA` é o estado que permite check-in

### 2. StatusPagamento (Financeiro)
```
PENDENTE     → Aguardando processamento
PROCESSANDO  → Em processamento
CONFIRMADO   → ✅ PAGAMENTO CONFIRMADO/APROVADO
NEGADO       → Pagamento recusado
ESTORNADO    → Pagamento estornado
CANCELADO    → Pagamento cancelado
```

**IMPORTANTE**:
- Ao aprovar comprovante: `statusPagamento = "CONFIRMADO"`
- Não usar mais `APROVADO` (é alias de `CONFIRMADO`)
- Validadores exigem `CONFIRMADO`

### 3. StatusHospedagem (Operacional)
```
NAO_INICIADA      → Aguardando check-in
CHECKIN_REALIZADO → Hóspede no hotel
CHECKOUT_REALIZADO → Hóspede saiu
ENCERRADA         → Hospedagem finalizada
```

**IMPORTANTE**:
- Criar `Hospedagem` com `statusHospedagem = "NAO_INICIADA"` quando reserva for confirmada
- Validadores exigem `NAO_INICIADA` para permitir check-in

---

## FLUXO OFICIAL: Upload → Aprovação → Check-in

### 1. Cliente faz upload de comprovante
```python
# reserva_routes.py: upload_comprovante_reserva
Reserva.statusReserva = "EM_ANALISE"
Pagamento.statusPagamento = "PENDENTE"
ComprovantePagamento.statusValidacao = "AGUARDANDO_COMPROVANTE"
```

### 2. Admin aprova comprovante
```python
# comprovante_repo.py: validar_comprovante (APROVADO)
Pagamento.statusPagamento = "CONFIRMADO"
Reserva.statusReserva = "CONFIRMADA"
ComprovantePagamento.statusValidacao = "APROVADO"

# Criar Hospedagem se não existir
if not hospedagem:
    Hospedagem.create(statusHospedagem="NAO_INICIADA")
```

### 3. Admin recusa comprovante
```python
# comprovante_repo.py: validar_comprovante (RECUSADO)
Pagamento.statusPagamento = "RECUSADO"
Reserva.statusReserva = "PAGA_REJEITADA"
ComprovantePagamento.statusValidacao = "RECUSADO"
```

### 4. Check-in (validação)
```python
# state_validators.py: pode_fazer_checkin
REQUER:
  - statusReserva == "CONFIRMADA"
  - statusPagamento == "CONFIRMADO"
  - statusHospedagem == "NAO_INICIADA"
```

---

## ARQUIVOS QUE PRECISAM ESTAR ALINHADOS

### ✅ Já corrigidos
- `backend/app/repositories/comprovante_repo.py` (linha 189: CONFIRMADA, linha 174: CONFIRMADO)

### ⚠️ Precisam revisão
- `backend/app/core/state_validators.py` (linha 161-166: valida CONFIRMADA + CONFIRMADO)
- `backend/app/schemas/status_enums.py` (linha 167-171: pode_fazer_checkin)
- `backend/app/services/checkin_service.py` (linha 44: valida CHECKIN_LIBERADO - ERRADO!)

---

## MIGRATION NECESSÁRIA

```python
# Corrigir registros antigos no banco:
1. CHECKIN_LIBERADO → CONFIRMADA (reservas)
2. APROVADO → CONFIRMADO (pagamentos)
3. Criar Hospedagem (NAO_INICIADA) para reservas CONFIRMADA sem hospedagem
```

---

## FRONTEND

### StatusBadge.js
Já mapeado:
- CONFIRMADA → "Confirmada" (verde)
- CHECKIN_LIBERADO → "Check-in Liberado" (roxo) - REMOVER
- PAGA_APROVADA → "Pago Aprovado" (verde) - REMOVER

**Ação**: Remover badges obsoletos, manter apenas CONFIRMADA
