# Jornada Real - Roadmap para IA/Dev Ler

Guia de navegação inteligente do JORNADA_REAL_FEATURES_CHECKLIST.md

---

## 📖 Ordem de Leitura Recomendada

### Passo 1️⃣: Entender o Contexto (5 min)
**Arquivo:** `JORNADA_REAL_FEATURES_CHECKLIST.md`
**Seções:**
1. "📊 Resumo Executivo" — tabela com prioridades
2. "📅 Roadmap Recomendado" — fases 1-3

**O que você aprende:**
- Existem 11 funcionalidades
- Total: 22-29 dias (4-5 semanas)
- 3 fases: MVP → Notificações → Segurança

**Saída esperada:** "Entendi o escopo completo"

---

### Passo 2️⃣: Identificar Sua Função (2 min)
Escolha qual tipo você é:

#### 👨‍💻 Dev Backend
→ Vá para: **"Backend Roadmap"**

#### 👨‍💻 Dev Frontend  
→ Vá para: **"Frontend Roadmap"**

#### 🧪 QA/Tester
→ Vá para: **"QA Roadmap"**

#### 📊 Product Manager
→ Vá para: **"Product Roadmap"**

#### 🤖 IA Implementando Code
→ Vá para: **"IA Implementation Roadmap"**

---

## 🔴 Backend Roadmap

### Fase 1 (Semana 1-2): Core Points System
```
Dia 1-2: Funcionalidade 1️⃣ (Cupom Amigo)
├─ Modelos Prisma
│  └─ ReferralCode (já existe no schema)
│  └─ Adicionar campos: status, currentUses
├─ Endpoints
│  ├─ POST /referrals/generate → gera código
│  ├─ GET /referrals/{code} → valida
│  └─ POST /referrals/apply-to-reservation → aplica benefício
├─ Lógica
│  ├─ Ao usar código: credita pontos para ambos
│  ├─ Validar: ativo, não expirado, max_uses ok
│  └─ Dedupe: só credita 1x por cliente
└─ Testes
   ├─ Gerar cupom
   ├─ Usar cupom válido
   └─ Rejeitar cupom maxed

Dia 3-4: Funcionalidade 2️⃣ (Benefícios Níveis)
├─ Models OK (LoyaltyLevel já tem bonus_percentage)
├─ Lógica no PointsTransaction
│  ├─ Ao creditar pontos: consultar nível do cliente
│  ├─ Fórmula: points * (1 + bonus_percentage/100)
│  └─ Salvar bonus% na metadata
└─ Testes
   ├─ Nível Essência (0%) = 50pts
   ├─ Nível Experiência (20%) = 60pts
   └─ Nível Real (40%) = 70pts

Dia 5: Funcionalidade 7️⃣ (Invalidar Códigos)
├─ Models
│  ├─ ReferralCode.status: active|used|expired|cancelled|max_usage_reached
│  └─ RewardRedemption.status: active|used|expired|cancelled
├─ Validação em endpoints
│  ├─ Ao usar: status==active + currentUses < maxUses
│  └─ Ao validar código: status==active + expiresAt > now
├─ Job automático
│  └─ Verifica expirados → muda para expired
└─ Testes
   ├─ Cupom com max_uses=5
   ├─ Usar 5x → passa para USED
   └─ 6ª tentativa → rejeitado

Dia 5: Funcionalidade 8️⃣ (Remover Suites Reservadas)
├─ Query SQL com exclusion constraint (já existe)
├─ Endpoint GET /availability
│  ├─ Params: checkin, checkout, suite_type
│  └─ Retorna quartos sem conflito de datas
└─ Testes
   ├─ Reserva 201 (15-18 jun)
   ├─ Query 16-18 jun
   └─ Resultado: apenas 202, 203 (201 excluído)

Dia 1-2 (Semana 2): Funcionalidade 3️⃣ (Barras Progresso)
├─ GET /customers/{cpf}/loyalty
│  ├─ Retorna: redeemablePoints, lifetimePoints
│  ├─ currentLevel + nextLevel
│  └─ rewardsUnlocked, rewardsTotal
└─ Testes
   ├─ Customer com 72/90 pontos
   └─ Response deve ter ambos os níveis
```

### Fase 2 (Semana 3): Notificações
```
Dia 1-2: Funcionalidade 4️⃣ (Aviso Prêmio Próximo)
├─ Job cron a cada 10 min
├─ Query: customers com (nextRewardPoints - redeemablePoints) <= 10
├─ Enviar WhatsApp via POST /notifications/send-whatsapp
└─ Dedupe: não 2x no mesmo dia

Dia 3: Funcionalidade 5️⃣ (Msg Pós Check-out)
├─ Hook: quando PointsTransaction criada (type: earn_reservation)
├─ Dispara POST /notifications/send-whatsapp
└─ Template com: pontos ganhos, bônus%, saldo novo

Dia 4: Funcionalidade 6️⃣ (Som Check-out)
├─ Endpoint GET /checkout-alerts/pending
├─ WebSocket wss://api/checkout-alerts (opcional)
└─ Marcar alert como "viewed"

Dia 5: Funcionalidade 🔟 (Confirmação Check-in Admin)
├─ Model CheckinApproval
├─ Endpoint POST /checkins/request-cash-approval
│  ├─ Gera codigo CHK-ABC123XYZ
│  ├─ Válido por 30min
│  └─ Envia WhatsApp para admin
├─ Endpoint POST /checkins/{code}/approve
│  └─ Desbloqueia check-in, invalida código
└─ Testes
   ├─ Solicitar aprovação
   ├─ Admin aprova
   └─ Código não pode reusar
```

### Fase 3 (Semana 4-5): Security & Promos
```
Dia 1-2: Funcionalidade 1️⃣1️⃣ (Autenticar Cadastro)
├─ Endpoint GET /customers/{cpf}
│  └─ Validar existência
├─ Endpoint POST /auth/otp/generate
│  ├─ Gera OTP 6 dígitos
│  ├─ Válido por 5min
│  └─ Envia via WhatsApp
├─ Endpoint POST /auth/otp/validate
│  ├─ Valida OTP
│  ├─ Max 3 tentativas
│  └─ Retorna JWT token
└─ Rate limit: 1 OTP/min

Dia 3-5: Funcionalidade 9️⃣ (Gerador Cupons)
├─ Model DiscountCoupon
│  ├─ code, discountType, discountValue
│  ├─ maxUses, currentUses
│  ├─ validFrom, validUntil
│  └─ status
├─ Model InfluencerCoupon (extends DiscountCoupon)
│  ├─ influencerName
│  ├─ influencerLink
│  └─ comissionPercentage
├─ Endpoints admin
│  ├─ POST /admin/coupons/generate
│  ├─ GET /admin/coupons
│  ├─ PUT /admin/coupons/{id}
│  └─ DELETE /admin/coupons/{id}
├─ Endpoint público
│  └─ POST /reservations { discount_coupon: "..." }
└─ Rastreamento
   └─ Dashboard: "Influencer X: 5 clientes, R$500 comissão"
```

---

## 👨‍💻 Frontend Roadmap

### Fase 1 (Semana 1-2): Integration & UI
```
Dia 1-2: Funcionalidade 1️⃣ (Cupom Amigo)
├─ Tela "/meu-cupom" ou widget em "/entrar-jornada-real"
├─ Exibe código gerado
├─ Botão "Copiar código"
├─ Botão "Compartilhar WhatsApp"
│  └─ Pré-popula mensagem
├─ Histórico de usos
│  └─ "3/5 amigos usaram, +150 pontos ganhos"
└─ Testes
   ├─ Gerar cupom
   ├─ Copiar funciona
   ├─ Compartilhar abre WhatsApp
   └─ Histórico atualiza

Dia 3: Funcionalidade 2️⃣ (Benefícios Níveis)
├─ /nivel_jornada_real
│  └─ Exibir "Experiência: +20% de pontos por reserva"
├─ /consultar-pontos
│  └─ Badge "Seu bônus atual: +20%"
├─ /reservar
│  └─ Estimativa ao confirmar
│     "Reserva R$500 → 60 pontos (com +20% bônus)"
└─ Testes
   ├─ Níveis exibem bônus correto
   └─ Estimativa calcula certo

Dia 4: Funcionalidade 3️⃣ (Barras Progresso)
├─ /consultar-pontos
│  ├─ Barra nível: width = (currentPoints / nextLevelPoints) * 100
│  └─ Barra prêmios: width = (rewardsUnlocked / rewardsTotal) * 100
└─ Testes
   ├─ 72/90 = 80%
   ├─ 2/4 = 50%
   └─ Animação suave

Dia 5: Funcionalidade 8️⃣ (Remover Suites Reservadas)
├─ /reservar
│  ├─ Ao buscar disponibilidade
│  └─ Mostra apenas quartos sem conflito
├─ Query params: ?checkin=YYYY-MM-DD&checkout=YYYY-MM-DD
└─ Testes
   ├─ Reserva 201 (15-18 jun)
   ├─ Busca 16-18 jun
   └─ Resultado mostra apenas 202, 203

Dia 1-2 (Semana 2): Funcionalidade 7️⃣ (Invalidar Códigos)
├─ /meu-cupom
│  └─ "Status: Ativo | 3/5 usos"
├─ Se maxed
│  └─ "Cupom expirou, gere um novo"
├─ /resgate_dos_premios
│  └─ Código resgatado fica "Resgatado" (cinzento)
└─ Testes
   ├─ Cupom ativo: clicável
   ├─ Cupom maxed: botão desabilitado
   └─ Código resgatado: não reutilizável
```

### Fase 2 (Semana 3): Notifications
```
Dia 1-2: Funcionalidade 4️⃣ (Aviso Prêmio Próximo)
├─ Nenhuma mudança frontend
└─ Apenas backend (notificação WhatsApp)

Dia 3: Funcionalidade 5️⃣ (Msg Pós Check-out)
├─ Nenhuma mudança frontend
└─ Apenas backend (notificação WhatsApp)

Dia 4: Funcionalidade 6️⃣ (Som Check-out)
├─ Sistema de reserva (dashboard recepção)
├─ Audio element: <audio id="checkout-alert">
├─ Listener WebSocket / polling
├─ Toca som: /public/sounds/checkout-alert.mp3
└─ Toast com info do quarto
   "CHECKOUT - Quarto 201"

Dia 5: Funcionalidade 🔟 (Confirmação Check-in Admin)
├─ Painel admin (dashboard recepcão)
├─ Notificações em tempo real
├─ Lista: cliente, quarto, valor, código
├─ Botão "Aprovar Check-in"
└─ Histórico de aprovações
```

### Fase 3 (Semana 4-5): Auth & Promos
```
Dia 1-2: Funcionalidade 1️⃣1️⃣ (Autenticar Cadastro)
├─ /reservar
│  └─ Seção de autenticação no início
│     1. CPF: [INPUT]
│     2. Se existe: dados pre-preenchidos
│     3. Botão "Continuar"
│     4. OTP enviado para WhatsApp
│     5. Código: [___][___][___][___][___][___]
│     6. Botão "Confirmar"
│     7. Acesso à reserva
├─ Validações
│  ├─ CPF: ###.###.###-##
│  ├─ CPF válido (algoritmo)
│  └─ OTP: 6 dígitos
└─ Testes
   ├─ CPF válido/inválido
   ├─ OTP correto/incorreto
   └─ Max 3 tentativas

Dia 3-5: Funcionalidade 9️⃣ (Gerador Cupons)
├─ Painel admin
│  ├─ Formulário "Criar Cupom"
│  ├─ Tipo: Desconto | Influencer
│  ├─ Valor: 15% ou R$50
│  ├─ Válido até: DATE
│  ├─ Max usos: NUMBER
│  └─ Botão "Gerar"
├─ Tabela de cupons
│  ├─ Código | Desconto | Status | Usos | Ação
│  ├─ VERAO2026 | 15% | ATIVO | 25/100 | [Desativar]
│  └─ INGRID_INF | 20% | ATIVO | 5 | [Ver stats]
├─ /reservar
│  ├─ Campo "Cupom de desconto"
│  ├─ Ao validar
│  └─ "15% desconto → novo preço R$425"
└─ Testes
   ├─ Criar cupom
   ├─ Usar cupom
   ├─ Validar preço
   └─ Stats influencer
```

---

## 🧪 QA Roadmap

### Ordem de Testes

```
Fase 1: Functional Tests
├─ 1️⃣ Cupom Amigo
│  ├─ [ ] Gerar código
│  ├─ [ ] Código válido
│  ├─ [ ] Código inválido
│  ├─ [ ] Max usos atingido
│  └─ [ ] Pontos creditados corretamente
├─ 2️⃣ Benefícios Níveis
│  ├─ [ ] Essência: 0% bônus
│  ├─ [ ] Experiência: 20% bônus
│  ├─ [ ] Real: 40% bônus
│  └─ [ ] Bônus calculado corretamente
├─ 3️⃣ Barras Progresso
│  ├─ [ ] Barra nível calcula %
│  ├─ [ ] Barra prêmios calcula %
│  └─ [ ] Animação suave
├─ 7️⃣ Invalidar Códigos
│  ├─ [ ] Status muda para USED
│  ├─ [ ] Status muda para EXPIRED
│  └─ [ ] Código expirado rejeita
├─ 8️⃣ Remover Suites
│  ├─ [ ] Suites com conflito não aparecem
│  ├─ [ ] Suites sem conflito aparecem
│  └─ [ ] Datas sobrepostas excluídas
└─ 1️⃣1️⃣ Autenticar Cadastro
   ├─ [ ] CPF válido carrega dados
   ├─ [ ] CPF inválido oferece cadastro
   ├─ [ ] OTP enviado
   ├─ [ ] OTP correto libera reserva
   ├─ [ ] OTP incorreto rejeita (max 3x)
   └─ [ ] Zero pessoas falsas

Fase 2: Integration Tests
├─ 4️⃣ Aviso Prêmio Próximo
│  ├─ [ ] WhatsApp enviado quando faltam <10pts
│  ├─ [ ] Mensagem correta
│  └─ [ ] Não duplica no mesmo dia
├─ 5️⃣ Msg Pós Check-out
│  ├─ [ ] WhatsApp enviado após check-out
│  ├─ [ ] Pontos corretos na mensagem
│  └─ [ ] Bônus refletido corretamente
├─ 6️⃣ Som Check-out
│  ├─ [ ] Som toca no horário certo
│  ├─ [ ] Volume adequado
│  └─ [ ] Notificação visual aparece
└─ 🔟 Confirmação Check-in Admin
   ├─ [ ] WhatsApp enviado para admin
   ├─ [ ] Admin consegue aprovar
   ├─ [ ] Check-in desbloqueado após aprovação
   └─ [ ] Código não reuza

Fase 3: E2E Tests
├─ Fluxo 1: Cupom Amigo → Check-in → Pontos
│  ├─ [ ] Cliente A gera cupom
│  ├─ [ ] Cliente B usa cupom
│  ├─ [ ] Ambos ganham pontos
│  └─ [ ] Ambos veem pontos atualizados
├─ Fluxo 2: Subir de nível → Desbloquear prêmio
│  ├─ [ ] Cliente sobe de Essência para Experiência
│  ├─ [ ] Bônus passa de 0% para 20%
│  ├─ [ ] Resgate de prêmio funciona
│  └─ [ ] Código gerado corretamente
├─ Fluxo 3: Reservar com CPF + Cupom
│  ├─ [ ] CPF autenticado
│  ├─ [ ] Cupom aplicado
│  ├─ [ ] Preço desconto refletido
│  └─ [ ] Reserva criada com desconto
└─ Fluxo 4: Admin confirmando check-in
   ├─ [ ] Admin recebe WhatsApp
   ├─ [ ] Admin aprova
   ├─ [ ] Cliente acessa quarto
   └─ [ ] Pontos creditados após checkout
```

---

## 📊 Product Roadmap

### Comunicação Stakeholders

#### Sprint 1 (Semana 1-2)
```
🚀 MVP — Sistema de Pontos & Níveis
├─ Cupom Amigo (indicação)
├─ Benefícios por Nível (+20%, +40%)
├─ Barras de Progresso (visual)
├─ Remoção de Suites Reservadas (UX)
└─ Invalidação de Códigos (segurança)

Valor entregue:
├─ Hóspedes ganham pontos nas reservas
├─ Podem compartilhar cupom amigo
├─ Veem claramente progresso para próximo nível
└─ Segurança: códigos expiram
```

#### Sprint 2 (Semana 3)
```
📬 Notificações 360°
├─ Aviso quando prêmio está perto (WhatsApp)
├─ Confirmação de pontos pós check-out
├─ Som alerta de checkout (recepção)
├─ Aprovação de check-in por admin
└─ Tudo via WhatsApp (comunicação direta)

Valor entregue:
├─ Hóspedes engajados com notificações
├─ Recepção gerencia checkout eficientemente
└─ Zero perda de informação
```

#### Sprint 3 (Semana 4-5)
```
🔐 Segurança & Promoções
├─ CPF + OTP autenticação (anti-fraude)
├─ Gerador de cupons para promoções
├─ Links rastreados para influencers
└─ Comissão automática calculada

Valor entregue:
├─ Zero reservas fraudulentas
├─ Campanhas promocionais estruturadas
├─ Integração com influencers escalável
└─ ROI rastreável por influencer
```

### Métricas de Sucesso
```
Fase 1:
├─ Cupom Amigo: 30% clientes indicam alguém
├─ Taxa de uso: 50% de clientes novos via cupom
└─ Pontos: média 100 pontos por hóspede

Fase 2:
├─ Abertura WhatsApp: >80%
├─ Engajamento: 60% clientes checam progresso 2x
└─ Check-out: -90% erros manuais (som alerta)

Fase 3:
├─ Cadastro autenticado: 100%
├─ Taxa de fraude: <1%
├─ Influencers: 5+ parceiros ativos
└─ Cupom influencer: 20% de novas reservas
```

---

## 🤖 IA Implementation Roadmap

### Se você é uma IA implementando tudo:

#### Leitura Obrigatória (ordem)
1. ✅ Este arquivo (você está aqui)
2. `JORNADA_REAL_FEATURES_CHECKLIST.md` → Seção 1️⃣-1️⃣1️⃣
3. `JORNADA_REAL_MOCKS_SCHEMA.md` → Schema esperado
4. `JORNADA_REAL_SKILLS.md` → Integração mocks

#### Implementação por Fase

**Fase 1 (Dias 1-10):**
```
Dia 1-2: Backend 1️⃣ (Cupom Amigo)
├─ Ler "1️⃣ Cupom Amigo - Backend Necessário"
├─ Implementar endpoints
├─ Escrever testes
└─ Fazer merge

Dia 3: Backend 2️⃣ (Benefícios Níveis)
├─ Ler spec
├─ Implementar lógica de bônus
├─ Testes
└─ Merge

Dia 4-5: Backend 7️⃣ + 8️⃣ (Invalidar + Suites)
├─ Implementar status logic
├─ Endpoint de disponibilidade
└─ Merge

Dia 6-7: Frontend 1️⃣ + 2️⃣ + 3️⃣
├─ Tela cupom amigo
├─ Exibir benefícios níveis
├─ Barras progresso
└─ Merge

Dia 8-10: Testes E2E fase 1
├─ QA testa fluxo completo
├─ Fix bugs
└─ Deploy staging
```

**Fase 2 (Dias 11-15):**
```
Dia 11-12: Backend 4️⃣ + 5️⃣ (Notificações)
├─ Implementar WhatsApp jobs
├─ Testes
└─ Merge

Dia 13: Backend 6️⃣ + 🔟 (Sound + Approval)
├─ Endpoints check-out
├─ Admin approval flow
└─ Merge

Dia 14-15: Frontend 4️⃣ + 5️⃣ + 6️⃣ + 🔟
├─ Dashboard recepcão
├─ Painel admin
├─ Listeners
└─ Merge
```

**Fase 3 (Dias 16-20):**
```
Dia 16-17: Backend 1️⃣1️⃣ (Autenticação)
├─ CPF validation
├─ OTP generation
├─ OTP validation
└─ Merge

Dia 18-20: Backend + Frontend 9️⃣ (Cupons)
├─ Models e endpoints
├─ Admin painel
├─ Validação cupom em reserva
└─ Merge
```

#### Checklist por Implementação
```
Para CADA funcionalidade:
├─ [ ] Ler a seção no CHECKLIST.md
├─ [ ] Ler schema/models esperados no MOCKS_SCHEMA.md
├─ [ ] Implementar Backend
│  ├─ [ ] Models/migrations
│  ├─ [ ] Endpoints (criar, validar, listar)
│  ├─ [ ] Lógica de negócio
│  ├─ [ ] Testes unitários
│  └─ [ ] Testes API (curl)
├─ [ ] Integrar Frontend
│  ├─ [ ] Chamar endpoints corretos
│  ├─ [ ] Remover mocks (se houver)
│  ├─ [ ] UI/UX conforme spec
│  └─ [ ] Testes componentes
├─ [ ] Testes E2E
│  ├─ [ ] Fluxo completo frontend→backend
│  └─ [ ] Casos de erro
└─ [ ] Code review + merge
```

#### Dependências (ordem crítica)
```
1️⃣ Cupom Amigo → depende de: ReferralCode model
2️⃣ Benefícios Níveis → depende de: LoyaltyLevel.bonusPercentage  
3️⃣ Barras Progresso → depende de: GET /customers/{cpf}/loyalty
7️⃣ Invalidar Códigos → depende de: status enums em models
8️⃣ Remover Suites → depende de: GET /availability funcionando
───────────────────────────────────────────────────
1️⃣1️⃣ Autenticar Cadastro → depende de: GET /customers/{cpf}
9️⃣ Gerador Cupons → depende de: DiscountCoupon model novo
```

#### Ordem Recomendada para IA
1. **Backend models & migrations** (Dias 1-3)
   - ReferralCode.status
   - RewardRedemption.status
   - DiscountCoupon (novo)
   - InfluencerCoupon (novo)
   - CheckinApproval (novo)

2. **Backend endpoints** (Dias 4-10)
   - Core CRUD para cada modelo
   - Validações de negócio
   - Jobs automáticos (cron)

3. **Frontend integração** (Dias 11-15)
   - Remover mocks
   - Chamar APIs
   - UI refinement

4. **Testes & refinement** (Dias 16-20)
   - E2E workflows
   - Bug fixes
   - Deploy

---

## 🎯 Quick Reference

**Estou implementando 1️⃣ (Cupom Amigo):**
→ Passo 1: Ler seção "1️⃣ Cupom Amigo" do CHECKLIST.md
→ Passo 2: Implementar "Backend Necessário"
→ Passo 3: Rodar testes conforme seção "Testes"

**Estou fazendo code review de funcionalidade 2️⃣:**
→ Ir para "2️⃣ Benefícios dos Níveis"
→ Verifica se tem: models, endpoints, lógica, testes
→ Compara com spec de "Backend Necessário"

**Testes falhando em feature 8️⃣:**
→ Ler "8️⃣ Remover Suites Reservadas - Testes"
→ Rodar exemplos curl fornecidos
→ Debugar query de disponibilidade

**QA testando fluxo E2E:**
→ Ir para "QA Roadmap" → "Fase 1: Functional Tests"
→ Seguir checklist de 1️⃣ até 1️⃣1️⃣
→ Registrar bugs vs. expected behavior em CHECKLIST.md

---

## 📍 Localização dos Arquivos

```
/repositorio_hotelaria/
├─ JORNADA_REAL_LEITURA_IA.md ← VOCÊ ESTÁ AQUI
├─ JORNADA_REAL_FEATURES_CHECKLIST.md ← SPEC TÉCNICA
├─ JORNADA_REAL_MOCKS_SCHEMA.md ← SCHEMA & ENDPOINTS
├─ JORNADA_REAL_SKILLS.md ← INTEGRAÇÃO MOCKS
├─ README_JORNADA_REAL.md ← OVERVIEW
└─ docs/jornada-real-backend-db.md ← ARQUITETURA
```

---

## ✅ Validação de Leitura

**Se você entendeu tudo, consegue responder:**

1. ✓ Quantas funcionalidades? → **11**
2. ✓ Quantas semanas de desenvolvimento? → **4-5**
3. ✓ Qual a prioridade de 1️⃣? → **🔴 ALTA**
4. ✓ Qual a complexidade de 9️⃣? → **Alta (4-5 dias)**
5. ✓ Qual funcionalidade não tem mudança frontend? → **4️⃣ e 5️⃣**
6. ✓ Ordem correta fase 1? → **1, 2, 3, 8, 7** (conforme Backend Roadmap)
7. ✓ Qual deve ser implementada primeiro? → **1️⃣ (Cupom Amigo)**

---

Você está pronto para começar! 🚀
