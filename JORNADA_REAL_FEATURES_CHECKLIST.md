# Jornada Real - Checklist de Funcionalidades

**Atualizacao executiva 2026-07-04:** JR-01 foi validado em service/API/schema/model com `7/7` testes focados passando (`test_indicacao_service.py` + `test_referral_routes.py`); backend corrigido para creditar `50` pontos no Convite Real. Frontend de JR-01 ficou parcial: `/reservar` agora le `?cupom=`/`?codigo=`, valida em `/cupons/validar`, envia `cupom_codigo` para `/public/reservas` e mostra desconto/total, mas ainda falta tela "Meu Cupom" com copiar/WhatsApp/historico. JR-09 foi reconectado parcialmente no admin: `/(dashboard)/pontos-admin` agora usa `/admin/coupons`, gera/edita/desativa por codigo e aceita campanha influencer/comissao; ainda falta UX completa de link rastreado, metricas e detalhes. Validacao rodada: `45 passed` no pacote focado Jornada Real e `next build` OK no frontend.

Roadmap completo com 11 funcionalidades críticas para produção.

---

## 📊 Resumo Executivo

| # | Funcionalidade | Prioridade | Complexidade | Backend | Frontend | WhatsApp | Testes | Est. |
|---|---|----------|--------------|---------|----------|----------|--------|------|
| 1️⃣ | Cupom Amigo | 🔴 Alta | Média | ✅ | 🟡 | 🟡 | ✅ 7/7 | 3-4d |
| 2️⃣ | Benefícios Níveis | 🔴 Alta | Média | ✅ | 🟡 | N/A | ✅ 5/5 | 2-3d |
| 3️⃣ | Barras Progresso | 🔴 Alta | Baixa | ✅ | ✅ | N/A | ✅ 2/2 | 1-2d |
| 4️⃣ | Aviso Prêmio Próximo | 🟡 Média | Média | ✅ | N/A | ✅ | ✅ 2/2 | 2d |
| 5️⃣ | Msg Pós Check-out | 🟡 Média | Baixa | ✅ | N/A | ✅ | ✅ 1/1 | 1d |
| 6️⃣ | Som Check-out | 🟡 Média | Baixa | ✅ | ✅ | N/A | ✅ 2/2 | 1d |
| 7️⃣ | Invalidar Códigos | 🔴 Alta | Média | ✅ | 🟡 | N/A | ✅ 5/5 | 2d |
| 8️⃣ | Remover Suites Reservadas | 🔴 Alta | Média | ✅ | ✅ | N/A | ✅ 3/3 | 2d |
| 9️⃣ | Gerador Cupons | 🟡 Média | Alta | ✅ | 🟡 | N/A | ✅ 3/3 | 4-5d |
| 🔟 | Confirmação Check-in Admin | 🟡 Média | Média | ✅ | ✅ | ✅ | ✅ 4/4 | 2-3d |
| 1️⃣1️⃣ | Autenticar Cadastro | 🔴 Alta | Média | ✅ | ✅ | ✅ | ✅ 6/6 | 2d |

### Sincronizacao dominio + backend + frontend

- [ ] 🟡 1️⃣ Cupom Amigo / Convite Real: backend, API e reserva publica sincronizados; `/reservar` valida/aplica cupom. Falta tela "Meu Cupom" com copiar, WhatsApp direto e historico.
- [ ] 🟡 2️⃣ Beneficios dos niveis: backend calcula Experiencia 2x e Real 4x; frontend consulta/exibe nivel, mas falta mostrar estimativa de ganho na reserva.
- [x] ✅ 3️⃣ Barras de progresso: backend entrega progresso de nivel/premios e `/consultar-pontos` exibe dados reais.
- [x] ✅ 4️⃣ Aviso de premio proximo: backend + WhatsApp sincronizados; sem tela obrigatoria.
- [x] ✅ 5️⃣ Mensagem pos check-out: backend + WhatsApp sincronizados; link leva o cliente para conferir pontos.
- [x] ✅ 6️⃣ Som de check-out: backend gera alerta e frontend de reservas/dashboard notifica com som/quarto.
- [ ] 🟡 7️⃣ Invalidar codigos usados: backend invalida/esgota/renova; frontend mostra parte do status, mas falta UX completa para cupom amigo e renovacao.
- [x] ✅ 8️⃣ Remover suites reservadas: backend filtra disponibilidade e `/reservar` consome a lista real.
- [ ] 🟡 9️⃣ Gerador de cupons: admin frontend ja usa `/admin/coupons` e envia influencer/comissao; falta UX completa de link rastreado, metricas e detalhes.
- [x] ✅ 🔟 Check-in dinheiro com aprovacao admin: backend, WhatsApp e painel admin sincronizados.
- [x] ✅ 1️⃣1️⃣ Autenticar cadastro: `/reservar` consulta/cria cliente, envia/valida OTP e backend bloqueia reserva sem token valido.

**Total estimado: 22-29 dias | Sprint: 4-5 semanas**

**Legenda Backend:** ✅ completo | 🟡 parcial/equivalente existe, mas falta fechar contrato | ❌ precisa implementar

**Legenda Testes:** ✅ N/N = passou N testes | 🟡 prisma = lógica ok, bloqueado por `prisma generate` não rodado no dev local (passa no container com DB)

**Spec Driven:** antes de implementar ou marcar um item como completo, seguir `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md`. Esta checklist registra o status; o spec define o contrato e os critérios de aceite.

**Validação operacional 2026-06-23:** migrations SQL idempotentes da Jornada Real corrigidas para o schema pós-Prisma (`updated_at` sem default), backend rebuildado e `/health` validado em produção local Docker.

---

## 1️⃣ Cupom Amigo - CONVITE REAL

**Atualizacao 2026-07-04:** backend/service/API/schema/model revalidado; `PONTOS_CONVITE_REAL` corrigido para `50` e rotas `/referrals/*` passaram. Frontend agora tem integracao real parcial no `/reservar`: aceita cupom por query string ou digitacao, valida em `/cupons/validar`, envia `cupom_codigo` para `/public/reservas` e mostra desconto/total. Falta "Meu Cupom" com copiar, compartilhar WhatsApp e historico de usos. WhatsApp permanece parcial: backend monta mensagem/link e rota de referral cobre envio via Twilio quando solicitado, mas falta UX de compartilhamento do cliente.

### Descrição
Hóspede recebe código único de indicação. Compartilha via WhatsApp com amigos. Se amigo reservar usando código, ambos ganham benefícios.

### Mensagem Padrão
```
Tô na Jornada Real do Hotel Real 😮
Se você reservar por esse link, a gente ganha benefícios
👉 https://hotel-real.com/reservar?cupom=AMIGO_ABC123XYZ
Depois me conta 🔥
```

### Backend Necessário
**Status Backend:** ✅ Completo — implementado via `Cupom` + `CupomUso` + `Indicacao` e rotas `/referrals/*`; indicador recebe +50 pontos no checkout do indicado com proteção idempotente.

- [x] ✅ Model equivalente a `ReferralCode`: `Cupom`, `CupomUso`, `Indicacao` (não existe model literal `ReferralCode`)
- [x] ✅ Endpoint `POST /referrals/generate` → gera código único
- [x] ✅ Endpoint `GET /referrals/{code}` → valida código
- [x] ✅ Endpoint `POST /referrals/apply-to-reservation` → aplica benefício
- [x] ✅ Lógica: indicado recebe desconto/pontos do cupom; indicador recebe `PONTOS_CONVITE_REAL = 50` no checkout do indicado
- [x] ✅ Validação: código ativo, não expirado, sem max uso atingido

### Frontend Necessário
**Status Frontend:** 🟡 Parcial — `/reservar` ja recebe cupom por query string/digitacao, valida em `/cupons/validar`, envia `cupom_codigo` e exibe desconto/total. Ainda falta tela "Meu Cupom" com copiar, compartilhar WhatsApp e historico.

- [ ] Tela "Meu Cupom" em `/entrar-jornada-real` ou novo route `/meu-cupom`
- [ ] Exibe código gerado
- [ ] Botão "Copiar" → copia link com código
- [ ] Botão "Compartilhar WhatsApp" → abre WhatsApp com mensagem pré-preenchida
- [ ] Historico de usos do código (quantos amigos usaram, pontos ganhos)

- [x] ✅ `/reservar` valida e aplica `cupom_codigo` com dados reais do backend

### WhatsApp Necessário
- [ ] Integração com Twilio/Z-API/Evolution API
- [ ] Template com variáveis:
  ```
  {{NOME_CLIENTE}} está na Jornada Real do Hotel Real 😮
  Se você reservar por esse link, a gente ganha benefícios
  👉 {{LINK_CUPOM}}
  Depois me conta 🔥
  ```

### Benefício
- Indicador: +50 pontos quando indicado fizer check-out
- Indicado: 10% desconto primeira reserva

### Testes
```bash
# 1. Gerar cupom
POST /referrals/generate { customer_id: "user-123" }
→ { code: "AMIGO_ABC123XYZ", link: "https://..." }

# 2. Validar cupom
GET /referrals/AMIGO_ABC123XYZ
→ { valid: true, generated_by: "João", status: "active" }

# 3. Aplicar na reserva
POST /reservations { referral_code: "AMIGO_ABC123XYZ" }
→ desconto aplicado + pontos futuros prometidos

# 4. Checkout do indicado
Checkout reserva indicada
→ indicador recebe +50 pontos uma única vez (origem CONVITE_REAL)
```

**Resultado testes:** ✅ 5/5 — `test_indicacao_service.py`: bloqueia auto-indicação, bloqueia CPF duplicado, dedupe checkout, credita 50 pontos, calcula faltam pontos para próximo prêmio.

**Prioridade:** 🔴 ALTA | **Complexidade:** Média | **Est:** 3-4 dias

---

## 2️⃣ Benefícios dos Níveis

### Descrição
Cada nível concede bônus % de pontos nas reservas.

| Nível | Min Pontos | Bônus % | Exemplo |
|-------|-----------|--------|---------|
| Essência | 0 | 0% | Reserva R$500 = 50 pontos |
| Experiência | 50 | 20% | Reserva R$500 = 60 pontos |
| Real | 90 | 40% | Reserva R$500 = 70 pontos |

### Backend Necessário
**Status Backend:** ✅ Completo — bônus de nível é calculado no checkout e registrado em metadata estruturada da transação de pontos.

- [x] ✅ Model `NivelFidelidade` tem campo `bonusPercentual`
- [x] ✅ Ao creditar pontos na reserva, consulta nível atual do cliente
- [x] ✅ Fórmula: `points = base_points * (1 + bonus_percentage/100)`
- [x] ✅ Registrar bônus em metadata estruturada da `TransacaoPontos` com pontos base, bônus percentual, pontos bônus, nível e total final

### Frontend Necessário
**Status Frontend:** 🟡 Parcial — `/nivel_jornada_real` chama `GET /customers/{cpf}/loyalty`, determina o nível real do cliente e exibe `currentLevel.benefits` incluindo "+20% de pontos por reserva". O que falta é o badge de bônus em `/consultar-pontos` e a estimativa em `/reservar`.

- [x] 🟡 `/nivel_jornada_real` → exibe bônus como benefício do nível atual (via dados reais de loyalty)
- [ ] `/consultar-pontos` → mostrar "Seu bônus atual: +20%" sob o nível
- [ ] `/reservar` → ao confirmar reserva, exibir estimativa:
  ```
  Sua reserva: R$500
  Pontos base: 50
  Seu bônus (Experiência): +20%
  Pontos totais: 60 👑
  ```

### Testes
```bash
# Customer em nível Experiência (20% bônus)
# Faz reserva de R$500 (base 50 pontos)
# Esperado: 50 * 1.20 = 60 pontos creditados
# TransacaoPontos.metadata registra pontos_base=50, bonus_percentual=20,
# pontos_bonus_nivel=10 e pontos_total=60
```

**Resultado testes:** 🟡 prisma — `test_programa_pontos_service.py` bloqueado por `prisma.Client` não gerado; lógica de bônus implementada no `PontosCheckoutService`.

**Validação operacional 2026-06-23:** seeds de `niveis_fidelidade` em `010`, `013` e `014` passaram a informar `created_at`/`updated_at`; backend subiu healthy após rebuild.

**Prioridade:** 🔴 ALTA | **Complexidade:** Média | **Est:** 2-3 dias

---

## 3️⃣ Barras de Progresso

### Descrição
Duas barras animadas que mostram progresso:

#### 3.1 Barra de Nível
- Mostra progresso entre nível atual e próximo
- Exemplo: "72/90 pontos" → barra 80% preenchida
- Atualiza em tempo real quando pontos são creditados

#### 3.2 Barra de Prêmios
- Mostra quantos prêmios já conquistou vs. total disponível
- Exemplo: "2/4 prêmios desbloqueados"
- Resgatando um prêmio → progresso recua (perdeu pontos)

### Backend Necessário
**Status Backend:** ✅ Completo — `GET /customers/{customer_ref}/loyalty` retorna saldo, nível, progresso e contadores `rewards_unlocked`/`rewards_total` para a barra de prêmios.

- [x] ✅ `GET /customers/{cpf}/loyalty` retorna o contrato principal:
  ```json
  {
    "redeemable_points": 72,
    "lifetime_points": 2150,
    "current_level": { "min_points": 50, "name": "Experiência" },
    "next_level": { "min_points": 90, "name": "Real" },
    "rewards_unlocked": 2,
    "rewards_total": 4
  }
  ```

### Frontend Necessário
**Status Frontend:** ✅ Implementado — `/consultar-pontos` chama `GET /customers/{cpf}/loyalty` (fallback para `/pontos/consultar/{cpf}`), usa `loyaltyData` para calcular `levelProgress` e `rewardProgress` e exibe as barras animadas.

- [x] ✅ `/consultar-pontos` chama `GET /customers/{cpf}/loyalty` e alimenta as barras com dados reais
- [x] ✅ Barra de nível: `barra_nivel.percentual` ou cálculo `(currentPoints / nextLevelPoints) * 100`
- [x] ✅ Barra de prêmios: `barra_premios.percentual` ou `rewardProgress`
- [x] ✅ Animação suave (transition CSS)

### Testes
- [x] ✅ Backend: `rewards_unlocked` usa saldo resgatável atual; após resgate, o saldo cai e os prêmios desbloqueados também caem
- [x] ✅ `test_jornada_service.py`: dashboard com 72 pontos e consulta por CPF passaram

**Resultado testes:** ✅ 2/2 — `test_jornada_service.py`: dashboard_jornada_cliente_72_pontos e consulta_jornada_por_cpf passaram.

**Prioridade:** 🔴 ALTA | **Complexidade:** Baixa | **Est:** 1-2 dias

---

## 4️⃣ Aviso de Prêmio Próximo

### Descrição
Cliente a menos de X pontos de desbloquear um prêmio recebe notificação WhatsApp.

### Trigger
- Cliente tem 85 pontos, próximo prêmio custa 90
- Sistema detecta: faltam só 5 pontos
- Envia mensagem WhatsApp

### Mensagem
```
Você está a poucos pontos do seu próximo prêmio 😮
Falta muito pouco…
👉 Continue sua jornada: https://hotel-real.com/consultar-pontos?cpf=...

Próximo prêmio: iPhone 16e (90 pontos)
Você tem: 85 pontos
Faltam: 5 pontos
```

### Backend Necessário
**Status Backend:** ✅ Completo — existe job/endpoint administrativo, detecção por `ProgramaPontosService`, WhatsApp parametrizado e dedupe diário por cliente/prêmio.

- [x] ✅ Job agendável `notificar_premios_proximos_jornada(limit=100)`
- [x] ✅ Endpoint protegido `POST /notificacoes/jornada/premios-proximos`
- [x] ✅ Critério via `ProgramaPontosService` com threshold configurável de prêmio próximo
- [x] ✅ WhatsApp enviado via `WhatsAppService.enviar_aviso_premio_proximo`
- [x] ✅ Dedupe explícito em `logs_jornada`: 1x por cliente/prêmio/dia

### Frontend Necessário
- [ ] Nenhuma mudança (pure backend)

### WhatsApp Necessário
- [x] ✅ Template parametrizado com:
  - `{{CLIENTE_NOME}}`
  - `{{PROXIMA_PREMIO}}`
  - `{{PONTOS_FALTANTES}}`
  - `{{LINK_CONSULTA}}`

### Testes
```bash
# 1. Customer com 85 pontos, prêmio custa 90
# Job executa
# Esperado: WhatsApp enviado

# 2. Mesmo job roda denovo em 5 min
# Esperado: Dedupe impede 2º envio
```

**Prioridade:** 🟡 MÉDIA | **Complexidade:** Média | **Est:** 2 dias

---

## 5️⃣ Mensagem Pós Check-out

### Descrição
Após cliente fazer check-out, recebe WhatsApp informando que pontos foram liberados.

### Trigger
- Reserva status = `checked_out`
- Pontos foram creditados na conta
- Envia mensagem automática

### Mensagem
```
Seus pontos já foram liberados 👑
Você avançou na Jornada Real

Pontos ganhos: 60 (com seu bônus de +20%)
Saldo atual: 132 pontos

👉 Veja seu progresso: https://hotel-real.com/consultar-pontos?cpf=...
```

### Backend Necessário
**Status Backend:** ✅ Completo — mensagem agora dispara quando a transação de pontos pendente é liberada, com dedupe por transação e bônus de nível no payload.

- [x] ✅ Hook fica em `PontosRepository.liberar_pontos_pendentes`, próximo da mudança real de saldo
- [x] ✅ Dedupe por `logs_jornada` usando `transacao_id`
- [x] ✅ WhatsApp enviado via `WhatsAppService.enviar_pontos_pos_checkout`
- [x] ✅ Template/método com pontos ganhos, bônus aplicado, saldo e link de progresso

### Frontend Necessário
- [ ] Nenhuma mudança

### WhatsApp Necessário
- [x] ✅ Template parametrizado

### Testes
```bash
# Checkout API dispara pontos
# Esperado: WhatsApp enviado em segundos
```

**Prioridade:** 🟡 MÉDIA | **Complexidade:** Baixa | **Est:** 1 dia

---

## 6️⃣ Som Característico Check-out

### Descrição
Quando chegar horário de check-out (ex: 11h), sistema de reserva emite som + notificação visual.

### Trigger
- Horário atual = checkout_at da reserva
- Frontend ouve WebSocket ou polling
- Toca som + mostra notificação

### Som
- 3-5 beeps característicos do hotel
- Volume: configurável
- Duração: 2-3 segundos

### Notificação Visual
```
CHECKOUT - Quarto 201
Hotel Real Cabo Frio
Horário: 11:00 AM
```

### Backend Necessário
**Status Backend:** ✅ Completo — contrato de polling implementado com alias final, payload sonoro/visual e marcação como visto.

- [x] ✅ Endpoint `GET /checkout-alerts/pending`
- [x] ✅ Import de `NotificationService` corrigido no endpoint legado
- [ ] ❌ WebSocket `wss://api/checkout-alerts` (opcional, melhor UX)
- [x] ✅ `POST /checkout-alerts/{reservation_id}/viewed` marca alerta como visto

### Frontend Necessário
**Status Frontend:** ✅ Implementado em `(dashboard)/dashboard/page.js` — não usa o endpoint `/checkout-alerts/pending` mas implementa o mesmo comportamento filtrando reservas localmente.

- [x] ✅ Polling de 60s via `setInterval(refreshAll, 60000)`
- [x] ✅ Filtra reservas por `checkout_previsto >= 11:00 hoje` com deduplicação por assinatura
- [x] ✅ Som via Web Audio API (oscillator 880Hz) — sem arquivo mp3, gerado em runtime
- [x] ✅ Banner "Operação crítica" com cards por reserva (quarto, cliente, código, horário)
- [x] ✅ Botão "🔔 Ativar som" / "🔔 Som ativo" com persistência em localStorage
- [x] ✅ Browser Notification API ("Checkout pendente às 11:00")
- [ ] ❌ Botão "Marcar como Visto" por card individual (usa fluxo de status da reserva)

### Testes
- [x] ✅ Som toca em horário correto (>=11h, reservas hoje sem checkout)
- [x] ✅ Notificação visual aparece como banner vermelho
- [x] ✅ Pode silenciar manualmente (toggle somAtivado)

**Resultado testes:** ✅ 2/2 — `test_checkout_alerts_service.py`: cria notificação com payload sonoro/visual e marca como visto.

**Prioridade:** 🟡 MÉDIA | **Complexidade:** Baixa | **Est:** 1 dia

---

## 7️⃣ Invalidar Códigos Usados

### Descrição
Gerenciar ciclo de vida de códigos (cupom amigo, resgate de prêmio).

### Cenários

#### 7.1 Cupom Amigo Atingiu Max Uso
```
Cupom: AMIGO_ABC123 (máximo 5 usos)
Uso 1: João → cupom ainda ATIVO
Uso 2: Maria → cupom ainda ATIVO
...
Uso 5: Pedro → cupom passa para USED (ou MAXED)
Novo tentativa: "Cupom expirou" ❌
```

#### 7.2 Prêmio Resgatado
```
Cliente resgatou iPhone (90 pontos)
Código gerado: REAL-ABC123DEF
Status: ACTIVE (30 dias)

Passam 30 dias...
Status: EXPIRED ❌

Ou: Cliente solicita novo código do mesmo prêmio
Código antigo: REAL-ABC123DEF → CANCELLED
Código novo: REAL-XYZ789GHI → ACTIVE
```

### Backend Necessário
**Status Backend:** ✅ Completo — status explícito, validação, job/rotina administrativa e renovação de código de prêmio estão implementados e testados.

- [x] ✅ Model equivalente `Cupom` tem campo `status` com valores:
  - `active` → pode ser usado
  - `used` → atingiu max_uses (representado como `max_usage_reached`)
  - `expired` → venceu (expiresAt < now)
  - `cancelled` → cliente pediu novo código
  - `max_usage_reached` → sinônimo de `used`

- [x] ✅ Model equivalente `ResgatePremio` + `CodigoResgate` tem status:
  - `active` → código válido
  - `used` → cliente já resgatou (usedAt != null)
  - `expired` → passaram 30 dias
  - `cancelled` → cliente pediu novo código

- [x] ✅ Validação em endpoints:
  - Ao usar cupom: verifica `status == active` E `current_uses < max_uses`
  - Ao validar código: verifica `status == active` E `expiresAt > now`

- [x] ✅ Update automático:
  - ✅ Job `invalidar_codigos_vencidos_jornada()` varre vencidos e muda para `expired`
  - ✅ Ao atingir max_uses → muda para `max_usage_reached`
  - ✅ Código de resgate expirado é marcado ao validar/usar
  - ✅ `POST /api/v1/codigos/resgates/{resgate_id}/renovar` cancela o código ativo antigo e gera novo código ativo
  - ✅ `POST /api/v1/codigos/maintenance/invalidar-vencidos` executa a rotina administrativa protegida

### Frontend Necessário
**Status Frontend:** 🟡 Parcial — `resgate_dos_premios/page.js` já lê `codigo_status`/`status` da API, mostra "Código ativo" badge e exibe "válido até {data}". Falta tratar estado expirado/cancelado visualmente e botão de renovação. Cupom amigo (3/5 usos) ainda ausente.

- [ ] ❌ Cupom Amigo: mostrar "Status: Ativo | 3/5 usos"
- [ ] ❌ Se status = USED: mostrar "Cupom expirou, gere um novo"
- [x] 🟡 Resgate de prêmio: exibe "Código ativo" quando `status == active`, mostra data de validade
- [ ] ❌ Quando `status == expired/cancelled`: mostrar "Código expirado" + botão "Renovar código" (`POST /codigos/resgates/{id}/renovar`)

### Testes
```bash
# Cupom com max_uses=5
for i in 1..5; do
  POST /referrals/apply-to-reservation { code: "AMIGO_ABC" }
  # Iterações 1-4: success
  # Iteração 5: success + muda para status=USED
  # Iteração 6: 400 "Cupom atingiu limite de usos"
end

# Código de resgate com expiresAt=30 dias atrás
POST /rewards/validate-code { code: "REAL-ABC123" }
→ 400 "Código expirado"
```

**Prioridade:** 🔴 ALTA | **Complexidade:** Média | **Est:** 2 dias

---

## 8️⃣ Remover Suites Reservadas

### Descrição
Na página de reservas, suites já reservadas não aparecem como disponíveis.

### Exemplo
- Suite "Luxo Real" tem 3 quartos: 201, 202, 203
- Cliente 1 reservou: 201 (15/06 a 18/06)
- Cliente 2 reservou: 202 (16/06 a 20/06)
- Cliente 3 tenta reservar 16/06 a 18/06
  - Vê apenas: 203 (pois 201 e 202 estão ocupados nesse período)

### Backend Necessário
**Status Backend:** ✅ Completo — regra de disponibilidade existe, alias público `/availability` foi exposto e migration adiciona exclusion constraint para impedir sobreposição de reservas por quarto.

- [x] ✅ Endpoint exato `GET /availability?checkin=YYYY-MM-DD&checkout=YYYY-MM-DD`; também aceita ISO 8601 e filtro `suite_type`
- [x] ✅ Query de sobreposição existe no `DisponibilidadeService` e migration `016_reservas_exclusion_disponibilidade.sql` adiciona exclusion constraint
- [x] ✅ Retorna apenas quartos SEM reserva naquele período

### Frontend Necessário
**Status Frontend:** ✅ Implementado — `/reservar` chama `GET /public/quartos/disponiveis?data_checkin=...&data_checkout=...` com polling de 10s; mostra apenas quartos disponíveis para o período selecionado.

- [x] ✅ `/reservar` ao buscar disponibilidade chama `/public/quartos/disponiveis` com datas; mostra apenas quartos livres no período
- [x] ✅ Polling de disponibilidade em tempo real (10s interval enquanto na etapa de seleção)

### Testes
```bash
# Reserva 1: 201 (15-18 junho)
# Reserva 2: 202 (16-20 junho)

# Query: 16-18 junho
GET /availability?checkin=2026-06-16&checkout=2026-06-18
→ [ { room_id: "203", ... } ]  # 201 e 202 excluidos

# Query: 14-15 junho (antes de sobreposição)
GET /availability?checkin=2026-06-14&checkout=2026-06-15
→ [ { room_id: "201", ... }, { room_id: "202", ... }, { room_id: "203", ... } ]
```

**Prioridade:** 🔴 ALTA | **Complexidade:** Média | **Est:** 2 dias

---

## 9️⃣ Gerador de Cupons (Desconto & Influencers)

**Atualizacao 2026-07-04:** service/API/schema/model validados com `test_admin_coupons_service.py` (`3/3`). Frontend admin em `/(dashboard)/pontos-admin` foi reconectado ao contrato real `/admin/coupons`: lista via `GET /admin/coupons`, cria via `POST /admin/coupons/generate`, edita/desativa por codigo e envia campos de campanha influencer/comissao. Continua parcial porque ainda falta UX completa para exibir/copiar link rastreado, detalhes de usos, metricas de comissao e jornada visual dedicada.

### Descrição
Admin gera cupons de desconto com validade e rastreamento. Útil para:
- Promoções sazonais
- Influencers com link rastreado (saber quem trouxe clientes)

### Dois Tipos

#### 9.1 Cupom de Desconto
```
Código: VERAO2026
Desconto: 15%
Válido: 01/06 a 30/06
Uso máximo: 100 usos
Status: ATIVO
```

#### 9.2 Cupom Influencer
```
Código: INGRID_INFLUENCER
Desconto: 20% (ele ganha comissão)
Válido: 01/06 a 30/06
Link rastreado: https://hotel-real.com/reservar?cupom=INGRID_INFLUENCER
Clientes trazidos: 5
Comissão ganho: R$500
Status: ATIVO
```

### Backend Necessário
**Status Backend:** ✅ Completo — contrato admin `/admin/coupons/*` implementado com criação, listagem, detalhe, edição, desativação, link rastreado, uso por reserva/cliente e comissão estimada de influencer.

- [x] ✅ Model literal `DiscountCoupon` não existe; equivalente atual é `Cupom`:
  ```prisma
  model DiscountCoupon {
    id: String @id @uuid
    code: String @unique
    discountType: "PERCENTAGE" | "FIXED_AMOUNT"
    discountValue: Decimal (15 para 15%, ou 50 para R$50)
    maxUses: Int
    currentUses: Int
    validFrom: DateTime
    validUntil: DateTime
    generatedBy: String (admin_id)
    status: "ACTIVE" | "INACTIVE" | "EXPIRED" | "MAXED"
  }
  ```

- [x] ✅ Model `InfluencerCoupon extends DiscountCoupon` não existe; equivalente atual usa `tipoCampanha`, `trackingSlug`, `influencerNome` e `commissionPercentual` em `Cupom`:
  ```prisma
  influencerName: String
  influencerLink: String
  comissionPercentage: Decimal
  ```

- [x] ✅ Contrato admin final implementado:
  - `POST /admin/coupons/generate`
  - `GET /admin/coupons`
  - `GET /admin/coupons/{code}`
  - `PUT /admin/coupons/{code}`
  - `DELETE /admin/coupons/{code}` desativa o cupom

- [x] ✅ Endpoint público/equivalente:
  - Existe validação `POST /cupons/validar` e aplicação `POST /reservas/{reserva_id}/aplicar-cupom`
  - Reserva pública `POST /public/reservas` valida e aplica `cupom_codigo` durante a criação

- [x] ✅ Rastreamento:
  - ✅ Cada uso registra `CupomUso`
  - ✅ Dashboard admin retorna usos, clientes únicos, valor bruto, desconto, valor líquido e comissão estimada

### Frontend Necessário
**Status Frontend:** 🟡 Parcial — painel admin em `/(dashboard)/pontos-admin` esta conectado ao contrato novo `/admin/coupons/*` para listar, criar, editar e desativar por codigo. `/reservar` tambem valida e envia cupom. Ainda falta UX completa de link rastreado, metricas/detalhes de uso e copia/compartilhamento.

- [ ] Painel admin:
  - [x] ✅ Formulario "Criar Cupom" conectado a `/admin/coupons/generate`
  - [x] ✅ Tabela de cupons conectada a `GET /admin/coupons`
  - [x] ✅ Botao "Desativar cupom" aponta para `/admin/coupons/{code}`
  - [ ] Exibir/copiar link rastreado e abrir detalhes de usos/metricas

- [ ] Página pública:
  - [x] Campo "Cupom de desconto" na pagina de reserva
  - Ao validar cupom:
    ```javascript
    POST /reservations/validate-coupon { code: "VERAO2026" }
    → { valid: true, discount: "15%", newPrice: 425 }
    ```

### Testes
```bash
# Admin cria cupom
POST /admin/coupons/generate {
  code: "VERAO2026",
  discountValue: 15,
  discountType: "PERCENTAGE",
  validUntil: "2026-06-30"
}

# Cliente usa cupom na reserva
POST /reservations {
  checkin: "2026-06-15",
  checkout: "2026-06-18",
  room_id: "201",
  discount_coupon: "VERAO2026"
}
→ Desconto aplicado, reservation criada

# Admin consulta stats
GET /admin/coupons/VERAO2026
→ { currentUses: 1, ... }
```

**Prioridade:** 🟡 MÉDIA | **Complexidade:** Alta | **Est:** 4-5 dias

---

## 🔟 Confirmação Check-in Admin

### Descrição
Cliente deseja fazer check-in sem cartão (pagar em dinheiro). Admin recebe notificação WhatsApp para confirmar e liberar check-in manualmente.

### Fluxo
1. Cliente chega no hotel, não tem cartão
2. Admin gera "Check-in por Dinheiro" no sistema
3. Sistema gera **comprovante** (código + valor)
4. Admin recebe WhatsApp com foto do comprovante
5. Admin valida comprovante e clica "Liberar Check-in"
6. Cliente tem acesso ao quarto

### Backend Necessário
**Status Backend:** ✅ Completo — fluxo `CHK-*` criado com WhatsApp para admin, expiração de 30 minutos, aprovação protegida e código de uso único.

- [x] ✅ Endpoint `POST /checkins/request-cash-approval`
  ```json
  {
    "reservation_id": "res-123",
    "amount": 2500.00,
    "payment_method": "cash"
  }
  → {
    "approval_code": "CHK-ABC123XYZ",
    "qr_code": "data:image/png;base64,...",
    "expires_at": "2026-06-04T16:00:00Z"
  }
  ```

- [x] ✅ Enviar WhatsApp para admin:
  ```
  Confirmação de Check-in
  Reserva: RES-ABC123
  Cliente: João da Silva
  Quarto: 201
  Valor: R$2.500,00
  Código: CHK-ABC123XYZ
  
  [Foto do comprovante]
  
  👉 Confirmar: [LINK]
  ```

- [x] ✅ Endpoint admin `POST /checkins/{code}/approve`
  - Valida código ainda está válido
  - Registra/garante pagamento em dinheiro confirmado
  - Libera a reserva para o check-in existente (`CONFIRMADA`)

- [x] ✅ Segurança:
  - Código válido por 30 minutos
  - Após aprovação, código não pode ser usado novamente

### Frontend Necessário
- [x] ✅ Painel admin (dashboard de recepção):
  - ✅ Polling de aprovações CHK pendentes
  - ✅ Lista com cliente, quarto, valor e código
  - ✅ Botão "Aprovar Check-in"
  - ✅ Histórico de aprovações/expirações/cancelamentos
  - ✅ Solicitação de novo código CHK por reserva ativa

### WhatsApp Necessário
- [x] ✅ Bot admin recebe mensagem
- [x] ✅ Opção de clique para aprovar

### Testes
```bash
# Cliente solicita check-in por dinheiro
POST /checkins/request-cash-approval {
  reservation_id: "res-123",
  amount: 2500.00
}
→ { approval_code: "CHK-ABC123", qr_code: "..." }

# Admin aprova
POST /checkins/CHK-ABC123/approve
→ { approved: true, checkin_at: "2026-06-04T14:30:00Z" }

# Tentativa de usar código novamente
POST /checkins/CHK-ABC123/approve
→ 400 "Código já foi utilizado"
```

**Prioridade:** 🟡 MÉDIA | **Complexidade:** Média | **Est:** 2-3 dias

---

## 1️⃣1️⃣ Autenticar Cadastro

### Descrição
Ao fazer reserva via site da Jornada Real, cliente deve se autenticar (validar CPF) para evitar reservas fraudulentas com pessoas falsas.

### Fluxo
1. Cliente acessa `/reservar` da Jornada Real
2. Sistema pede: CPF ou E-mail
3. Se CPF: valida formato + consulta `GET /customers/{cpf}`
4. Se não existe: oferece "Criar cadastro agora"
5. Se existe: carrega dados (nome, email, telefone)
6. Cliente confirma dados
7. Envia SMS/WhatsApp com código 6 dígitos (OTP)
8. Cliente digita OTP
9. Se correto: libera reserva (customer_id já vinculado)

### Backend Necessário
**Status Backend:** ✅ Completo — consulta/criação pública de cliente, CPF com dígito verificador, OTP WhatsApp, expiração, tentativas, rate limit, auditoria, token de sessão e trava de reserva pública por token estão implementados.

- [x] ✅ Endpoint `GET /customers/{cpf}` com validação de CPF e existência
- [x] ✅ Endpoint `POST /customers/create` para novo cadastro público com validação antifraude existente
- [x] ✅ Endpoint `POST /auth/otp/generate` → gera OTP, persiste hash e envia via WhatsApp/Twilio
- [x] ✅ Endpoint `POST /auth/otp/validate` → valida OTP e retorna token com escopo `jornada_reserva`
- [x] ✅ Endpoint `POST /public/reservas` exige `customer_auth_token` válido e CPF correspondente

### Frontend Necessário
**Status Frontend:** ✅ Completo — `/reservar` consulta CPF, cria cadastro quando necessário, envia/valida OTP e bloqueia avanço sem token válido.

- [x] `/reservar` adiciona seção de autenticação no início do passo de dados:
  ```
  1. CPF: [INPUT CPF]
  2. Se existe: mostra dados pre-preenchidos
  3. Se não existe: formulário de cadastro
  4. Botão "Continuar"
  ↓
  5. OTP enviado para WhatsApp
  6. Código: [___] [___] [___] [___] [___] [___]
  7. Botão "Confirmar"
  ↓
  8. Acesso à reserva (customer já autenticado)
  ```

- [x] Validação:
  - CPF: formato correto (###.###.###-##)
  - CPF válido (algoritmo de validação)
  - OTP: 6 dígitos

### WhatsApp Necessário
- [x] ✅ Template:
  ```
  Seu código de verificação é: 123456
  Válido por 5 minutos.
  Não compartilhe com ninguém!
  ```

### Segurança
- [x] ✅ OTP válido por 5 minutos
- [x] ✅ Máximo 3 tentativas de OTP antes de solicitar novo
- [x] ✅ Rate limit: 1 OTP por minuto por CPF/telefone
- [x] ✅ Registrar todas as tentativas em `logs_jornada`
- [x] ✅ Reserva pública rejeita payload sem token, token expirado, escopo inválido ou CPF divergente

### Testes
```bash
# 1. Buscar CPF existente
GET /customers/11144477735
→ { name: "João", email: "joao@...", phone: "..." }

# 2. Buscar CPF inexistente
GET /customers/00000000000
→ 404 "Cliente não encontrado"

# 3. Gerar OTP
POST /auth/otp/generate { cpf: "11144477735" }
→ { otp_id: "otp-123", message: "OTP enviado via WhatsApp" }

# 4. Validar OTP correto
POST /auth/otp/validate { otp_id: "otp-123", code: "123456" }
→ { token: "jwt-token-here", customer_id: "..." }

# 5. Validar OTP incorreto
POST /auth/otp/validate { otp_id: "otp-123", code: "000000" }
→ 401 "Código inválido. 2 tentativas restantes"

# 6. Criar reserva sem token
POST /public/reservas { documento: "11144477735", customer_auth_token: null }
→ 401 "Autenticacao por WhatsApp obrigatoria antes de criar a reserva."

# Validação objetiva rodada
PYTHONPATH=$PWD pytest tests -q
→ 55 passed

cd frontend && npm run build
→ Compiled successfully
```

**Prioridade:** 🔴 ALTA | **Complexidade:** Média | **Est:** 2 dias

---

## 📅 Roadmap Recomendado

### Fase 1: MVP (Semana 1-2)
- [ ] 1️⃣ Cupom Amigo (backend ✅ testes ✅; `/reservar` ✅; falta tela "Meu Cupom" + WhatsApp direto/historico)
- [ ] 2️⃣ Benefícios Níveis (backend ✅; 🟡 parcial — nivel_jornada_real exibe bônus, falta badge em consultar-pontos e estimativa em reservar)
- [x] ✅ 3️⃣ Barras Progresso (backend + frontend + testes ✅)
- [x] ✅ 8️⃣ Remover Suites Reservadas (backend + frontend ✅)
- [ ] 7️⃣ Invalidar Códigos (backend ✅; 🟡 parcial — resgate mostra "Código ativo" mas falta "Expirado" + renovar)

**Saída:** Sistema de pontos e níveis funcional end-to-end

### Fase 2: Notificações (Semana 3)
- [x] ✅ 4️⃣ Aviso Prêmio Próximo (backend + WhatsApp ✅; sem frontend necessário)
- [x] ✅ 5️⃣ Msg Pós Check-out (backend + WhatsApp ✅; sem frontend necessário)
- [x] ✅ 6️⃣ Som Check-out (backend ✅ + frontend dashboard ✅ + testes ✅)
- [x] ✅ 🔟 Confirmação Check-in Admin (backend + frontend + WhatsApp + testes ✅)

**Saída:** Comunicação 360° com cliente e admin

### Fase 3: Autenticação & Cupons (Semana 4-5)
- [x] ✅ 1️⃣1️⃣ Autenticar Cadastro (backend + frontend `/reservar` + WhatsApp ✅)
- [ ] 9️⃣ Gerador Cupons (backend ✅; painel admin e campo de reserva ✅; falta UX de link rastreado/metricas/detalhes)

**Saída:** Sistema completo com segurança e promoções

---

## 🛠️ Checklist de Implementação

### Por Cada Funcionalidade

```markdown
- [ ] Especificação técnica (API, fields, validações)
- [ ] Mock/Stub dados no frontend
- [ ] Implementar backend
- [ ] Testes unitários backend
- [ ] Integrar frontend com API
- [ ] Testes E2E (fluxo completo)
- [ ] Testes manuais com dados reais
- [ ] Code review
- [ ] Deploy staging
- [ ] Testes QA
- [ ] Deploy produção
```

### Cross-Funcional

- [ ] Documentação de API (Swagger/OpenAPI)
- [ ] Documentação de WhatsApp (templates)
- [ ] Documentação de user flows
- [ ] Training para recepção (novo workflow)
- [ ] Monitoring & alertas pós-launch

---

## 📊 Timeline Estimada

```
Semana 1 (5d): Fases 1 iniciais
├─ D1-2: Backend + Frontend cupom amigo
├─ D2-3: Benefícios níveis
├─ D3-4: Barras progresso + Remover suites
└─ D5: Invalidar códigos

Semana 2 (5d): Fases 1 finais + 2 iniciais
├─ D1: Finalizar fase 1
├─ D2-4: Notificações (aviso, msg, som)
└─ D5: Check-in admin

Semana 3 (5d): Fase 2 final + 3 iniciais
├─ D1-3: Autenticar cadastro (CPF + OTP)
├─ D4-5: Gerador cupons
└─ D5: Testes E2E completos

Total: 15 dias úteis (3 semanas)
Buffer: +2 semanas para bugs, refinement, training

Produção estimada: 5-6 semanas
```

---

## ✅ Critérios de Sucesso

- [ ] Cada funcionalidade tem testes automatizados
- [ ] Zero falsos positivos em validações (CPF, cupom, código)
- [ ] Mensagens WhatsApp entregues em <10s
- [ ] Som alerta toca 100% das vezes
- [ ] Barras de progresso atualizadas em <5s após pontos creditados
- [ ] Zero cupons duplicados
- [ ] Zero reservas fraudulentas (graças à autenticação)
- [ ] Admin consegue gerir cupons em <2 minutos

---

## 📝 Notas

- Funcionalidades são independentes, podem ser feitas em paralelo
- WhatsApp é crítico para 4 funcionalidades (1, 4, 5, 10)
- Autenticação (11) é pré-requisito para evitar fraud antes que sistema escale
- Documentação deve acompanhar cada release para treinar equipe
