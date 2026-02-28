# Fluxo Correto: Reserva + Pagamento + Comprovante + Aprovação

## 🎯 Modelo Mental Correto

Você não tem só uma reserva. Você tem:

1. **Reserva** (intenção comercial)
2. **Tentativa de Pagamento** (transação financeira)
3. **Comprovante** (prova documental)
4. **Aprovação** (validação humana)

São **quatro entidades lógicas diferentes**, mesmo que implementadas em 2-3 tabelas.

---

## 📊 Estados Oficiais da Reserva

```python
# app/schemas/status_enums.py

PENDENTE_PAGAMENTO       # Reserva criada, aguardando escolha de pagamento
AGUARDANDO_COMPROVANTE   # Escolheu "balcão", aguardando upload
EM_ANALISE               # Comprovante enviado, aguardando validação admin
PAGA_APROVADA            # Comprovante aprovado, pagamento confirmado
PAGA_REJEITADA           # Comprovante rejeitado
CHECKIN_LIBERADO         # ✅ Pagamento OK, pode fazer check-in
CHECKIN_REALIZADO        # Check-in feito, hóspede no hotel
CHECKOUT_REALIZADO       # Check-out realizado
CANCELADA                # Reserva cancelada
NO_SHOW                  # Cliente não compareceu
```

---

## 🔄 Fluxo End-to-End

### 1. Criação da Reserva

```http
POST /api/v1/reservas
```

**Status inicial**: `PENDENTE_PAGAMENTO`

### 2. Modal de Pagamento (Frontend)

Opções:
- ☑️ PIX
- ☑️ Cartão Online
- ☑️ **Pagamento no balcão (maquininha)**

### 3. Se escolher "Pagamento no balcão"

**Sistema muda para**: `AGUARDANDO_COMPROVANTE`

**Frontend abre**: Modal de upload de comprovante (obrigatório)

### 4. Upload do Comprovante

```http
POST /api/v1/reservas/{id}/comprovante
Content-Type: application/json

{
  "arquivo_base64": "base64_string",
  "nome_arquivo": "comprovante.jpg",
  "metodo_pagamento": "PIX|DINHEIRO|DEBITO|CREDITO",
  "observacao": "Pago no débito"
}
```

**Backend faz**:
1. Salva arquivo em `uploads/comprovantes/{cliente_id}_{nome}/{ano}/{mes}/`
2. Cria registro em `comprovantes_pagamento`
3. Atualiza reserva: `status = EM_ANALISE`

### 5. Página /comprovantes (Admin)

**Endpoint**: `GET /api/v1/comprovantes/pendentes`

Lista:
```
Reserva | Cliente      | Método | Preview | Status    | Ação
#123    | João Silva   | Balcão | Ver     | PENDENTE  | [Aprovar] [Rejeitar]
```

**Visualização do comprovante**:
- Zoom
- Fullscreen
- Download

### 6. Aprovação

```http
POST /api/v1/comprovantes/validar

{
  "pagamento_id": 123,
  "status": "APROVADO",
  "usuario_validador_id": 1,
  "motivo": "Comprovante válido"
}
```

**Backend faz**:
1. `comprovante.status = APROVADO`
2. `pagamento.status = APROVADO`
3. **`reserva.status = CHECKIN_LIBERADO`** ✅
4. `reserva.status_financeiro = PAGO_TOTAL`

### 7. Rejeição

```http
POST /api/v1/comprovantes/validar

{
  "pagamento_id": 123,
  "status": "RECUSADO",
  "usuario_validador_id": 1,
  "motivo": "Comprovante ilegível"
}
```

**Backend faz**:
1. `comprovante.status = RECUSADO`
2. `pagamento.status = RECUSADO`
3. **`reserva.status = PAGA_REJEITADA`** ❌

---

## 🔒 Regra de Ouro do Sistema

### Check-in só pode acontecer se:

```python
if reserva.status != "CHECKIN_LIBERADO":
    raise HTTPException(403, "Pagamento não aprovado")
```

**Qualquer outra coisa**: `403 Forbidden - "Pagamento não aprovado"`

---

## 🛡️ Proteção Real (Antifraude Básica)

### No endpoint de check-in:

```python
# app/services/checkin_service.py

def validar_pre_checkin(self, reserva_id: int):
    reserva = self.db.query(Reserva).filter(Reserva.id == reserva_id).first()
    
    # VALIDAÇÃO CRÍTICA
    if reserva.status_reserva != "CHECKIN_LIBERADO":
        if reserva.status_reserva == "PENDENTE_PAGAMENTO":
            raise CheckinValidationError("Reserva aguardando pagamento")
        elif reserva.status_reserva == "AGUARDANDO_COMPROVANTE":
            raise CheckinValidationError("Aguardando upload do comprovante")
        elif reserva.status_reserva == "EM_ANALISE":
            raise CheckinValidationError("Comprovante em análise pelo administrador")
        elif reserva.status_reserva == "PAGA_REJEITADA":
            raise CheckinValidationError("Comprovante de pagamento foi rejeitado")
        else:
            raise CheckinValidationError(f"Status não permite check-in: {reserva.status_reserva}")
```

---

## 🎨 UX Correta (Frontend)

### Na página /reservas

**Badge clara**:
- 🟡 Aguardando comprovante
- 🔵 Em análise
- 🔴 Rejeitado
- 🟢 Pago aprovado
- 🟣 Check-in liberado

**Botão de check-in**:

Só aparece se:
```typescript
if (reserva.status === "CHECKIN_LIBERADO") {
  return <Button>Fazer Check-in</Button>
}
```

---

## ❌ Erro Comum (Que Você Estava Cometendo)

### Antes:
```python
# Reserva tinha apenas:
pago: boolean  # ❌ Não funciona em mundo real
```

**Problemas**:
- ❌ Não existe auditoria
- ❌ Não existe aprovação
- ❌ Não existe histórico
- ❌ Qualquer upload libera tudo

### Agora:
```python
# Reserva tem:
status_reserva: StatusReserva  # ✅ Estado completo
status_financeiro: StatusFinanceiro  # ✅ Estado financeiro separado

# Comprovante tem:
status_validacao: StatusValidacao  # ✅ Estado de aprovação
validador_id: int  # ✅ Quem aprovou
data_validacao: datetime  # ✅ Quando aprovou
motivo_recusa: str  # ✅ Por que rejeitou
```

---

## 📁 Estrutura de Arquivos

```
uploads/comprovantes/
  ├── 123_joao_silva/
  │   ├── 2026/
  │   │   ├── 01/
  │   │   │   ├── comprovante_pag456_20260126_143022_a1b2c3d4.jpg
  │   │   │   └── comprovante_pag789_20260126_150033_e5f6g7h8.pdf
```

**Organização**:
- Por cliente (ID + nome sanitizado)
- Por ano/mês
- Nome único com timestamp + UUID

---

## 🔍 Tabela de Comprovantes (Mínimo Profissional)

```sql
CREATE TABLE comprovantes_pagamento (
  id SERIAL PRIMARY KEY,
  pagamento_id INT NOT NULL,
  tipo_comprovante VARCHAR(50),  -- PIX, TRANSFERENCIA, DINHEIRO, etc
  nome_arquivo VARCHAR(255),
  caminho_arquivo TEXT,
  status_validacao VARCHAR(50),  -- AGUARDANDO, EM_ANALISE, APROVADO, RECUSADO
  valor_confirmado DECIMAL(10,2),
  observacoes TEXT,
  observacoes_internas TEXT,
  
  -- Auditoria
  data_upload TIMESTAMP,
  data_validacao TIMESTAMP,
  validador_id INT,
  motivo_recusa TEXT,
  
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🎯 O Que Isso Te Dá (Nível SaaS Real)

Com essa implementação você ganha:

✅ **Compliance** - Rastreabilidade completa  
✅ **Antifraude** - Validação humana obrigatória  
✅ **Auditoria** - Histórico de todas as decisões  
✅ **Prova Legal** - Comprovante arquivado com metadados  
✅ **Zero Check-in Indevido** - Bloqueio automático  
✅ **Transparência** - Cliente vê status em tempo real  

---

## 💡 Frase que Define a Lógica Certa

> **"Comprovante não é mídia. Comprovante é evento financeiro que altera estado de negócio."**

Se não modelar assim, o sistema sempre vai ser frágil.

---

## 🚀 Endpoints Implementados

### Reservas
- `POST /api/v1/reservas` - Criar reserva (status: PENDENTE_PAGAMENTO)
- `POST /api/v1/reservas/{id}/comprovante` - Upload de comprovante
- `GET /api/v1/reservas/{id}` - Consultar reserva

### Comprovantes
- `GET /api/v1/comprovantes/pendentes` - Listar pendentes de validação
- `GET /api/v1/comprovantes/em-analise` - Listar em análise
- `POST /api/v1/comprovantes/validar` - Aprovar/Rejeitar
- `GET /api/v1/comprovantes/dashboard` - Dashboard de validação
- `GET /api/v1/comprovantes/arquivo/{nome}` - Download do arquivo

### Check-in
- `POST /api/v1/checkin/{id}/realizar` - Realizar check-in (BLOQUEADO se status != CHECKIN_LIBERADO)

---

## 📝 Próximos Passos (Frontend)

1. **Modal de Pagamento** - Adicionar opção "Pagamento no balcão"
2. **Upload de Comprovante** - Modal com preview e validação
3. **Página /comprovantes** - Dashboard de aprovação para admins
4. **Badge de Status** - Indicadores visuais claros
5. **Botão de Check-in** - Condicional baseado em status

---

## 🔧 Arquivos Modificados

- `backend/app/schemas/status_enums.py` - Enum expandido
- `backend/app/api/v1/reserva_routes.py` - Endpoint de upload
- `backend/app/repositories/comprovante_repo.py` - Lógica de aprovação
- `backend/app/services/checkin_service.py` - Validação crítica

---

## ✅ Status da Implementação

- [x] Enum de status expandido
- [x] Endpoint de upload de comprovante
- [x] Lógica de aprovação/rejeição
- [x] Validação de check-in
- [x] Auditoria completa
- [x] Notificações para admins
- [ ] Frontend: Modal de pagamento
- [ ] Frontend: Upload de comprovante
- [ ] Frontend: Página /comprovantes
- [ ] Frontend: Badges de status

---

**Data de Implementação**: 26/01/2026  
**Versão**: 1.0  
**Status**: Backend Completo ✅
