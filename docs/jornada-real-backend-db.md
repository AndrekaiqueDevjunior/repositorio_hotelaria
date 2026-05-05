# Jornada Real - Backend e Banco de Dados

Documento de arquitetura e implementacao para o sistema de fidelidade Jornada Real do Hotel Real.

Stack alvo: Node.js + NestJS ou Express, PostgreSQL, Prisma ORM, JWT, fila de notificacoes e integracao WhatsApp desacoplada.

Observacao sobre o repositorio atual: existe um backend FastAPI com modelos como `Cliente`, `Reserva`, `Quarto`, pontos, premios e indicacoes. Este documento define o contrato alvo em Node/Prisma pedido para a Jornada Real. Ele tambem pode ser usado para evoluir o backend atual, preservando os mesmos invariantes transacionais.

## 1. Visao Geral da Arquitetura Backend

Arquitetura recomendada:

- API REST: NestJS preferencialmente, por modularidade, DI, guards JWT, interceptors e validacao com DTOs.
- Banco: PostgreSQL 14+.
- ORM: Prisma.
- Autenticacao: JWT com roles (`admin`, `reception`, `customer`, `system`).
- Tempo real: SSE para alertas operacionais simples ou WebSocket se o painel de reservas ja usa socket.
- Fila: tabela `notifications` + worker em background. Em producao, pode evoluir para BullMQ/Redis mantendo a tabela como ledger.
- WhatsApp: adapter `WhatsAppProvider` com implementacoes para Z-API, Evolution API, Twilio ou WhatsApp Cloud API.
- Auditoria: tabela `audit_logs` para acoes sensiveis.
- Idempotencia: header `Idempotency-Key` nos endpoints criticos e constraints no banco.

Modulos:

- `CustomersModule`: cadastro, CPF unico, perfil e visao de fidelidade.
- `ReservationsModule`: reservas, check-in, check-out, disponibilidade.
- `LoyaltyModule`: niveis, progresso, calculo e ledger de pontos.
- `ReferralsModule`: Convite Real / Cupom Amigo.
- `RewardsModule`: premios, resgates e uso de codigos.
- `NotificationsModule`: mensagens WhatsApp e alertas internos.
- `CheckoutAlertsModule`: alertas do horario de checkout em tempo real.
- `AuthModule`: login, JWT e permissoes.

## 2. Diagrama Textual das Entidades

```text
customers 1---1 customer_loyalty
customers 1---N reservations
customers 1---N points_transactions
customers 1---N referral_codes
customers 1---N reward_redemptions
customers 1---N notifications

suite_types 1---N rooms
rooms 1---N reservations
rooms 1---N checkout_alerts

reservations N---1 customers
reservations N---1 rooms
reservations 1---0..1 points_transactions [earn_reservation]
reservations 1---0..1 referral_uses
reservations 1---N notifications
reservations 1---0..1 checkout_alerts

loyalty_levels 1---N customer_loyalty

referral_codes 1---N referral_uses
referral_uses N---1 referrer customer
referral_uses N---1 referred customer
referral_uses 0..1---1 reservation

rewards 1---N reward_redemptions
reward_redemptions N---1 customers

notifications N---0..1 customers
notifications N---0..1 reservations
audit_logs N---0..1 users/customers/reservations
```

## 3. Prisma Schema Completo

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum CustomerStatus {
  active
  inactive
  blocked
}

enum RoomStatus {
  available
  maintenance
  blocked
  inactive
}

enum ReservationStatus {
  pending_payment
  reserved
  confirmed
  checked_in
  checked_out
  cancelled
  no_show
}

enum PointTransactionType {
  earn_reservation
  earn_referral
  redeem_reward
  manual_adjustment
  expire_points
}

enum ReferralCodeStatus {
  active
  used
  expired
  cancelled
  max_usage_reached
}

enum ReferralUseStatus {
  pending
  reserved
  checked_out
  credited
  invalid
}

enum RewardRedemptionStatus {
  active
  used
  expired
  cancelled
}

enum NotificationType {
  reward_near
  post_checkout_points
  checkout_alert
  referral_invite
}

enum NotificationChannel {
  whatsapp
  system
  email
}

enum NotificationStatus {
  pending
  sent
  failed
  cancelled
}

enum CheckoutAlertStatus {
  pending
  sent
  viewed
  dismissed
}

model Customer {
  id          String         @id @default(uuid()) @db.Uuid
  name        String
  cpf         String         @unique
  email       String?        @unique
  phone       String
  birthDate   DateTime?      @map("birth_date") @db.Date
  status      CustomerStatus @default(active)
  createdAt   DateTime       @default(now()) @map("created_at")
  updatedAt   DateTime       @updatedAt @map("updated_at")

  loyalty             CustomerLoyalty?
  reservations         Reservation[]
  pointsTransactions   PointsTransaction[]
  referralCodes        ReferralCode[]
  referralUsesReceived ReferralUse[]       @relation("ReferredCustomer")
  referralUsesMade     ReferralUse[]       @relation("ReferrerCustomer")
  redemptions          RewardRedemption[]
  notifications        Notification[]

  @@index([phone])
  @@index([status])
  @@map("customers")
}

model SuiteType {
  id          String   @id @default(uuid()) @db.Uuid
  name        String
  description String?
  basePrice   Decimal  @map("base_price") @db.Decimal(10, 2)
  capacity    Int
  active      Boolean  @default(true)
  createdAt   DateTime @default(now()) @map("created_at")
  updatedAt   DateTime @updatedAt @map("updated_at")

  rooms Room[]

  @@index([active])
  @@map("suite_types")
}

model Room {
  id          String     @id @default(uuid()) @db.Uuid
  number      String     @unique
  suiteTypeId String     @map("suite_type_id") @db.Uuid
  status      RoomStatus @default(available)
  createdAt   DateTime   @default(now()) @map("created_at")
  updatedAt   DateTime   @updatedAt @map("updated_at")

  suiteType      SuiteType       @relation(fields: [suiteTypeId], references: [id])
  reservations   Reservation[]
  checkoutAlerts CheckoutAlert[]

  @@index([suiteTypeId])
  @@index([status])
  @@map("rooms")
}

model Reservation {
  id                 String            @id @default(uuid()) @db.Uuid
  customerId         String            @map("customer_id") @db.Uuid
  roomId             String            @map("room_id") @db.Uuid
  checkinAt          DateTime          @map("checkin_at")
  checkoutAt         DateTime          @map("checkout_at")
  actualCheckinAt    DateTime?         @map("actual_checkin_at")
  actualCheckoutAt   DateTime?         @map("actual_checkout_at")
  totalAmount        Decimal           @map("total_amount") @db.Decimal(10, 2)
  paymentMethod      String?           @map("payment_method")
  origin             String            @default("jornada_real")
  status             ReservationStatus @default(pending_payment)
  pointsCredited     Boolean           @default(false) @map("points_credited")
  pointsCreditedAt   DateTime?         @map("points_credited_at")
  pointsTransactionId String?           @unique @map("points_transaction_id") @db.Uuid
  referralCodeUsed   String?           @map("referral_code_used")
  createdAt          DateTime          @default(now()) @map("created_at")
  updatedAt          DateTime          @updatedAt @map("updated_at")

  customer          Customer            @relation(fields: [customerId], references: [id])
  room              Room                @relation(fields: [roomId], references: [id])
  pointsTransaction PointsTransaction?  @relation("ReservationPointsCredit", fields: [pointsTransactionId], references: [id])
  pointsEntries     PointsTransaction[] @relation("ReservationPointEntries")
  referralUse       ReferralUse?
  notifications     Notification[]
  checkoutAlert     CheckoutAlert?

  @@index([customerId])
  @@index([roomId, checkinAt, checkoutAt])
  @@index([status])
  @@index([pointsCredited])
  @@map("reservations")
}

model LoyaltyLevel {
  id              String   @id @default(uuid()) @db.Uuid
  name            String   @unique
  minPoints       Int      @map("min_points")
  bonusPercentage Decimal  @map("bonus_percentage") @db.Decimal(5, 2)
  benefits        Json?
  sortOrder       Int      @map("sort_order")
  active          Boolean  @default(true)
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  customerLoyalties CustomerLoyalty[]

  @@unique([sortOrder])
  @@index([active, minPoints])
  @@map("loyalty_levels")
}

model CustomerLoyalty {
  id               String   @id @default(uuid()) @db.Uuid
  customerId       String   @unique @map("customer_id") @db.Uuid
  currentLevelId   String?  @map("current_level_id") @db.Uuid
  lifetimePoints   Int      @default(0) @map("lifetime_points")
  redeemablePoints Int      @default(0) @map("redeemable_points")
  createdAt        DateTime @default(now()) @map("created_at")
  updatedAt        DateTime @updatedAt @map("updated_at")

  customer     Customer      @relation(fields: [customerId], references: [id])
  currentLevel LoyaltyLevel? @relation(fields: [currentLevelId], references: [id])

  @@index([currentLevelId])
  @@index([lifetimePoints])
  @@map("customer_loyalty")
}

model PointsTransaction {
  id            String               @id @default(uuid()) @db.Uuid
  customerId    String               @map("customer_id") @db.Uuid
  reservationId String?              @map("reservation_id") @db.Uuid
  type          PointTransactionType
  points        Int
  description   String
  metadata      Json?
  createdAt     DateTime             @default(now()) @map("created_at")

  customer              Customer      @relation(fields: [customerId], references: [id])
  reservationEntry      Reservation?  @relation("ReservationPointEntries", fields: [reservationId], references: [id])
  creditedReservation   Reservation?  @relation("ReservationPointsCredit")

  @@index([customerId, createdAt])
  @@index([reservationId])
  @@index([type])
  @@unique([reservationId, type], map: "uq_points_one_reservation_credit")
  @@map("points_transactions")
}

model ReferralCode {
  id          String             @id @default(uuid()) @db.Uuid
  customerId  String             @map("customer_id") @db.Uuid
  code        String             @unique
  maxUses     Int                @default(5) @map("max_uses")
  currentUses Int                @default(0) @map("current_uses")
  status      ReferralCodeStatus @default(active)
  expiresAt   DateTime           @map("expires_at")
  createdAt   DateTime           @default(now()) @map("created_at")
  updatedAt   DateTime           @updatedAt @map("updated_at")

  customer Customer      @relation(fields: [customerId], references: [id])
  uses     ReferralUse[]

  @@index([customerId])
  @@index([status, expiresAt])
  @@map("referral_codes")
}

model ReferralUse {
  id                 String            @id @default(uuid()) @db.Uuid
  referralCodeId     String            @map("referral_code_id") @db.Uuid
  referrerCustomerId String            @map("referrer_customer_id") @db.Uuid
  referredCustomerId String            @map("referred_customer_id") @db.Uuid
  reservationId      String?           @unique @map("reservation_id") @db.Uuid
  status             ReferralUseStatus @default(pending)
  pointsCredited     Boolean           @default(false) @map("points_credited")
  createdAt          DateTime          @default(now()) @map("created_at")
  updatedAt          DateTime          @updatedAt @map("updated_at")

  referralCode ReferralCode @relation(fields: [referralCodeId], references: [id])
  referrer     Customer     @relation("ReferrerCustomer", fields: [referrerCustomerId], references: [id])
  referred     Customer     @relation("ReferredCustomer", fields: [referredCustomerId], references: [id])
  reservation  Reservation? @relation(fields: [reservationId], references: [id])

  @@unique([referralCodeId, referredCustomerId], map: "uq_referral_code_referred_once")
  @@unique([referredCustomerId], map: "uq_referred_customer_global_once")
  @@index([referrerCustomerId])
  @@index([status])
  @@map("referral_uses")
}

model Reward {
  id             String   @id @default(uuid()) @db.Uuid
  name           String
  description    String?
  requiredPoints Int      @map("required_points")
  active         Boolean  @default(true)
  stock          Int?     // null = ilimitado
  createdAt      DateTime @default(now()) @map("created_at")
  updatedAt      DateTime @updatedAt @map("updated_at")

  redemptions RewardRedemption[]

  @@index([active, requiredPoints])
  @@map("rewards")
}

model RewardRedemption {
  id             String                 @id @default(uuid()) @db.Uuid
  customerId     String                 @map("customer_id") @db.Uuid
  rewardId       String                 @map("reward_id") @db.Uuid
  pointsSpent    Int                    @map("points_spent")
  redemptionCode String                 @unique @map("redemption_code")
  status         RewardRedemptionStatus @default(active)
  usedAt         DateTime?              @map("used_at")
  expiresAt      DateTime               @map("expires_at")
  createdAt      DateTime               @default(now()) @map("created_at")
  updatedAt      DateTime               @updatedAt @map("updated_at")

  customer Customer @relation(fields: [customerId], references: [id])
  reward   Reward   @relation(fields: [rewardId], references: [id])

  @@index([customerId])
  @@index([rewardId])
  @@index([status, expiresAt])
  @@map("reward_redemptions")
}

model Notification {
  id               String              @id @default(uuid()) @db.Uuid
  customerId       String?             @map("customer_id") @db.Uuid
  reservationId    String?             @map("reservation_id") @db.Uuid
  type             NotificationType
  channel          NotificationChannel
  message          String
  status           NotificationStatus  @default(pending)
  scheduledAt      DateTime            @default(now()) @map("scheduled_at")
  sentAt           DateTime?           @map("sent_at")
  providerResponse Json?               @map("provider_response")
  retryCount       Int                 @default(0) @map("retry_count")
  dedupeKey        String?             @unique @map("dedupe_key")
  createdAt        DateTime            @default(now()) @map("created_at")
  updatedAt        DateTime            @updatedAt @map("updated_at")

  customer    Customer?    @relation(fields: [customerId], references: [id])
  reservation Reservation? @relation(fields: [reservationId], references: [id])

  @@index([customerId, createdAt])
  @@index([status, scheduledAt])
  @@index([type, channel])
  @@map("notifications")
}

model CheckoutAlert {
  id           String              @id @default(uuid()) @db.Uuid
  reservationId String             @unique @map("reservation_id") @db.Uuid
  roomId       String              @map("room_id") @db.Uuid
  alertTime    DateTime            @map("alert_time")
  status       CheckoutAlertStatus @default(pending)
  soundEnabled Boolean             @default(true) @map("sound_enabled")
  viewedAt     DateTime?           @map("viewed_at")
  createdAt    DateTime            @default(now()) @map("created_at")
  updatedAt    DateTime            @updatedAt @map("updated_at")

  reservation Reservation @relation(fields: [reservationId], references: [id])
  room        Room        @relation(fields: [roomId], references: [id])

  @@index([status, alertTime])
  @@index([roomId])
  @@map("checkout_alerts")
}

model LoyaltyRule {
  id        String   @id @default(uuid()) @db.Uuid
  key       String   @unique
  value     Json
  active    Boolean  @default(true)
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  @@map("loyalty_rules")
}

model IdempotencyKey {
  id          String   @id @default(uuid()) @db.Uuid
  key         String   @unique
  route       String
  requestHash String   @map("request_hash")
  response    Json?
  createdAt   DateTime @default(now()) @map("created_at")
  expiresAt   DateTime @map("expires_at")

  @@index([expiresAt])
  @@map("idempotency_keys")
}

model AuditLog {
  id          String   @id @default(uuid()) @db.Uuid
  actorType   String   @map("actor_type")
  actorId     String?  @map("actor_id")
  entityType  String   @map("entity_type")
  entityId    String?  @map("entity_id")
  action      String
  before      Json?
  after       Json?
  ipAddress   String?  @map("ip_address")
  userAgent   String?  @map("user_agent")
  createdAt   DateTime @default(now()) @map("created_at")

  @@index([entityType, entityId])
  @@index([actorType, actorId])
  @@index([createdAt])
  @@map("audit_logs")
}
```

### SQL Complementar Recomendado

O Prisma nao cria exclusion constraint para intervalo de datas. Use migration SQL manual para impedir conflito real no banco:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE reservations
ADD CONSTRAINT no_room_overlap_active_reservations
EXCLUDE USING gist (
  room_id WITH =,
  tstzrange(checkin_at, checkout_at, '[)') WITH &&
)
WHERE (status IN ('reserved', 'confirmed', 'checked_in', 'pending_payment'));
```

## 4. Relacionamentos

- `Customer` tem um unico `CustomerLoyalty`, que guarda os dois saldos importantes: `lifetime_points` e `redeemable_points`.
- `PointsTransaction` e o ledger. Nenhum saldo deve ser alterado sem transacao correspondente.
- `Reservation.points_transaction_id` aponta para a transacao de credito principal da reserva e impede credito duplicado.
- `ReferralCode` pertence ao cliente indicador. `ReferralUse` liga indicador, indicado e reserva.
- `RewardRedemption` gera um codigo unico por resgate. Codigo usado ou expirado nao pode voltar para `active`.
- `CheckoutAlert` e unico por reserva para impedir alertas duplicados.

## 5. Regras de Negocio Detalhadas

### Pontos

- Regra configuravel: `points_per_currency_unit`, por exemplo `{ "currency": "BRL", "pointsPerUnit": 1 }`.
- `pontos_base = floor(total_amount * pointsPerUnit)`.
- `pontos_bonus = floor(pontos_base * bonusPercentage / 100)`.
- `pontos_total = pontos_base + pontos_bonus`.
- Somente reservas `checked_out` podem creditar pontos.
- `lifetime_points` aumenta com ganhos e ajustes positivos elegiveis.
- `redeemable_points` aumenta com ganhos e diminui com resgates/expiracao.
- Resgate nunca reduz `lifetime_points`.
- Toda alteracao de pontos deve ter registro em `points_transactions`.

### Niveis

- Nivel atual: maior `loyalty_levels.min_points <= customer_loyalty.lifetime_points`, ativo.
- Beneficios ficam em JSON para flexibilidade.
- Niveis iniciais:

```json
[
  {
    "name": "EXPERIENCIA",
    "min_points": 0,
    "bonus_percentage": 20,
    "sort_order": 1,
    "benefits": { "reservation_points_bonus": "20%" }
  },
  {
    "name": "REAL",
    "min_points": 1000,
    "bonus_percentage": 40,
    "sort_order": 2,
    "benefits": { "reservation_points_bonus": "40%" }
  }
]
```

### Convite Real / Cupom Amigo

- Codigo unico, aleatorio e nao sequencial.
- Link exemplo: `https://hotelreal.com/jornada/convite?code=JR-9K4L2Q`.
- Nao permite autoindicacao: `referrer_customer_id != referred_customer_id`.
- O CPF indicado so pode gerar beneficio uma vez globalmente.
- Beneficio fica `pending/reserved` ate check-out.
- Credito de indicacao ocorre apos check-out da reserva do indicado.
- Se `current_uses >= max_uses`, status vira `max_usage_reached`.
- Codigo expirado, cancelado, usado ou limite atingido nao pode ser aplicado.

### Premios

- Cliente so resgata premio ativo e com saldo suficiente.
- Resgate roda em transacao com lock no saldo do cliente.
- Gera `redemption_code` unico.
- `reward_redemptions.status = active` ate uso, expiracao ou cancelamento.
- Uso de codigo altera para `used`, grava `used_at` e impede reutilizacao.

### Notificacoes

- Criar registros em `notifications` com `status=pending`.
- Worker busca pendentes por `scheduled_at <= now()`.
- Mensagens de premio proximo usam `dedupe_key`, por exemplo `reward_near:{customerId}:{rewardId}:{lastPointsTxId}`.
- Reenvio somente apos nova movimentacao de pontos ou apos janela configurada, por exemplo 7 dias.

### Disponibilidade

- Intervalo usa regra `[checkin, checkout)`: checkout no mesmo instante em que outro checkin comeca nao conflita.
- Status bloqueantes: `reserved`, `checked_in`, `pending_payment`, `confirmed`.
- Status nao bloqueantes: `cancelled`, `no_show`, `checked_out`.
- A API de disponibilidade e apenas informativa; a criacao de reserva revalida dentro de transacao.

## 6. Fluxo de Check-out e Liberacao de Pontos

1. Recepcao chama `PATCH /reservations/:id/checkout`.
2. Backend abre transacao.
3. Busca reserva com lock.
4. Valida status `checked_in` ou `confirmed`.
5. Atualiza `status=checked_out`, `actual_checkout_at=now()`.
6. Chama `creditarPontosCheckout(reservationId)` na mesma transacao ou por job idempotente logo depois.
7. Calcula pontos base, bonus e total.
8. Cria `points_transactions` tipo `earn_reservation`.
9. Atualiza `customer_loyalty.lifetime_points` e `redeemable_points`.
10. Atualiza nivel atual.
11. Marca `reservations.points_credited=true`, `points_credited_at=now()`, `points_transaction_id`.
12. Se reserva tinha convite pendente, credita bonus de indicacao conforme regra.
13. Cria notificacao WhatsApp `post_checkout_points`.
14. Verifica premio proximo e cria notificacao `reward_near` se elegivel.
15. Commit.

## 7. Fluxo Convite Real / Cupom Amigo

### Geracao

1. Cliente autenticado chama `POST /referrals/generate`.
2. Backend verifica cliente ativo.
3. Gera codigo unico.
4. Cria `referral_codes`.
5. Cria `notifications` tipo `referral_invite` ou retorna mensagem pronta para compartilhamento.

Mensagem:

```text
To na Jornada Real do Hotel Real
Se voce reservar por esse link, a gente ganha beneficios
👉 [LINK]
Depois me conta
```

### Validacao

1. Indicado informa codigo/link.
2. Backend valida existencia, status, expiracao e limite.
3. Backend compara CPF do indicado com CPF do indicador.
4. Backend verifica se o indicado ja aparece em `referral_uses`.
5. Retorna se o codigo pode ser usado.

### Aplicacao na reserva

1. Ao criar reserva, o cliente envia `referral_code`.
2. Em transacao, backend cria reserva e `referral_uses` com status `reserved`.
3. Incrementa `current_uses`.
4. Se atingiu `max_uses`, muda status para `max_usage_reached`.
5. Beneficio ainda nao e creditado.

### Confirmacao apos check-out

1. No check-out, busca `referral_uses` da reserva.
2. Se status `reserved` e `points_credited=false`, cria transacoes para indicador e/ou indicado.
3. Atualiza `status=credited`.

## 8. Fluxo de Resgate de Premio

1. Cliente chama `POST /rewards/redeem`.
2. Backend abre transacao.
3. Busca premio ativo.
4. Bloqueia linha `customer_loyalty` do cliente.
5. Valida saldo `redeemable_points >= required_points`.
6. Se premio tem estoque, decrementa estoque com validacao `stock > 0`.
7. Cria `points_transactions` tipo `redeem_reward` com pontos negativos.
8. Atualiza `redeemable_points -= required_points`.
9. Gera `redemption_code`.
10. Cria `reward_redemptions(status=active)`.
11. Commit.

Uso do codigo:

1. Recepcao chama `POST /rewards/use-code`.
2. Transacao busca codigo com lock.
3. Valida `status=active` e `expires_at > now()`.
4. Atualiza `status=used`, `used_at=now()`.
5. Registra auditoria.

## 9. Fluxo de Disponibilidade de Suites

1. Cliente chama `GET /availability?checkin=2026-06-10&checkout=2026-06-12&suite_type=REAL`.
2. Backend valida `checkout > checkin`.
3. Busca quartos ativos/disponiveis.
4. Exclui quartos com reserva bloqueante que sobrepoe o intervalo.
5. Retorna lista com suite, preco, capacidade e caracteristicas.
6. Ao criar reserva, repete a verificacao dentro de transacao.
7. Banco tambem protege com exclusion constraint.

Consulta base:

```sql
SELECT r.*
FROM rooms r
JOIN suite_types st ON st.id = r.suite_type_id
WHERE r.status = 'available'
  AND st.active = true
  AND ($3::uuid IS NULL OR st.id = $3::uuid)
  AND NOT EXISTS (
    SELECT 1
    FROM reservations res
    WHERE res.room_id = r.id
      AND res.status IN ('reserved', 'confirmed', 'checked_in', 'pending_payment')
      AND tstzrange(res.checkin_at, res.checkout_at, '[)') &&
          tstzrange($1::timestamptz, $2::timestamptz, '[)')
  );
```

## 10. Endpoints REST com Exemplos

Base URL sugerida: `/api/v1`.

### Clientes

`POST /customers`

Request:

```json
{
  "name": "Maria Souza",
  "cpf": "12345678901",
  "email": "maria@email.com",
  "phone": "+5588999999999",
  "birth_date": "1990-04-12"
}
```

Response:

```json
{
  "id": "6c7a6f5a-4efe-4a3a-a8cc-b711c0879610",
  "name": "Maria Souza",
  "status": "active",
  "loyalty": {
    "lifetime_points": 0,
    "redeemable_points": 0
  }
}
```

`GET /customers/:id`

`GET /customers/:id/loyalty`

Response:

```json
{
  "customer_id": "6c7a6f5a-4efe-4a3a-a8cc-b711c0879610",
  "current_level": {
    "name": "EXPERIENCIA",
    "bonus_percentage": 20
  },
  "next_level": {
    "name": "REAL",
    "min_points": 1000
  },
  "lifetime_points": 420,
  "redeemable_points": 300,
  "points_to_next_level": 580,
  "level_progress_percentage": 42
}
```

`GET /customers/:id/points-history`

Response:

```json
{
  "items": [
    {
      "id": "tx-id",
      "type": "earn_reservation",
      "points": 120,
      "description": "Pontos da reserva RES-001",
      "created_at": "2026-05-05T14:00:00.000Z"
    }
  ]
}
```

### Reservas

`POST /reservations`

Request:

```json
{
  "customer_id": "6c7a6f5a-4efe-4a3a-a8cc-b711c0879610",
  "room_id": "room-uuid",
  "checkin_at": "2026-06-10T14:00:00.000Z",
  "checkout_at": "2026-06-12T12:00:00.000Z",
  "payment_method": "pix",
  "origin": "jornada_real",
  "referral_code": "JR-9K4L2Q"
}
```

Response:

```json
{
  "id": "reservation-uuid",
  "status": "pending_payment",
  "total_amount": "480.00",
  "room": {
    "number": "205",
    "suite_type": "REAL"
  },
  "referral": {
    "status": "reserved"
  }
}
```

`GET /reservations/:id`

`PATCH /reservations/:id/checkin`

Response:

```json
{
  "id": "reservation-uuid",
  "status": "checked_in",
  "actual_checkin_at": "2026-06-10T14:10:00.000Z"
}
```

`PATCH /reservations/:id/checkout`

Response:

```json
{
  "id": "reservation-uuid",
  "status": "checked_out",
  "points": {
    "base": 400,
    "bonus": 80,
    "total": 480,
    "transaction_id": "tx-uuid"
  },
  "notifications_created": [
    "post_checkout_points",
    "reward_near"
  ]
}
```

`GET /availability?checkin=2026-06-10&checkout=2026-06-12&suite_type=REAL`

Response:

```json
{
  "checkin": "2026-06-10",
  "checkout": "2026-06-12",
  "items": [
    {
      "room_id": "room-uuid",
      "room_number": "205",
      "suite_type": "REAL",
      "price": "240.00",
      "capacity": 2,
      "features": ["hidro", "ar-condicionado"],
      "available": true
    }
  ]
}
```

### Pontos

`POST /points/credit-reservation/:reservationId`

Response:

```json
{
  "reservation_id": "reservation-uuid",
  "credited": true,
  "points": {
    "base": 100,
    "bonus": 20,
    "total": 120
  }
}
```

`GET /loyalty/progress/:customerId`

Response:

```json
{
  "level_bar": {
    "lifetime_points": 420,
    "current_level": "EXPERIENCIA",
    "next_level": "REAL",
    "points_to_next_level": 580,
    "progress_percentage": 42
  },
  "reward_bar": {
    "redeemable_points": 300,
    "next_reward": {
      "id": "reward-uuid",
      "name": "Drink cortesia",
      "required_points": 500
    },
    "points_to_next_reward": 200,
    "progress_percentage": 60,
    "available_rewards": [],
    "redemptions": []
  }
}
```

`POST /points/manual-adjustment`

Request:

```json
{
  "customer_id": "customer-uuid",
  "points": 50,
  "affects_lifetime": false,
  "description": "Ajuste operacional aprovado"
}
```

### Convite Real

`POST /referrals/generate`

Request:

```json
{
  "customer_id": "customer-uuid",
  "max_uses": 5,
  "expires_in_days": 30
}
```

Response:

```json
{
  "code": "JR-9K4L2Q",
  "link": "https://hotelreal.com/jornada/convite?code=JR-9K4L2Q",
  "whatsapp_message": "To na Jornada Real do Hotel Real\nSe voce reservar por esse link, a gente ganha beneficios\n👉 https://hotelreal.com/jornada/convite?code=JR-9K4L2Q\nDepois me conta"
}
```

`POST /referrals/validate`

Request:

```json
{
  "code": "JR-9K4L2Q",
  "referred_cpf": "98765432100"
}
```

Response:

```json
{
  "valid": true,
  "referrer_customer_id": "customer-uuid",
  "expires_at": "2026-06-04T00:00:00.000Z"
}
```

`POST /referrals/apply-to-reservation`

Request:

```json
{
  "reservation_id": "reservation-uuid",
  "code": "JR-9K4L2Q",
  "referred_customer_id": "customer-uuid"
}
```

`GET /referrals/customer/:customerId`

### Premios

`GET /rewards`

`POST /rewards/redeem`

Request:

```json
{
  "customer_id": "customer-uuid",
  "reward_id": "reward-uuid"
}
```

Response:

```json
{
  "redemption_id": "redemption-uuid",
  "redemption_code": "RW-7H2K9P",
  "status": "active",
  "points_spent": 500,
  "remaining_redeemable_points": 120
}
```

`POST /rewards/use-code`

Request:

```json
{
  "redemption_code": "RW-7H2K9P"
}
```

Response:

```json
{
  "used": true,
  "used_at": "2026-05-05T15:00:00.000Z"
}
```

`GET /rewards/customer/:customerId`

### Notificacoes

`POST /notifications/send-whatsapp`

Request:

```json
{
  "customer_id": "customer-uuid",
  "type": "post_checkout_points",
  "message": "Seus pontos ja foram liberados..."
}
```

`GET /notifications/customer/:customerId`

### Check-out Alert

`GET /checkout-alerts/pending`

Response:

```json
{
  "items": [
    {
      "id": "alert-uuid",
      "reservation_id": "reservation-uuid",
      "room_number": "205",
      "guest_name": "Maria Souza",
      "checkout_time": "2026-05-05T12:00:00.000Z",
      "status": "checked_in",
      "alert_visual": true,
      "alert_sound": true
    }
  ]
}
```

`POST /checkout-alerts/:id/viewed`

SSE:

`GET /events/checkout-alerts`

Evento:

```json
{
  "event": "checkout_alert_event",
  "data": {
    "reservation_id": "reservation-uuid",
    "room_number": "205",
    "guest_name": "Maria Souza",
    "checkout_time": "2026-05-05T12:00:00.000Z",
    "alert_sound": true
  }
}
```

## 11. Pseudocodigo das Funcoes Principais

### calcularPontosReserva()

```ts
async function calcularPontosReserva(reservationId, tx) {
  const reservation = await tx.reservation.findUniqueOrThrow({
    where: { id: reservationId },
    include: {
      customer: { include: { loyalty: { include: { currentLevel: true } } } }
    }
  });

  const rule = await getLoyaltyRule("points_per_currency_unit", tx);
  const pointsPerUnit = rule.pointsPerUnit ?? 1;

  const base = Math.floor(Number(reservation.totalAmount) * pointsPerUnit);
  const bonusPercentage = Number(reservation.customer.loyalty?.currentLevel?.bonusPercentage ?? 0);
  const bonus = Math.floor(base * bonusPercentage / 100);

  return {
    base,
    bonus,
    total: base + bonus,
    bonusPercentage
  };
}
```

### creditarPontosCheckout()

```ts
async function creditarPontosCheckout(reservationId) {
  return prisma.$transaction(async (tx) => {
    const reservation = await tx.$queryRaw`
      SELECT * FROM reservations WHERE id = ${reservationId}::uuid FOR UPDATE
    `;

    if (!reservation) throw new NotFoundError("Reserva nao encontrada");
    if (reservation.status !== "checked_out") throw new DomainError("Reserva ainda nao fez check-out");
    if (reservation.points_credited) return { credited: false, reason: "already_credited" };

    const points = await calcularPontosReserva(reservationId, tx);

    const pointTx = await tx.pointsTransaction.create({
      data: {
        customerId: reservation.customer_id,
        reservationId,
        type: "earn_reservation",
        points: points.total,
        description: `Pontos da reserva ${reservationId}`,
        metadata: points
      }
    });

    await tx.customerLoyalty.upsert({
      where: { customerId: reservation.customer_id },
      create: {
        customerId: reservation.customer_id,
        lifetimePoints: points.total,
        redeemablePoints: points.total
      },
      update: {
        lifetimePoints: { increment: points.total },
        redeemablePoints: { increment: points.total }
      }
    });

    await atualizarNivelCliente(reservation.customer_id, tx);

    await tx.reservation.update({
      where: { id: reservationId },
      data: {
        pointsCredited: true,
        pointsCreditedAt: new Date(),
        pointsTransactionId: pointTx.id
      }
    });

    await creditarIndicacaoSeExistir(reservationId, tx);
    await criarNotificacaoPostCheckout(reservation.customer_id, reservationId, tx);
    await criarNotificacaoPremioProximoSeElegivel(reservation.customer_id, tx);

    return { credited: true, points, transactionId: pointTx.id };
  });
}
```

### atualizarNivelCliente()

```ts
async function atualizarNivelCliente(customerId, tx) {
  const loyalty = await tx.customerLoyalty.findUniqueOrThrow({
    where: { customerId }
  });

  const level = await tx.loyaltyLevel.findFirst({
    where: {
      active: true,
      minPoints: { lte: loyalty.lifetimePoints }
    },
    orderBy: [{ minPoints: "desc" }, { sortOrder: "desc" }]
  });

  if (!level) return null;

  await tx.customerLoyalty.update({
    where: { customerId },
    data: { currentLevelId: level.id }
  });

  return level;
}
```

### gerarConviteReal()

```ts
async function gerarConviteReal(customerId, options) {
  const customer = await prisma.customer.findUniqueOrThrow({ where: { id: customerId } });
  if (customer.status !== "active") throw new DomainError("Cliente inativo");

  const code = await generateUniqueCode("JR");
  const expiresAt = addDays(new Date(), options.expiresInDays ?? 30);

  const referralCode = await prisma.referralCode.create({
    data: {
      customerId,
      code,
      maxUses: options.maxUses ?? 5,
      expiresAt
    }
  });

  const link = `${process.env.PUBLIC_APP_URL}/jornada/convite?code=${code}`;

  return {
    code,
    link,
    whatsappMessage: `To na Jornada Real do Hotel Real\nSe voce reservar por esse link, a gente ganha beneficios\n👉 ${link}\nDepois me conta`
  };
}
```

### validarCupomAmigo()

```ts
async function validarCupomAmigo(code, referredCpf, tx = prisma) {
  const referral = await tx.referralCode.findUnique({
    where: { code },
    include: { customer: true }
  });

  if (!referral) return { valid: false, reason: "invalid_code" };
  if (referral.status !== "active") return { valid: false, reason: referral.status };
  if (referral.expiresAt <= new Date()) return { valid: false, reason: "expired" };
  if (referral.currentUses >= referral.maxUses) return { valid: false, reason: "max_usage_reached" };
  if (normalizeCpf(referral.customer.cpf) === normalizeCpf(referredCpf)) {
    return { valid: false, reason: "self_referral" };
  }

  const referred = await tx.customer.findUnique({ where: { cpf: normalizeCpf(referredCpf) } });
  if (referred) {
    const existingUse = await tx.referralUse.findFirst({
      where: { referredCustomerId: referred.id }
    });
    if (existingUse) return { valid: false, reason: "cpf_already_referred" };
  }

  return { valid: true, referral };
}
```

### resgatarPremio()

```ts
async function resgatarPremio(customerId, rewardId) {
  return prisma.$transaction(async (tx) => {
    const reward = await tx.reward.findUniqueOrThrow({ where: { id: rewardId } });
    if (!reward.active) throw new DomainError("Premio inativo");

    const loyaltyRows = await tx.$queryRaw`
      SELECT * FROM customer_loyalty WHERE customer_id = ${customerId}::uuid FOR UPDATE
    `;
    const loyalty = loyaltyRows[0];
    if (!loyalty) throw new DomainError("Cliente sem carteira de pontos");
    if (loyalty.redeemable_points < reward.requiredPoints) throw new DomainError("Saldo insuficiente");

    if (reward.stock !== null) {
      const updated = await tx.reward.updateMany({
        where: { id: rewardId, stock: { gt: 0 } },
        data: { stock: { decrement: 1 } }
      });
      if (updated.count !== 1) throw new DomainError("Premio sem estoque");
    }

    const code = await generateUniqueCode("RW");

    await tx.pointsTransaction.create({
      data: {
        customerId,
        type: "redeem_reward",
        points: -reward.requiredPoints,
        description: `Resgate do premio ${reward.name}`,
        metadata: { rewardId }
      }
    });

    await tx.customerLoyalty.update({
      where: { customerId },
      data: { redeemablePoints: { decrement: reward.requiredPoints } }
    });

    return tx.rewardRedemption.create({
      data: {
        customerId,
        rewardId,
        pointsSpent: reward.requiredPoints,
        redemptionCode: code,
        expiresAt: addDays(new Date(), 30)
      }
    });
  });
}
```

### inutilizarCodigoAntigo()

```ts
async function inutilizarCodigoAntigo(type, code, reason, actor) {
  return prisma.$transaction(async (tx) => {
    if (type === "referral") {
      const updated = await tx.referralCode.updateMany({
        where: { code, status: "active" },
        data: { status: reason === "expired" ? "expired" : "cancelled" }
      });
      if (updated.count !== 1) throw new DomainError("Codigo nao esta ativo");
    }

    if (type === "reward") {
      const updated = await tx.rewardRedemption.updateMany({
        where: { redemptionCode: code, status: "active" },
        data: { status: reason === "expired" ? "expired" : "cancelled" }
      });
      if (updated.count !== 1) throw new DomainError("Codigo nao esta ativo");
    }

    await tx.auditLog.create({
      data: {
        actorType: actor.type,
        actorId: actor.id,
        entityType: type,
        entityId: code,
        action: `invalidate_${reason}`,
        after: { code, reason }
      }
    });
  });
}
```

### buscarSuitesDisponiveis()

```ts
async function buscarSuitesDisponiveis({ checkin, checkout, suiteTypeId }) {
  if (new Date(checkout) <= new Date(checkin)) {
    throw new ValidationError("checkout deve ser maior que checkin");
  }

  return prisma.$queryRaw`
    SELECT
      r.id AS room_id,
      r.number AS room_number,
      st.id AS suite_type_id,
      st.name AS suite_type,
      st.base_price AS price,
      st.capacity AS capacity,
      st.description AS description,
      true AS available
    FROM rooms r
    JOIN suite_types st ON st.id = r.suite_type_id
    WHERE r.status = 'available'
      AND st.active = true
      AND (${suiteTypeId}::uuid IS NULL OR st.id = ${suiteTypeId}::uuid)
      AND NOT EXISTS (
        SELECT 1 FROM reservations res
        WHERE res.room_id = r.id
          AND res.status IN ('reserved', 'confirmed', 'checked_in', 'pending_payment')
          AND tstzrange(res.checkin_at, res.checkout_at, '[)') &&
              tstzrange(${checkin}::timestamptz, ${checkout}::timestamptz, '[)')
      )
    ORDER BY st.base_price, r.number
  `;
}
```

### emitirAlertaCheckout()

```ts
async function emitirAlertaCheckout(now = new Date()) {
  const reservations = await prisma.reservation.findMany({
    where: {
      status: { in: ["checked_in", "confirmed"] },
      checkoutAt: { lte: now },
      checkoutAlert: null
    },
    include: { room: true, customer: true }
  });

  for (const reservation of reservations) {
    const alert = await prisma.checkoutAlert.create({
      data: {
        reservationId: reservation.id,
        roomId: reservation.roomId,
        alertTime: now,
        soundEnabled: true,
        status: "pending"
      }
    });

    await prisma.notification.create({
      data: {
        reservationId: reservation.id,
        customerId: reservation.customerId,
        type: "checkout_alert",
        channel: "system",
        message: `Checkout pendente do quarto ${reservation.room.number}`,
        dedupeKey: `checkout_alert:${reservation.id}`
      }
    });

    sse.publish("checkout_alert_event", {
      alert_id: alert.id,
      reservation_id: reservation.id,
      room_number: reservation.room.number,
      guest_name: reservation.customer.name,
      checkout_time: reservation.checkoutAt,
      status: reservation.status,
      alert_sound: true
    });
  }
}
```

## 12. Estrutura de Pastas do Backend

```text
backend-node/
  prisma/
    schema.prisma
    migrations/
    seed.ts
  src/
    main.ts
    app.module.ts
    common/
      errors/
      decorators/
      guards/
      interceptors/
      pipes/
      utils/
    auth/
      auth.module.ts
      auth.controller.ts
      auth.service.ts
      jwt.strategy.ts
    prisma/
      prisma.module.ts
      prisma.service.ts
    customers/
      customers.controller.ts
      customers.service.ts
      dto/
    reservations/
      reservations.controller.ts
      reservations.service.ts
      availability.service.ts
      dto/
    loyalty/
      loyalty.controller.ts
      loyalty.service.ts
      points.service.ts
      levels.service.ts
      dto/
    referrals/
      referrals.controller.ts
      referrals.service.ts
      referral-code.service.ts
      dto/
    rewards/
      rewards.controller.ts
      rewards.service.ts
      redemption-code.service.ts
      dto/
    notifications/
      notifications.controller.ts
      notifications.service.ts
      notification-worker.ts
      whatsapp/
        whatsapp-provider.interface.ts
        zapi.provider.ts
        evolution.provider.ts
        twilio.provider.ts
        cloud-api.provider.ts
    checkout-alerts/
      checkout-alerts.controller.ts
      checkout-alerts.service.ts
      checkout-alerts.gateway.ts
    audit/
      audit.service.ts
  test/
    loyalty.spec.ts
    referrals.spec.ts
    rewards.spec.ts
    availability.spec.ts
```

## 13. Cuidados para Evitar Bugs, Duplicidade e Fraude

- Usar transacao em credito de pontos, resgate, uso de codigo, criacao de reserva e checkout.
- Criar exclusion constraint para impedir overbooking no banco.
- Usar `FOR UPDATE` ao mexer em saldo de pontos e codigos.
- Usar idempotencia em endpoints criticos.
- Nunca confiar em preco vindo do frontend; calcular `total_amount` no backend.
- Normalizar CPF e telefone antes de salvar.
- Proibir autoindicacao por CPF e por `customer_id`.
- Garantir `ReferralUse` unico por CPF/cliente indicado.
- Registrar `points_transactions` para todo movimento.
- Fazer workers de notificacao idempotentes com `dedupe_key`.
- Nao enviar WhatsApp repetido sem nova transacao de pontos ou janela minima.
- Expirar codigos por job agendado e por validacao lazy no uso.
- Proteger endpoints administrativos com roles.
- Registrar auditoria para ajuste manual, cancelamento de codigo, uso de premio e alteracao de nivel/regra.
- Testar concorrencia: dois resgates simultaneos, duas reservas no mesmo quarto e duplo checkout.

## 14. Checklist Final de Implementacao

- [ ] Criar projeto Node/NestJS ou modulo equivalente no backend atual.
- [ ] Configurar PostgreSQL, Prisma e migrations.
- [ ] Aplicar `schema.prisma`.
- [ ] Criar migration SQL da exclusion constraint de reservas.
- [ ] Seed de niveis `EXPERIENCIA` e `REAL`.
- [ ] Seed das regras `points_per_currency_unit`, `reward_near_threshold_percentage`, `reward_near_resend_days`, `referral_bonus_points`.
- [ ] Implementar JWT e roles.
- [ ] Implementar DTOs e validacoes.
- [ ] Implementar disponibilidade com revalidacao transacional.
- [ ] Implementar criacao de reserva com aplicacao opcional de convite.
- [ ] Implementar check-in e check-out.
- [ ] Implementar credito idempotente de pontos.
- [ ] Implementar progresso de nivel e barra de premios.
- [ ] Implementar Convite Real com max uses, expiracao e anti-autoindicacao.
- [ ] Implementar resgate e uso de premios.
- [ ] Implementar fila de notificacoes e adapter WhatsApp.
- [ ] Implementar alerta de check-out por SSE/WebSocket.
- [ ] Implementar audit logs.
- [ ] Criar testes unitarios de calculo de pontos.
- [ ] Criar testes de integracao para credito duplicado, cupom duplicado, premio duplicado e overbooking.
- [ ] Criar observabilidade minima: logs estruturados, metricas de fila e falhas de WhatsApp.

