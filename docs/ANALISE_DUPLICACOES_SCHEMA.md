# ANÁLISE DE DUPLICAÇÕES NO SCHEMA PRISMA

**Data:** 07/01/2026  
**Arquivo:** `backend/prisma/schema.prisma`

---

## 🔴 DUPLICAÇÕES CRÍTICAS ENCONTRADAS

### 1. Tabela `Reserva` - Campos de Status Duplicados

**Linhas 66 e 76:**

```prisma
model Reserva {
  id               Int      @id @default(autoincrement())
  codigoReserva    String   @unique @map("codigo_reserva")
  clienteId        Int      @map("cliente_id")
  status_reserva   String   @default("PENDENTE")  // ❌ CAMPO 1
  checkinPrevisto  DateTime @map("checkin_previsto")
  checkoutPrevisto DateTime @map("checkout_previsto")
  checkinReal      DateTime? @map("checkin_real")
  checkoutReal     DateTime? @map("checkout_real")
  valorDiaria      Decimal   @map("valor_diaria") @db.Decimal(10, 2)
  quartoNumero     String    @map("quarto_numero")
  numDiarias       Int       @map("num_diarias")
  clienteNome      String    @map("cliente_nome")
  tipoSuite        String    @map("tipo_suite")
  status           String    @default("PENDENTE")  // ❌ CAMPO 2 (DUPLICADO!)
  origem           String    @default("PARTICULAR")
  // ...
}
```

**Problema:**
- Dois campos de status: `status_reserva` e `status`
- Ambos com mesmo valor default: "PENDENTE"
- Causa inconsistências quando apenas um é atualizado
- **Bug corrigido:** Check-in atualizava apenas `status`, mas frontend lia `status_reserva`

**Impacto:**
- ⚠️ ALTO - Status inconsistente entre campos
- ⚠️ Check-in não refletia no frontend
- ⚠️ Confusão em validações e queries

**Solução Temporária Implementada:**
Arquivo: `backend/app/repositories/reserva_repo.py`

```python
# Atualiza AMBOS os campos até migração
await self.db.reserva.update(
    where={"id": reserva_id},
    data={
        "status": "HOSPEDADO",
        "status_reserva": "HOSPEDADO",  # ← WORKAROUND
        "checkinReal": now_utc()
    }
)
```

**Solução Definitiva Recomendada:**

```sql
-- Migração para remover duplicação

-- 1. Sincronizar ambos os campos
UPDATE reservas 
SET status = status_reserva 
WHERE status != status_reserva;

-- 2. Remover coluna duplicada
ALTER TABLE reservas DROP COLUMN status_reserva;

-- 3. Atualizar schema.prisma
-- Remover linha: status_reserva String @default("PENDENTE")
-- Manter apenas: status String @default("PENDENTE")
```

---

### 2. Tabela `Pagamento` - Campos de Status Duplicados

**Linhas 124 e 125:**

```prisma
model Pagamento {
  id                  Int      @id @default(autoincrement())
  reservaId           Int      @map("reserva_id")
  clienteId           Int      @map("cliente_id")
  valor               Decimal  @db.Decimal(10, 2)
  metodo              String
  parcelas            Int?
  status              String   @default("PENDENTE")        // ❌ CAMPO 1
  statusPagamento     String?  @map("status_pagamento")   // ❌ CAMPO 2 (DUPLICADO!)
  cieloPaymentId      String?  @map("cielo_payment_id")
  // ...
}
```

**Problema:**
- Dois campos de status: `status` e `statusPagamento`
- `status` é obrigatório (String)
- `statusPagamento` é opcional (String?)
- Não há sincronização automática entre eles

**Impacto:**
- ⚠️ MÉDIO - Pode causar inconsistência em relatórios
- ⚠️ Queries precisam verificar ambos os campos
- ⚠️ Integração com Cielo pode usar campo diferente

**Uso Atual:**
```python
# pagamento_repo.py usa mapeamento
status_map = {
    "APROVADO": "PAGO",
    "CONFIRMADO": "PAGO",
    "APPROVED": "PAGO",
    # ...
}

update_data = {
    "status": status,
    "statusPagamento": status_map.get(status, "PENDENTE")
}
```

**Solução Definitiva Recomendada:**

```sql
-- Migração para remover duplicação

-- 1. Copiar valores de status para statusPagamento se estiver NULL
UPDATE pagamentos 
SET status_pagamento = status 
WHERE status_pagamento IS NULL;

-- 2. Decidir qual campo manter (recomendado: status)
-- Se manter 'status':
ALTER TABLE pagamentos DROP COLUMN status_pagamento;

-- Se manter 'statusPagamento':
ALTER TABLE pagamentos DROP COLUMN status;
ALTER TABLE pagamentos RENAME COLUMN status_pagamento TO status;

-- 3. Atualizar schema.prisma
-- Manter apenas UM campo de status
```

---

## ⚠️ OUTROS PROBLEMAS RELACIONADOS

### 3. Inconsistência de Nomenclatura

**snake_case vs camelCase:**

```prisma
model Reserva {
  status_reserva   String   // snake_case (Python style)
  checkinPrevisto  DateTime // camelCase (JS style)
  clienteId        Int      // camelCase
  codigoReserva    String   // camelCase
}
```

**Recomendação:**
- Padronizar TUDO para snake_case (padrão Python/PostgreSQL)
- Usar `@map()` para manter compatibilidade com banco existente

---

## 📊 RESUMO DAS DUPLICAÇÕES

| Tabela | Campo 1 | Campo 2 | Severidade | Status |
|--------|---------|---------|------------|--------|
| Reserva | `status` | `status_reserva` | 🔴 ALTA | Workaround aplicado |
| Pagamento | `status` | `statusPagamento` | 🟡 MÉDIA | Mapeamento aplicado |

---

## 🛠️ PLANO DE AÇÃO

### Curto Prazo (IMPLEMENTADO ✅)
1. ✅ Atualizar AMBOS os campos em todas as operações
2. ✅ Adicionar comentários no código alertando sobre duplicação
3. ✅ Documentar problema neste arquivo

### Médio Prazo (RECOMENDADO)
1. ⏳ Criar migração SQL para sincronizar campos
2. ⏳ Remover campos duplicados do schema
3. ⏳ Atualizar código para usar apenas campo único
4. ⏳ Testar extensivamente após migração

### Longo Prazo (MELHORIA)
1. ⏳ Padronizar nomenclatura (tudo snake_case)
2. ⏳ Revisar schema completo para outras duplicações
3. ⏳ Implementar validações em nível de banco (constraints)

---

## ⚠️ ATENÇÃO DESENVOLVEDORES

**Ao trabalhar com Reservas:**
```python
# ❌ ERRADO - Atualizar apenas um campo
data={"status": "HOSPEDADO"}

# ✅ CORRETO - Atualizar ambos até migração
data={
    "status": "HOSPEDADO",
    "status_reserva": "HOSPEDADO"
}
```

**Ao consultar status:**
```python
# ✅ Usar fallback para compatibilidade
status_atual = reserva.status or reserva.status_reserva
```

---

## 📝 NOTAS TÉCNICAS

**Por que duplicações são ruins:**
1. **Inconsistência de Dados** - Campos podem ficar dessincronizados
2. **Bugs Silenciosos** - Código pode usar campo errado sem erro
3. **Manutenção Difícil** - Alterações precisam tocar múltiplos campos
4. **Performance** - Índices e queries duplicados
5. **Confusão** - Desenvolvedores não sabem qual campo usar

**Referências:**
- Issue corrigida: Check-in não atualizava status
- Arquivo: `BUGFIX_CHECKIN_STATUS.md`
- Data da correção: 07/01/2026

---

**FIM DA ANÁLISE**
