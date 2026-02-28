# TAXONOMIA COMPLETA - Sistema Hotel Real Cabo Frio

**Data**: 03/01/2026  
**Consultor**: Arquitetura de Software e Operações Hoteleiras  
**Status**: Mapeamento Completo Backend + Frontend

---

## 📚 ÍNDICE

1. [DOMÍNIOS E BOUNDED CONTEXTS](#dominios)
2. [ENTIDADES E AGREGADOS](#entidades)
3. [ESTADOS E TRANSIÇÕES](#estados)
4. [EVENTOS DE DOMÍNIO](#eventos)
5. [COMANDOS](#comandos)
6. [REGRAS DE NEGÓCIO](#regras)
7. [FLUXOS OPERACIONAIS](#fluxos)
8. [INTEGRAÇÕES EXTERNAS](#integracoes)

---

## 🏗️ DOMÍNIOS E BOUNDED CONTEXTS {#dominios}

### 1. GESTÃO DE RESERVAS
**Responsabilidade**: Ciclo de vida completo da reserva (criação → finalização)

**Entidades**:
- `Reserva` (agregado raiz)
- `Hospedagem`
- `Voucher`

**Serviços**:
- `reserva_service.py`
- `voucher_service.py`

**APIs**:
- `/api/v1/reservas`
- `/api/v1/public/reservas/{codigo}` (validação antifraude)

---

### 2. GESTÃO DE CLIENTES
**Responsabilidade**: Cadastro, histórico e segmentação de clientes

**Entidades**:
- `Cliente` (agregado raiz)
- `Usuario` (relação 1:1)
- `UsuarioPontos`

**Serviços**:
- `cliente_service.py` (não encontrado - provavelmente inline nos repos)

**APIs**:
- `/api/v1/clientes`

---

### 3. PAGAMENTOS E FATURAMENTO
**Responsabilidade**: Processamento financeiro, integração gateway

**Entidades**:
- `Pagamento` (agregado raiz)
- `Reserva` (referência)

**Serviços**:
- `pagamento_service.py`
- Integração Cielo (cartão + PIX)

**APIs**:
- `/api/v1/pagamentos`
- `/api/v1/pagamentos/webhook` (callback Cielo)

**Estados**:
- `PENDENTE` → `AGUARDANDO` → `APROVADO`/`RECUSADO` → `CANCELADO`

---

### 4. PROGRAMA DE FIDELIDADE
**Responsabilidade**: Pontos, resgates, convites de indicação

**Entidades**:
- `UsuarioPontos` (agregado raiz)
- `TransacaoPontos`
- `HistoricoPontos`
- `Convite`
- `ConviteUso`

**Serviços**:
- `pontos_service.py`

**APIs**:
- `/api/v1/pontos/saldo/{cliente_id}`
- `/api/v1/pontos/historico/{cliente_id}`
- `/api/v1/pontos/convites/gerar`
- `/api/v1/pontos/convites/usar`

**Regras**:
- 1 ponto = R$ 10,00 gastos
- Convite indicação: 50 pontos (indicador) + 30 pontos (indicado)
- Pontos creditados apenas no checkout

---

### 5. ANTIFRAUDE E SEGURANÇA
**Responsabilidade**: Detecção de padrões suspeitos, alertas

**Entidades**:
- `OperacaoAntifraude` (agregado raiz)
- `Cliente` (análise comportamental)

**Serviços**:
- `antifraude_service.py`

**APIs**:
- `/api/v1/antifraude/analisar/cliente/{id}`
- `/api/v1/antifraude/transacoes-suspeitas`
- `/api/v1/antifraude/estatisticas`

**Regras Implementadas**:
- Score baseado em regras (sem ML)
- Alertas: reservas múltiplas, alta taxa cancelamento, pagamentos recusados
- Níveis: BAIXO, MÉDIO, ALTO

---

### 6. INVENTÁRIO DE QUARTOS
**Responsabilidade**: Disponibilidade, manutenção, histórico

**Entidades**:
- `Quarto` (agregado raiz)

**Serviços**:
- `quarto_service.py` (provavelmente inline)

**APIs**:
- `/api/v1/quartos`
- `/api/v1/quartos/disponiveis/periodo`
- `/api/v1/quartos/{numero}/historico`

**Estados**:
- `LIVRE`, `OCUPADO`, `MANUTENCAO`, `RESERVADO`

---

### 7. COMUNICAÇÕES
**Responsabilidade**: Notificações ao cliente/staff

**Entidades**:
- `Notificacao`

**APIs**:
- `/api/v1/notificacoes` (presumido)

---

### 8. GESTÃO DE USUÁRIOS E AUTENTICAÇÃO
**Responsabilidade**: Login, roles, permissões

**Entidades**:
- `Usuario` (agregado raiz)
- `Funcionario`

**Perfis**:
- `ADMIN`, `RECEPCAO`, `GERENCIA`, `CLIENTE`

**APIs**:
- `/api/v1/auth/login`
- `/api/v1/usuarios`

---

## 📦 ENTIDADES E AGREGADOS {#entidades}

### Agregado: RESERVA

```
Reserva (raiz)
├── id: int
├── codigo_reserva: string (único, gerado)
├── cliente_id → Cliente
├── quarto_numero → Quarto
├── tipo_suite: enum (LUXO, MASTER, REAL)
├── checkin_previsto: datetime
├── checkout_previsto: datetime
├── checkinReal: datetime?
├── checkoutReal: datetime?
├── num_diarias: int
├── valor_diaria: decimal
├── valor_total: decimal
├── status: enum ⚠️ DUPLICADO
├── status_reserva: enum ⚠️ DUPLICADO
├── pagamentos: Pagamento[]
├── hospedagem: Hospedagem?
├── voucher: Voucher?
└── created_at, updated_at
```

**Status Válidos**:
- `PENDENTE` - Criada, sem pagamento
- `CONFIRMADA` - Pagamento aprovado
- `HOSPEDADO` - Check-in realizado
- `CHECKED_OUT` - Check-out realizado
- `CANCELADO` - Cancelada

**Eventos**:
- `ReservaCriada`
- `ReservaConfirmada` (pós-pagamento)
- `CheckinRealizado`
- `CheckoutRealizado`
- `ReservaCancelada`

---

### Agregado: PAGAMENTO

```
Pagamento (raiz)
├── id: int
├── reserva_id → Reserva
├── payment_id: string (Cielo)
├── metodo: enum (credit_card, debit_card, pix, boleto)
├── valor: decimal
├── parcelas: int
├── status: enum
├── cielo_transaction_id: string?
├── cielo_qrcode: string? (PIX)
├── cielo_payload: json
├── erro_msg: string?
└── created_at, updated_at
```

**Status Válidos**:
- `PENDENTE`
- `AGUARDANDO` (PIX gerado)
- `APROVADO` / `PAGO` / `CONFIRMADO` / `CAPTURED` / `AUTHORIZED`
- `RECUSADO` / `NEGADO`
- `CANCELADO`

---

### Agregado: HOSPEDAGEM

```
Hospedagem
├── id: int
├── reserva_id → Reserva (1:1)
├── num_hospedes: int
├── num_criancas: int
├── placa_veiculo: string?
├── observacoes: text?
├── consumo_frigobar: decimal
├── servicos_extras: decimal
├── avaliacao: int (1-5)
├── comentario_avaliacao: text?
├── statusHospedagem: enum
└── created_at, updated_at
```

**Status**:
- `NAO_INICIADA`
- `EM_ANDAMENTO`
- `FINALIZADA`

---

### Agregado: PONTOS

```
UsuarioPontos (raiz)
├── id: int
├── cliente_id → Cliente (1:1)
├── pontos_atuais: int
├── pontos_acumulados_total: int
└── updated_at

TransacaoPontos
├── id: int
├── cliente_id → Cliente
├── reserva_id → Reserva?
├── tipo: enum (CREDITO, DEBITO)
├── valor: int
├── origem: enum (CHECKOUT, CONVITE, RESGATE, AJUSTE)
├── descricao: string
├── processado: bool
├── created_at

HistoricoPontos
├── id: int
├── cliente_id → Cliente
├── pontos_antes: int
├── pontos_depois: int
├── operacao: string
├── created_at
```

---

### Agregado: CONVITE (Indicação)

```
Convite
├── id: int
├── codigo: string (único, 8 chars)
├── cliente_id → Cliente (quem gerou)
├── pontos_indicador: int (default 50)
├── pontos_indicado: int (default 30)
├── usos_restantes: int (default 5)
├── data_expiracao: datetime
├── ativo: bool
└── created_at

ConviteUso
├── id: int
├── convite_id → Convite
├── cliente_id → Cliente (quem usou)
└── used_at
```

---

### Agregado: ANTIFRAUDE

```
OperacaoAntifraude
├── id: int
├── cliente_id → Cliente
├── reserva_id → Reserva?
├── tipo_analise: string
├── score_risco: decimal
├── nivel_risco: enum (BAIXO, MEDIO, ALTO)
├── regras_ativadas: json
├── alertas: json[]
├── recomendacao: string
└── created_at
```

**Regras Implementadas**:
1. Reservas recentes (> 3 em 30 dias)
2. Taxa de cancelamento alta (> 30%)
3. Pagamentos recusados consecutivos (> 2)
4. Reservas consecutivas canceladas (> 2)
5. Reserva longa demais (> 30 dias)
6. Valor muito alto (> R$ 10.000)

---

## 🔄 ESTADOS E TRANSIÇÕES {#estados}

### Máquina de Estados: RESERVA

```
┌─────────────────────────────────────────────────────────┐
│                   CICLO DE VIDA RESERVA                 │
└─────────────────────────────────────────────────────────┘

[CRIAÇÃO]
    ↓
PENDENTE ──────────────────────────────────────→ CANCELADO
    │                                                  ↑
    │ pagamento aprovado                              │
    ↓                                                  │
CONFIRMADA ────────────────────────────────────────────┤
    │                                                  │
    │ check-in                                         │
    ↓                                                  │
HOSPEDADO ─────────────────────────────────────────────┤
    │                                                  
    │ check-out
    ↓
CHECKED_OUT [FINAL]
```

**Transições Permitidas**:
- `PENDENTE` → `CONFIRMADA` (via pagamento)
- `PENDENTE` → `CANCELADO` (via API)
- `CONFIRMADA` → `HOSPEDADO` (via check-in)
- `CONFIRMADA` → `CANCELADO` (via API)
- `HOSPEDADO` → `CHECKED_OUT` (via check-out)
- `HOSPEDADO` → `CANCELADO` (via API) ⚠️ QUESTIONÁVEL

**Transições PROIBIDAS** (não validadas no código):
- `CHECKED_OUT` → qualquer (imutável)
- `CANCELADO` → qualquer (imutável)

---

### Máquina de Estados: PAGAMENTO

```
PENDENTE ──→ AGUARDANDO ──→ APROVADO [FINAL]
              (PIX)          ↓
                             └─→ CAPTURED/AUTHORIZED

PENDENTE ──→ RECUSADO [FINAL]

APROVADO ──→ CANCELADO (estorno)
```

---

### Máquina de Estados: HOSPEDAGEM

```
NAO_INICIADA ──→ EM_ANDAMENTO ──→ FINALIZADA
  (criada)       (check-in)        (check-out)
```

---

## 🎯 EVENTOS DE DOMÍNIO {#eventos}

### Reserva
- `ReservaCriada` - Nova reserva no sistema
- `ReservaConfirmada` - Pagamento aprovado
- `ReservaCancelada` - Cancelamento solicitado
- `CheckinRealizado` - Hóspede chegou
- `CheckoutRealizado` - Hóspede saiu
- `VoucherGerado` - Código de confirmação criado

### Pagamento
- `PagamentoIniciado`
- `PagamentoAprovado` → **Gatilho**: confirmar reserva + gerar voucher
- `PagamentoRecusado`
- `PagamentoCancelado`

### Pontos
- `PontosCreditados`
- `PontosDebitados`
- `ConviteGerado`
- `ConviteUsado`

### Antifraude
- `AlertaFraudeGerado`
- `ClienteBloqueado` (não implementado)

---

## ⚙️ COMANDOS {#comandos}

### Reserva
- `CriarReserva(cliente_id, quarto, datas, valor)`
- `ConfirmarReserva(reserva_id)` - Após pagamento
- `RealizarCheckin(reserva_id, dados_hospedagem)`
- `RealizarCheckout(reserva_id, consumos)`
- `CancelarReserva(reserva_id, motivo?)`

### Pagamento
- `ProcessarPagamento(reserva_id, metodo, dados_cartao?)`
- `ConfirmarPagamentoPix(payment_id)` - Manual sandbox
- `CancelarPagamento(payment_id)`

### Pontos
- `CreditarPontos(cliente_id, valor, origem)`
- `DebitarPontos(cliente_id, valor, motivo)`
- `GerarConvite(cliente_id)`
- `UsarConvite(codigo, cliente_id)`

---

## 📜 REGRAS DE NEGÓCIO {#regras}

### RN-001: Cálculo de Diárias
```python
num_diarias = ceil((checkout - checkin).days)
valor_total = num_diarias * valor_diaria
```

### RN-002: Check-in Permitido
```
CONDIÇÕES:
1. reserva.status == "CONFIRMADA"
2. EXISTS pagamento WHERE status IN ("APROVADO", "PAGO", "CONFIRMADO")
3. data_atual >= (checkin_previsto - 1 dia)
4. quarto.status == "LIVRE"
```

### RN-003: Check-out Permitido
```
CONDIÇÕES:
1. reserva.status == "HOSPEDADO"
2. EXISTS hospedagem WHERE statusHospedagem == "EM_ANDAMENTO"
```

### RN-004: Geração de Voucher
```
GATILHO: Pagamento.status = "APROVADO"
AÇÃO:
1. Gerar código único (8 chars alfanumérico)
2. Criar Voucher(reserva_id, codigo, validade=checkin+7dias)
3. Enviar notificação ao cliente (não implementado)
```

### RN-005: Crédito de Pontos
```
GATILHO: Checkout realizado
FÓRMULA: pontos = floor(valor_total / 10)
CONDIÇÕES:
1. Pagamento aprovado
2. Checkout confirmado
3. Cliente não bloqueado
```

### RN-006: Antifraude - Score de Risco
```
BAIXO (0-30):    Aprovar automaticamente
MÉDIO (31-60):   Revisar manualmente
ALTO (61-100):   Bloquear / alertar gerência

PENALIDADES:
- Reservas recentes (>3): +20
- Taxa cancelamento alta: +25
- Pagamentos recusados: +30
- Cancelamentos consecutivos: +35
```

### RN-007: Disponibilidade de Quartos
```
Quarto disponível SE:
1. quarto.status == "LIVRE"
2. NÃO EXISTS Reserva WHERE:
   - quarto_numero = X
   - status IN ("CONFIRMADA", "HOSPEDADO")
   - (checkin_previsto <= nova_checkout) AND (checkout_previsto >= nova_checkin)
```

---

## 🔀 FLUXOS OPERACIONAIS {#fluxos}

### FLUXO 1: Reserva Pública (Cliente)

```
1. Cliente acessa /reservar
2. Seleciona datas + tipo de suíte
3. Sistema verifica quartos disponíveis
4. Cliente preenche dados pessoais
5. Sistema cria Usuario + Cliente + Reserva (status=PENDENTE)
6. Sistema redireciona para pagamento
7. Cliente escolhe método (Cartão/PIX)
8. Sistema chama Cielo API
9. SE aprovado:
   - Reserva.status = CONFIRMADA
   - Gera Voucher
   - Envia email (não implementado)
10. Cliente recebe código de reserva
```

### FLUXO 2: Check-in (Recepção)

```
1. Hóspede chega ao hotel
2. Recepcionista valida código voucher
3. Sistema verifica:
   - Pagamento aprovado?
   - Reserva CONFIRMADA?
   - Data dentro do permitido?
4. Recepcionista preenche:
   - Num hóspedes/crianças
   - Placa veículo
   - Observações
5. Sistema executa check-in:
   - Reserva.status = HOSPEDADO
   - Reserva.checkinReal = now()
   - Hospedagem.statusHospedagem = EM_ANDAMENTO
   - Quarto.status = OCUPADO
6. Entrega chaves ao hóspede
```

### FLUXO 3: Check-out (Recepção)

```
1. Hóspede solicita check-out
2. Recepcionista abre modal check-out
3. Preenche:
   - Consumo frigobar
   - Serviços extras
   - Avaliação (1-5 estrelas)
   - Comentários
4. Sistema calcula saldo devedor:
   saldo = valor_total - SUM(pagamentos.valor) + consumo + extras
5. SE saldo > 0:
   - Solicitar pagamento adicional
6. Sistema executa check-out:
   - Reserva.status = CHECKED_OUT
   - Reserva.checkoutReal = now()
   - Hospedagem.statusHospedagem = FINALIZADA
   - Quarto.status = LIVRE
   - Credita pontos: floor(valor_total / 10)
7. Agradecer e liberar hóspede
```

### FLUXO 4: Cancelamento

```
1. Cliente/Recepcionista solicita cancelamento
2. Sistema verifica status:
   - SE PENDENTE: cancelar imediatamente
   - SE CONFIRMADA: verificar política de cancelamento (não implementada)
   - SE HOSPEDADO: alertar (incomum)
3. Sistema atualiza:
   - Reserva.status = CANCELADO
   - Libera quarto
4. SE pagamento foi feito:
   - Iniciar processo de estorno (não implementado)
5. Registra em OperacaoAntifraude
```

---

## 🔌 INTEGRAÇÕES EXTERNAS {#integracoes}

### 1. Cielo (Pagamentos)
**Tipo**: REST API  
**Ambiente**: Sandbox (teste)  
**Métodos**:
- `POST /sales` - Criar transação (cartão/PIX)
- `PUT /sales/{id}/capture` - Capturar autorização
- `GET /sales/{id}` - Consultar status
- Webhook (não configurado)

**Credenciais**: `CIELO_MERCHANT_ID`, `CIELO_MERCHANT_KEY`

### 2. Ngrok (Exposição)
**Tipo**: Tunnel HTTP  
**Uso**: Expor frontend/backend publicamente

### 3. Redis (Cache)
**Uso**:
- Locks distribuídos (idempotência)
- Cache de sessões

### 4. PostgreSQL (Persistência)
**Versão**: 15  
**ORM**: Prisma

---

## ⚠️ GAPS IDENTIFICADOS

### Críticos
1. **Duplicação de status** (`status` vs `status_reserva`)
2. **Validação de pagamento no check-in** (frontend não verifica)
3. **Webhooks Cielo não configurados** (polling manual)
4. **Política de cancelamento** (não implementada)
5. **Estorno de pagamento** (não implementado)

### Importantes
6. **Notificações ao cliente** (email/SMS não enviados)
7. **Auditoria completa** (logs insuficientes)
8. **Multi-tenancy** (não suportado)
9. **Histórico de alterações** (não rastreado)
10. **Bloqueio de cliente fraudulento** (apenas alerta)

### Desejáveis
11. **Channel Manager** (não integrado)
12. **Housekeeping** (limpeza de quartos)
13. **Relatórios gerenciais** (básicos apenas)
14. **Integrações OTA** (Booking, Airbnb)

---

**FIM DA TAXONOMIA**
