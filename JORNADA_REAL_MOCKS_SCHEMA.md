# Jornada Real: Mocks, Schema Backend & Integração Frontend

**Status**: Mapeamento de dados mockados vs. schema esperado do backend.

---

## 1. Entidades Principais do Backend

### Schema Prisma — Tabelas Críticas

#### 1.1 `customers` + `customer_loyalty`
```prisma
model Customer {
  id: String @id @uuid
  name: String
  cpf: String @unique
  email: String? @unique
  phone: String
  status: CustomerStatus (active | inactive | blocked)
  createdAt: DateTime
  
  loyalty: CustomerLoyalty? (1:1)
}

model CustomerLoyalty {
  id: String @id @uuid
  customerId: String @unique @uuid
  currentLevelId: String? @uuid (FK → LoyaltyLevel)
  lifetimePoints: Int @default(0)      // Total histórico
  redeemablePoints: Int @default(0)    // Saldo disponível
  createdAt: DateTime
}
```

**Relação com Frontend:**
- `/consultar` recebe `cpf` como param
- `/consultar-pontos` deve buscar `GET /customers/{cpf}/loyalty` → `lifetimePoints`, `currentLevel`
- **MOCK ATUAL**: pontos hardcoded como `72` constante

---

#### 1.2 `loyalty_levels`
```prisma
model LoyaltyLevel {
  id: String @id @uuid
  name: String @unique          // "Essência", "Experiência", "Real"
  minPoints: Int                // 0, 50, 90
  bonusPercentage: Decimal      // % desconto/bônus
  benefits: Json?               // ["Entrada", "Pontos", "Prêmios"]
  sortOrder: Int @unique        // 1, 2, 3
}
```

**Relação com Frontend:**
- `/nivel_jornada_real` exibe os 3 níveis
- Atualmente hardcoded no page.js como dados estáticos
- Backend define via `GET /loyalty-levels`

---

#### 1.3 `rewards`
```prisma
model Reward {
  id: String @id @uuid
  name: String                  // "Tecnologia Real", "Rituais do Real"
  description: String?
  requiredPoints: Int           // 90, 35, 25
  active: Boolean @default(true)
  stock: Int?                   // null = ilimitado
  imageUrl: String?             // URL da imagem do prêmio
  expiresAt: DateTime?
}
```

**Relação com Frontend:**
- `/consultar-pontos` → `GET /premios` busca lista
- `/resgate_dos_premios` → mostra o catálogo completo
- **MOCK ATUAL**: `prizeDefaults` array com iPhone(90pts), Cafeteira(35pts), Diária(25pts)
- Status como "Disponível: 1 restante" é **hardcoded**, não vem do backend

---

#### 1.4 `reward_redemptions`
```prisma
model RewardRedemption {
  id: String @id @uuid
  customerId: String @uuid
  rewardId: String @uuid
  pointsSpent: Int
  redemptionCode: String @unique   // "REAL-123456" etc
  status: RewardRedemptionStatus   // active | used | expired | cancelled
  usedAt: DateTime?
  expiresAt: DateTime              // 30 dias de validade
}
```

**Relação com Frontend:**
- `/resgate_dos_premios` clica em "Confirmar" → `POST /rewards/redeem`
- **MOCK ATUAL**: `code: REAL -${Date.now().toString().slice(-6)}` gerado localmente
- Não persiste no backend, apenas exibe no modal

---

#### 1.5 `points_transactions` (Ledger)
```prisma
model PointsTransaction {
  id: String @id @uuid
  customerId: String @uuid
  reservationId: String? @uuid
  type: PointTransactionType    // earn_reservation | redeem_reward | manual_adjustment
  points: Int                    // positivo (ganho) ou negativo (gasto)
  description: String
  metadata: Json?
}
```

**Relação com Frontend:**
- Usado internamente pelo backend para auditoria
- Frontend não consulta este modelo diretamente
- Histórico seria via `GET /customers/{id}/points-history`

---

## 2. Endpoints da API vs. Implementação Frontend

### Mapeamento de Requisições

#### 2.1 Consultar Pontos do Cliente
| Endpoint | Método | Parametro | Response | Frontend Atual |
|----------|--------|-----------|----------|----------------|
| `/customers/{cpf}/loyalty` | GET | cpf (path) | `{ lifetimePoints, redeemablePoints, currentLevel }` | ❌ Não usa |
| **Status** | | | | **Usa valores hardcoded: 72 pontos** |

**Mudança necessária:**
```javascript
// ANTES (consultar-pontos/page.js:21)
const currentPoints = 72

// DEPOIS
const { data: loyaltyData } = await api.get(`/customers/${cpf}/loyalty`)
const currentPoints = loyaltyData.redeemablePoints
```

---

#### 2.2 Listar Prêmios Disponíveis
| Endpoint | Método | Response | Frontend Atual |
|----------|--------|----------|----------------|
| `/premios` ou `/rewards` | GET | `{ items: [ { id, name, points, image, stock } ] }` | ✅ Usa corretamente |
| **Status** | | | **Implementado em ambas as páginas** |

**Código atual (funciona):**
```javascript
// consultar-pontos/page.js:108
const response = await api.get('/premios')
const premios = Array.isArray(response.data) ? response.data : []
setApiRewards(premios.map(normalizeReward))
```

---

#### 2.3 Resgatar Prêmio (CRÍTICO)
| Endpoint | Método | Body | Response | Frontend Atual |
|----------|--------|------|----------|----------------|
| `/rewards/redeem` | POST | `{ reward_id, customer_id }` | `{ id, redemption_code, expires_at, status }` | ❌ Não usa |
| **Status** | | | | **Apenas gera código local** |

**Mudança necessária:**
```javascript
// ANTES (resgate_dos_premios/page.js:243)
const handleRedeem = (prize) => {
  setRedeemedPrize({ ...prize, code: `REAL -${Date.now().toString().slice(-6)}` })
}

// DEPOIS
const handleRedeem = async (prize) => {
  const response = await api.post('/rewards/redeem', {
    reward_id: prize.id,
    customer_id: getCurrentCustomerId() // do authContext
  })
  setRedeemedPrize(response.data) // vem com código + expiry do backend
}
```

---

#### 2.4 Validar Código de Resgate (Recepção)
| Endpoint | Método | Body | Response | Frontend |
|----------|--------|------|----------|----------|
| `/rewards/use-code` | POST | `{ code }` | `{ valid, reward_name, customer_name }` | N/A |
| **Status** | | | | Backend apenas (painel recepcionist) |

---

#### 2.5 Consultar Disponibilidade de Quartos
| Endpoint | Método | Query Params | Response | Frontend |
|----------|--------|--------------|----------|----------|
| `/availability` | GET | `?checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&suite_type=REAL` | `{ items: [ { room_id, price, capacity } ] }` | ✅ Implementado |
| **Status** | | | | `/reservar` usa este endpoint |

---

## 3. Tabela de Mocks Identificados

### 🔴 Críticos (Funcionamento quebrado)

| Arquivo | Linha | Mock | Atual | Deveria ser |
|---------|-------|------|-------|------------|
| `consultar-pontos/page.js` | 21 | `currentPoints = 72` | Constante | `GET /customers/{cpf}/loyalty` |
| `consultar-pontos/page.js` | 25 | `rewardProgress = 66` | % fixa | Calcular dos prêmios da API |
| `consultar-pontos/page.js` | 167 | "Hóspede Real" | Nome fixo | Do response `/customers/{cpf}/loyalty` |
| `resgate_dos_premios/page.js` | 246 | `code: REAL -${Date.now()}` | Local | `POST /rewards/redeem` → backend |

### 🟡 Secundários (Funcionam com dados fake)

| Arquivo | Linha | Mock | Comportamento |
|---------|-------|------|---------------|
| `consultar-pontos/page.js` | 264 | "2/3 prêmios" | Contador fixo, deveria somar dos resgates anteriores |
| `resgate_dos_premios/page.js` | 30-31 | "Disponível: 1 restante" | Status do estoque hardcoded |
| `nivel_jornada_real/page.js` | 54-56 | Fallbacks "João"/72 | Aceitável se params vêm da URL anterior |

### 🟢 Baixa Prioridade (Fallbacks aceitáveis)

| Arquivo | Comportamento |
|---------|---------------|
| `prizeDefaults` array | Funciona como fallback se API falhar |
| `levelDefaults` | Exibição ok com dados estáticos |

---

## 4. Fluxos de Dados Esperados

### 4.1 Fluxo Completo: Consultar Pontos
```
1. User entra em "/" (home Jornada Real)
2. Clica "Ver meus pontos" (CTA hero)
3. Navega para "/consultar" (entrada CPF)
4. Digite CPF → POST é feito?
5. Redireciona para "/consultar-pontos?cpf=11144477735"
6. Page carrega:
   - GET /customers/11144477735/loyalty
     ← Backend retorna: { lifetimePoints: 2150, redeemablePoints: 72, currentLevel: { name: "Experiência" } }
   - GET /premios
     ← Backend retorna: [ { id: "abc123", name: "iPhone", requiredPoints: 90, stock: 0 }, ... ]
7. Exibe:
   - "72 pontos atuais" (não 72 hardcoded)
   - Progresso do nível (não 66% fixo)
   - Prêmios com estoque real (não "Disponível: 1")
```

### 4.2 Fluxo Crítico: Resgatar Prêmio
```
1. User em "/consultar-pontos" clica em prêmio
2. Abre card do prêmio com "Resgatar" button
3. Click → POST /rewards/redeem
   Body: { reward_id: "abc123", customer_id: "xyz789" }
   Response: { 
     id: "redemption-123",
     redemptionCode: "REAL-78AB92CD",
     status: "active",
     expiresAt: "2026-07-04"
   }
4. Modal de sucesso exibe:
   - Código gerado pelo backend
   - Data de validade (30 dias)
5. Backend:
   - Decrementa redeemablePoints
   - Registra na tabela reward_redemptions
   - Cria PointsTransaction (tipo: redeem_reward)
```

---

## 5. Campos de Resposta Esperados (Schemas JSON)

### GET /customers/{cpf}/loyalty
```json
{
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_name": "João da Silva",
  "lifetime_points": 2150,
  "redeemable_points": 72,
  "current_level": {
    "id": "level-2",
    "name": "Experiência",
    "min_points": 50,
    "bonus_percentage": 20,
    "benefits": ["Acompanhamento", "Prêmios intermediários"]
  }
}
```

### GET /premios
```json
{
  "data": [
    {
      "id": "reward-001",
      "name": "Tecnologia Real",
      "slug": "tecnologia-real",
      "description": "iPhone 16e",
      "required_points": 90,
      "image_url": "/images/premios/tecnologia-real.png",
      "active": true,
      "stock": null,
      "created_at": "2026-01-15"
    },
    {
      "id": "reward-002",
      "name": "Rituais do Real",
      "slug": "rituais-do-real",
      "description": "Cafeteira Premium",
      "required_points": 35,
      "image_url": "/images/premios/rituais-do-real.png",
      "active": true,
      "stock": 5,
      "created_at": "2026-01-15"
    }
  ]
}
```

### POST /rewards/redeem
```json
// Request
{
  "reward_id": "reward-001",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000"
}

// Response
{
  "id": "redemption-456",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "reward_id": "reward-001",
  "reward_name": "Tecnologia Real",
  "points_spent": 90,
  "redemption_code": "REAL-A7F9B2E1",
  "status": "active",
  "expires_at": "2026-07-04T23:59:59Z",
  "created_at": "2026-06-04T15:22:00Z"
}
```

---

## 6. Checklist de Integração

### Fase 1: Pontos & Níveis (CRÍTICO)
- [ ] `/consultar-pontos` → chamar `GET /customers/{cpf}/loyalty`
- [ ] Remover `const currentPoints = 72`
- [ ] Remover `const rewardProgress = 66`
- [ ] Calcular progresso dinamicamente: `(redeemablePoints / nextLevelPoints) * 100`
- [ ] Exibir nome real do cliente: `loyaltyData.customer_name`
- [ ] Adaptar barra de prêmios (contar resgates prévios)

### Fase 2: Resgate de Prêmios (CRÍTICO)
- [ ] `resgate_dos_premios` → `handleRedeem()` chama `POST /rewards/redeem`
- [ ] Remover geração local de código: `Date.now().slice(-6)`
- [ ] Exibir `redemptionCode` retornado pelo backend
- [ ] Exibir `expiresAt` (validade 30 dias)
- [ ] Tratamento de erro: estoque zerado, saldo insuficiente, prêmio inativo

### Fase 3: Consulta de CPF
- [ ] `/consultar` → validação CPF deve chamar `GET /customers/{cpf}` para confirmar existência?
- [ ] Ou apenas validação de formato + redireciona?

### Fase 4: Testes
- [ ] Teste com CPF válido → pontos carregam
- [ ] Teste com CPF inválido → erro 404
- [ ] Teste resgate com saldo suficiente
- [ ] Teste resgate com saldo insuficiente
- [ ] Teste resgate com estoque zerado

---

## 7. Similaridade Frontend-Backend

### Conformidade com Schema
| Aspecto | Frontend | Backend | Gap |
|---------|----------|---------|-----|
| Estrutura de Pontos | ✅ Usa `lifetimePoints`/`redeemablePoints` conceitual | ✅ Schema Prisma define ambos | Pequeno (não usa lifetime) |
| Níveis | ✅ 3 níveis (Essência, Experiência, Real) | ✅ LoyaltyLevel table com `minPoints`, `benefits` | Pequeno (benefits não exibido) |
| Prêmios | ✅ Busca via API | ✅ GET /premios funciona | Nenhum |
| Resgate | ❌ Local/mock | ✅ POST /rewards/redeem | **CRÍTICO** |
| Validação | ✅ Saldo validado no backend | ✅ Transação com lock | Frontend confia no backend ✅ |
| Auditoria | N/A | ✅ audit_logs table | Ok |

---

## 8. Conclusão

**Readiness Score: 60%**

✅ **Pronto para produção:**
- Listar prêmios (`GET /premios`)
- Estrutura de níveis
- Design UI/UX

❌ **Precisa correção urgente:**
- Pontos hardcoded → deve vir de `GET /customers/{cpf}/loyalty`
- Resgate mockado → deve chamar `POST /rewards/redeem`
- Código gerado localmente → deve vir do backend

**Estimativa de esforço:** 2-3 dias de desenvolvimento (integração + testes).
