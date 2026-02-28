# BACKLOG PRIORIZADO E PLANO DE TESTES

**Projeto**: Hotel Real Cabo Frio - Roadmap de Melhorias  
**Data**: 03/01/2026  
**Baseline**: Análise arquitetural completa realizada

---

## 📋 BACKLOG PRIORIZADO

### 🔴 P0 - CRÍTICO (Bloqueadores Legais/Operacionais)

#### BUG-001: Check-in/Checkout Desabilitados Após Pagamento
**Esforço**: 8h | **Risco**: Baixo | **Impacto**: CRÍTICO

**Descrição**: Botões de check-in ficam desabilitados após pagamento devido a lógica incorreta no frontend que não valida status CONFIRMADA nem pagamento aprovado.

**Solução**:
1. Atualizar lógica de habilitação dos botões (frontend)
2. Adicionar validação de pagamento no check-in (backend)
3. Incluir `pagamentos` no endpoint `/reservas`
4. Testes E2E do fluxo completo

**Arquivos afetados**:
- `frontend/app/(dashboard)/reservas/page.js` (linhas 1303-1344)
- `backend/app/services/reserva_service.py` (método `checkin`)
- `backend/app/repositories/reserva_repo.py` (include pagamentos)

**DoD**:
- [ ] Botão check-in habilitado somente se status=CONFIRMADA E pagamento aprovado
- [ ] Botão check-out habilitado somente se status=HOSPEDADO
- [ ] Backend valida pagamento antes de check-in
- [ ] Testes E2E passam

---

#### LEGAL-001: Implementar FNRH (Ficha Nacional de Registro de Hóspedes)
**Esforço**: 40h | **Risco**: Médio | **Impacto**: BLOQUEANTE LEGAL

**Descrição**: Obrigação legal (Lei 11.771/2008) - coletar dados de hóspedes e enviar à Polícia Federal.

**Solução**:
1. Criar modelo `FichaHospede` com campos obrigatórios
2. Formulário de coleta no check-in
3. Integração API SINCS (Polícia Federal) OU livro físico
4. Validação de documento (CPF/RG)

**Dados obrigatórios**:
- Nome completo, CPF/RG, órgão emissor
- Nacionalidade, data nascimento
- Endereço completo
- Profissão, motivo viagem, destino seguinte

**DoD**:
- [ ] Modelo criado e migrado
- [ ] Formulário check-in coleta todos os dados
- [ ] Validação de CPF/RG implementada
- [ ] Envio para SINCS OU armazenamento conforme
- [ ] Auditoria registrada

---

#### LEGAL-002: Emissão de Nota Fiscal Eletrônica (NF-e)
**Esforço**: 60h | **Risco**: Alto | **Impacto**: BLOQUEANTE FISCAL

**Descrição**: Obrigação fiscal - emitir NF-e para todos os serviços prestados.

**Solução**:
1. Integrar com API SEFAZ OU serviço terceiro (NFE.io, Bling, Tiny)
2. Gerar NF-e automaticamente no check-out
3. Armazenar XML e PDF
4. Enviar por email ao cliente

**DoD**:
- [ ] Integração com serviço de NF-e
- [ ] NF-e gerada automaticamente no checkout
- [ ] XML e PDF armazenados
- [ ] Email enviado ao cliente
- [ ] Dashboard de NF-e emitidas

---

#### DATA-001: Consolidar Status de Reserva (Remover Duplicação)
**Esforço**: 12h | **Risco**: Médio | **Impacto**: ALTO

**Descrição**: Schema possui `status` e `status_reserva` causando inconsistências.

**Solução**:
1. Migration para remover `status_reserva`
2. Migrar dados para `status` único
3. Atualizar todos os usos no código
4. Validar enum de estados

**DoD**:
- [ ] Migration criada e testada
- [ ] Todos os registros migrados
- [ ] Código atualizado (grep search completo)
- [ ] Testes de regressão passam

---

#### PAY-001: Implementar Pré-autorização de Cartão
**Esforço**: 24h | **Risco**: Médio | **Impacto**: ALTO

**Descrição**: Garantir reserva sem capturar dinheiro imediatamente (prática universal).

**Solução**:
1. Usar endpoint Cielo de pré-autorização (não captura)
2. Armazenar ID da autorização
3. Capturar no check-in
4. Ajustar valor no check-out (consumos)
5. Liberar saldo não usado

**Fluxo**:
```
Reserva → Pré-autoriza R$ 500
Check-in → Captura R$ 500
Check-out → Total R$ 580 (consumos)
          → Captura adicional R$ 80
          → Fecha transação
```

**DoD**:
- [ ] Endpoint de pré-autorização integrado
- [ ] Captura no check-in
- [ ] Ajuste no check-out
- [ ] Testes com cartão sandbox

---

### 🟠 P1 - IMPORTANTE (Operação Hoteleira)

#### OPS-001: Implementar No-Show
**Esforço**: 16h | **Risco**: Baixo | **Impacto**: MÉDIO

**Descrição**: Gerenciar clientes que não comparecem.

**Solução**:
1. Job diário: verificar reservas com checkin_previsto + 24h passado
2. Se status != HOSPEDADO, marcar como NO_SHOW
3. Cobrar taxa (capturar pré-autorização)
4. Liberar quarto
5. Registrar em antifraude

**DoD**:
- [ ] Status NO_SHOW adicionado ao enum
- [ ] Job diário implementado
- [ ] Cobrança de taxa automática
- [ ] Dashboard de no-shows

---

#### OPS-002: Sistema de Housekeeping
**Esforço**: 40h | **Risco**: Médio | **Impacto**: ALTO

**Descrição**: Gestão de limpeza de quartos (essencial para operação).

**Solução**:
1. Criar modelo `TarefaLimpeza`
2. Estados: SUJO, EM_LIMPEZA, LIMPO, INSPECIONADO
3. Interface para camareiras
4. Dashboard para governança
5. Integrar com status de quarto

**DoD**:
- [ ] Modelo criado
- [ ] Workflow de limpeza implementado
- [ ] Interface camareiras (mobile-friendly)
- [ ] Dashboard governança
- [ ] Integração com disponibilidade de quartos

---

#### OPS-003: Early Check-in / Late Check-out
**Esforço**: 16h | **Risco**: Baixo | **Impacto**: MÉDIO

**Descrição**: Permitir check-in antecipado e check-out tardio (com taxa).

**Solução**:
1. Configurações globais: horário padrão check-in (15h) e check-out (12h)
2. Opção de solicitar early/late (frontend)
3. Calcular taxa adicional
4. Validar disponibilidade do quarto
5. Benefício automático por nível de fidelidade

**DoD**:
- [ ] Configurações de horários
- [ ] Interface de solicitação
- [ ] Cálculo de taxa
- [ ] Validação de disponibilidade
- [ ] Integração com níveis de fidelidade

---

#### PAY-002: Estorno de Pagamentos
**Esforço**: 20h | **Risco**: Médio | **Impacto**: MÉDIO

**Descrição**: Permitir estorno em cancelamentos.

**Solução**:
1. Endpoint Cielo de estorno (total/parcial)
2. Lógica de estorno baseada em política de cancelamento
3. Registrar transação de estorno
4. Atualizar status do pagamento
5. Notificar cliente

**DoD**:
- [ ] Integração com Cielo estorno
- [ ] Política de cancelamento configurável
- [ ] UI de solicitação de estorno
- [ ] Auditoria de estornos
- [ ] Email de confirmação

---

#### OPS-004: Walk-in (Reserva sem Agendamento)
**Esforço**: 12h | **Risco**: Baixo | **Impacto**: MÉDIO

**Descrição**: Permitir check-in direto sem reserva prévia.

**Solução**:
1. Criar reserva + cliente + pagamento em fluxo único
2. Verificar disponibilidade imediata
3. Check-in instantâneo
4. Interface simplificada para recepção

**DoD**:
- [ ] Fluxo walk-in implementado
- [ ] UI simplificada
- [ ] Validação de disponibilidade
- [ ] Testes E2E

---

### 🟡 P2 - DESEJÁVEL (Melhorias)

#### FIDEL-001: Sistema de Níveis (Bronze → Diamante)
**Esforço**: 16h | **Risco**: Baixo | **Impacto**: MÉDIO

**Descrição**: Implementar programa de fidelidade com 4 níveis.

**Solução**: Ver `PROPOSTA_MELHORIAS_PONTOS_ANTIFRAUDE.md`

**DoD**:
- [ ] Modelo de níveis criado
- [ ] Cálculo anual implementado
- [ ] Multiplicadores de pontos
- [ ] Benefícios por nível
- [ ] UI de exibição de nível

---

#### FIDEL-002: Resgate de Pontos
**Esforço**: 20h | **Risco**: Baixo | **Impacto**: MÉDIO

**Descrição**: Permitir uso de pontos para descontos e upgrades.

**Solução**: Ver `PROPOSTA_MELHORIAS_PONTOS_ANTIFRAUDE.md`

**DoD**:
- [ ] Catálogo de resgates
- [ ] Endpoint de resgate
- [ ] Integração com reservas
- [ ] UI de catálogo
- [ ] Testes E2E

---

#### FIDEL-003: Expiração de Pontos
**Esforço**: 8h | **Risco**: Baixo | **Impacto**: BAIXO

**Descrição**: Pontos expiram em 12 meses (reduzir passivo).

**Solução**: Ver `PROPOSTA_MELHORIAS_PONTOS_ANTIFRAUDE.md`

**DoD**:
- [ ] Campo data_expiracao
- [ ] Job de expiração diária
- [ ] Notificações pré-expiração
- [ ] Testes automatizados

---

#### FRAUD-001: Validações Básicas (CPF, Email, Telefone)
**Esforço**: 16h | **Risco**: Baixo | **Impacto**: ALTO

**Descrição**: Validar dados básicos para reduzir fraude.

**Solução**: Ver `PROPOSTA_MELHORIAS_PONTOS_ANTIFRAUDE.md`

**DoD**:
- [ ] Validador de CPF (algoritmo + Receita)
- [ ] Validador de email (formato + MX)
- [ ] Validador de telefone (formato + DDD)
- [ ] Integração em criação de cliente

---

#### FRAUD-002: Análise Técnica (IP, Device)
**Esforço**: 24h | **Risco**: Médio | **Impacto**: MÉDIO

**Descrição**: Detectar VPN, proxy, dispositivos suspeitos.

**Solução**: Ver `PROPOSTA_MELHORIAS_PONTOS_ANTIFRAUDE.md`

**DoD**:
- [ ] Integração IP Quality Score
- [ ] Device fingerprinting (frontend)
- [ ] Análise de risco automática
- [ ] Dashboard de análises

---

#### FRAUD-003: Integração Bureau de Crédito
**Esforço**: 32h | **Risco**: Alto | **Impacto**: MÉDIO

**Descrição**: Consultar Serasa/SPC para validar clientes.

**Solução**: Ver `PROPOSTA_MELHORIAS_PONTOS_ANTIFRAUDE.md`

**DoD**:
- [ ] Integração Serasa API
- [ ] Consulta automática em reservas
- [ ] Score integrado ao antifraude
- [ ] Testes com sandbox

---

#### FEAT-001: Channel Manager (OTAs)
**Esforço**: 80h | **Risco**: Alto | **Impacto**: ALTO

**Descrição**: Integrar com Booking, Airbnb, Expedia.

**Solução**:
1. Integrar API OTAs
2. Sincronização de disponibilidade
3. Importação de reservas
4. Gestão de tarifas
5. Calendar unificado

**DoD**:
- [ ] Integração com 3 OTAs
- [ ] Sincronização bidirecional
- [ ] Dashboard unificado
- [ ] Testes de integração

---

#### REPORT-001: Relatórios Gerenciais
**Esforço**: 40h | **Risco**: Baixo | **Impacto**: MÉDIO

**Descrição**: Dashboards e relatórios para gestão.

**Relatórios**:
- Ocupação por período
- Revenue por tipo de suíte
- ADR (Average Daily Rate)
- RevPAR (Revenue Per Available Room)
- Taxa de no-show
- Top clientes
- Performance de canais

**DoD**:
- [ ] 7 relatórios implementados
- [ ] Filtros por data, tipo, canal
- [ ] Exportação PDF/Excel
- [ ] Gráficos interativos

---

## 📊 RESUMO DO BACKLOG

```
┌──────────────────────────────────────────────────────┐
│         RESUMO POR PRIORIDADE                        │
├──────────────────────────────────────────────────────┤
│ P0 - CRÍTICO      │ 5 itens  │ 144h │ 18 dias       │
│ P1 - IMPORTANTE   │ 5 itens  │ 124h │ 15 dias       │
│ P2 - DESEJÁVEL    │ 8 itens  │ 236h │ 30 dias       │
├──────────────────────────────────────────────────────┤
│ TOTAL             │ 18 itens │ 504h │ 63 dias úteis │
└──────────────────────────────────────────────────────┘
```

**Com equipe de 2 devs**: ~32 dias (~6 semanas)  
**Com equipe de 1 dev**: ~63 dias (~3 meses)

---

## 🧪 PLANO DE TESTES

### Estratégia de Testes

```
┌─────────────────────────────────────────────────────┐
│              PIRÂMIDE DE TESTES                     │
├─────────────────────────────────────────────────────┤
│ E2E (10%)           │ Cypress, Playwright           │
│ Integração (30%)    │ Pytest + TestClient           │
│ Unitários (60%)     │ Pytest + Jest                 │
└─────────────────────────────────────────────────────┘
```

---

### SUITE 1: Testes de Correção do Bug Check-in/Checkout

**Objetivo**: Validar correção do BUG-001

#### TC-BUG-001: Fluxo Completo Feliz
```gherkin
Given uma nova reserva é criada
And o pagamento é processado e aprovado
When o frontend carrega a lista de reservas
Then o botão "Check-in" deve estar HABILITADO
And o botão "Check-out" deve estar DESABILITADO
And o tooltip deve mostrar "Check-in disponível"

When o usuário clica em "Check-in"
And preenche os dados de hospedagem
And confirma o check-in
Then a reserva deve ter status "HOSPEDADO"
And o botão "Check-in" deve estar DESABILITADO
And o botão "Check-out" deve estar HABILITADO

When o usuário clica em "Check-out"
And preenche consumos e avaliação
And confirma o check-out
Then a reserva deve ter status "CHECKED_OUT"
And ambos os botões devem estar DESABILITADOS
And pontos devem ter sido creditados
```

#### TC-BUG-002: Tentativa Check-in Sem Pagamento
```gherkin
Given uma reserva com status "PENDENTE"
And nenhum pagamento foi processado
When o frontend carrega a lista de reservas
Then o botão "Check-in" deve estar DESABILITADO
And o tooltip deve mostrar "Aguardando pagamento"

When o usuário tenta chamar a API de check-in diretamente
Then deve retornar erro 400
And a mensagem deve ser "Check-in requer pagamento aprovado"
And o status da reserva deve continuar "PENDENTE"
```

#### TC-BUG-003: Tentativa Check-out Sem Check-in
```gherkin
Given uma reserva com status "CONFIRMADA"
And o pagamento foi aprovado
When o frontend carrega a lista de reservas
Then o botão "Check-out" deve estar DESABILITADO
And o tooltip deve mostrar "Check-in necessário antes do check-out"

When o usuário tenta chamar a API de check-out diretamente
Then deve retornar erro 400
And a mensagem deve ser "Check-out requer check-in"
```

#### TC-BUG-004: Múltiplos Pagamentos Parciais
```gherkin
Given uma reserva de R$ 1000
And um pagamento de R$ 500 foi aprovado
When o frontend carrega a lista de reservas
Then o botão "Check-in" deve estar HABILITADO (pagamento parcial aprovado)

Given um segundo pagamento de R$ 500 é processado e aprovado
When o check-in é realizado
Then deve ter sucesso
And a reserva deve ter 2 pagamentos associados
```

---

### SUITE 2: Testes de Fluxo de Reserva

#### TC-RES-001: Criar Reserva via Agenda Pública
```python
async def test_criar_reserva_agenda_publica():
    # 1. Selecionar datas disponíveis
    response = await client.get(
        "/quartos/disponiveis/periodo",
        params={
            "checkin": "2026-02-01T15:00:00Z",
            "checkout": "2026-02-05T12:00:00Z",
            "tipo_suite": "LUXO"
        }
    )
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # 2. Criar cliente + reserva
    payload = {
        "cliente": {
            "nome_completo": "João Silva",
            "email": "joao@example.com",
            "cpf": "12345678901",
            "telefone": "11987654321"
        },
        "reserva": {
            "quarto_numero": response.json()[0]["numero"],
            "tipo_suite": "LUXO",
            "checkin_previsto": "2026-02-01T15:00:00Z",
            "checkout_previsto": "2026-02-05T12:00:00Z",
            "valor_diaria": 200.00,
            "num_diarias": 4
        }
    }
    
    response = await client.post("/reservas", json=payload)
    assert response.status_code == 201
    reserva = response.json()
    assert reserva["status"] == "PENDENTE"
    assert "codigo_reserva" in reserva
    
    # 3. Processar pagamento
    pag_payload = {
        "reserva_id": reserva["id"],
        "metodo": "credit_card",
        "valor": 800.00,
        "cartao_numero": "4111111111111111",  # Sandbox
        "cartao_validade": "12/28",
        "cartao_cvv": "123",
        "cartao_nome": "JOAO SILVA"
    }
    
    response = await client.post("/pagamentos", json=pag_payload)
    assert response.status_code == 201
    pagamento = response.json()
    assert pagamento["status"] == "APROVADO"
    
    # 4. Verificar reserva confirmada
    response = await client.get(f"/reservas/{reserva['id']}")
    assert response.json()["status"] == "CONFIRMADA"
    
    # 5. Verificar voucher gerado
    assert response.json()["voucher"] is not None
```

---

### SUITE 3: Testes de Antifraude

#### TC-FRAUD-001: Cliente Suspeito (Alta Taxa Cancelamento)
```python
async def test_antifraude_alta_taxa_cancelamento():
    # Criar cliente
    cliente = await criar_cliente_teste()
    
    # Criar 10 reservas e cancelar 8
    for i in range(10):
        reserva = await criar_reserva_teste(cliente.id)
        if i < 8:
            await cancelar_reserva(reserva.id)
    
    # Analisar cliente
    response = await client.get(f"/antifraude/analisar/cliente/{cliente.id}")
    assert response.status_code == 200
    
    analise = response.json()
    assert analise["nivel_risco"] in ["MEDIO", "ALTO"]
    assert "TAXA_CANCELAMENTO" in str(analise["regras_ativadas"])
    assert analise["score_risco"] >= 25
```

#### TC-FRAUD-002: Validação de Voucher Inválido
```python
async def test_validar_voucher_invalido():
    # Tentar validar código inexistente
    response = await client.get("/public/reservas/CODIGOFAKE123")
    assert response.status_code == 404
    
    # Verificar que operação antifraude foi registrada
    ops = await db.operacao_antifraude.find_many(
        where={"tipo_analise": "VALIDACAO_VOUCHER_FALHOU"}
    )
    assert len(ops) > 0
```

---

### SUITE 4: Testes de Pontos e Fidelidade

#### TC-POINTS-001: Acúmulo de Pontos no Checkout
```python
async def test_acumulo_pontos_checkout():
    # Criar reserva de R$ 1000
    cliente, reserva = await criar_reserva_paga(valor_total=1000.00)
    
    # Fazer check-in
    await realizar_checkin(reserva.id)
    
    # Verificar que ainda não creditou pontos
    saldo_antes = await get_saldo_pontos(cliente.id)
    
    # Fazer check-out
    await realizar_checkout(reserva.id)
    
    # Verificar crédito de pontos
    saldo_depois = await get_saldo_pontos(cliente.id)
    
    # R$ 1000 / 10 = 100 pontos
    assert saldo_depois.pontos_atuais == saldo_antes.pontos_atuais + 100
    
    # Verificar transação registrada
    historico = await get_historico_pontos(cliente.id)
    assert len(historico) == 1
    assert historico[0]["tipo"] == "CREDITO"
    assert historico[0]["origem"] == "CHECKOUT"
```

#### TC-POINTS-002: Sistema de Convites
```python
async def test_sistema_convites():
    # Cliente A gera convite
    cliente_a = await criar_cliente_teste()
    convite = await gerar_convite(cliente_a.id)
    
    assert len(convite["codigo"]) == 8
    assert convite["usos_restantes"] == 5
    
    # Cliente B usa convite
    cliente_b = await criar_cliente_teste()
    resultado = await usar_convite(convite["codigo"], cliente_b.id)
    
    assert resultado["success"] == True
    
    # Verificar bônus
    saldo_a = await get_saldo_pontos(cliente_a.id)
    saldo_b = await get_saldo_pontos(cliente_b.id)
    
    assert saldo_a.pontos_atuais == 50  # Indicador
    assert saldo_b.pontos_atuais == 30  # Indicado
    
    # Verificar usos restantes
    convite_atualizado = await get_convite(convite["codigo"])
    assert convite_atualizado["usos_restantes"] == 4
```

---

### SUITE 5: Testes de Integração Cielo

#### TC-PAY-001: Pagamento Cartão de Crédito
```python
async def test_pagamento_cartao_credito():
    reserva = await criar_reserva_teste()
    
    payload = {
        "reserva_id": reserva.id,
        "metodo": "credit_card",
        "valor": reserva.valor_total,
        "parcelas": 3,
        "cartao_numero": "4111111111111111",
        "cartao_validade": "12/28",
        "cartao_cvv": "123",
        "cartao_nome": "TESTE"
    }
    
    response = await client.post("/pagamentos", json=payload)
    assert response.status_code == 201
    
    pagamento = response.json()
    assert pagamento["status"] == "APROVADO"
    assert pagamento["payment_id"] is not None
    assert pagamento["cielo_transaction_id"] is not None
    
    # Verificar que reserva foi confirmada
    reserva_atualizada = await db.reserva.find_unique(where={"id": reserva.id})
    assert reserva_atualizada.status == "CONFIRMADA"
    
    # Verificar que voucher foi gerado
    voucher = await db.voucher.find_first(where={"reserva_id": reserva.id})
    assert voucher is not None
```

#### TC-PAY-002: Pagamento PIX
```python
async def test_pagamento_pix():
    reserva = await criar_reserva_teste()
    
    payload = {
        "reserva_id": reserva.id,
        "metodo": "pix",
        "valor": reserva.valor_total
    }
    
    response = await client.post("/pagamentos", json=payload)
    assert response.status_code == 201
    
    pagamento = response.json()
    assert pagamento["status"] == "AGUARDANDO"
    assert pagamento["cielo_qrcode"] is not None
    
    # Simular confirmação de pagamento (sandbox)
    response = await client.post(
        f"/pagamentos/{pagamento['payment_id']}/confirmar-pix"
    )
    assert response.status_code == 200
    
    # Verificar status atualizado
    pag_atualizado = await db.pagamento.find_unique(where={"id": pagamento["id"]})
    assert pag_atualizado.status == "APROVADO"
```

---

### SUITE 6: Testes de Performance

#### TC-PERF-001: Consulta de Disponibilidade
```python
async def test_performance_disponibilidade():
    # Criar 100 quartos
    for i in range(100):
        await db.quarto.create({
            "numero": f"{i+1}",
            "tipo_suite": random.choice(["LUXO", "MASTER", "REAL"]),
            "status": "LIVRE"
        })
    
    # Medir tempo de consulta
    start = time.time()
    
    response = await client.get(
        "/quartos/disponiveis/periodo",
        params={
            "checkin": "2026-02-01T15:00:00Z",
            "checkout": "2026-02-05T12:00:00Z"
        }
    )
    
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.5  # Deve responder em menos de 500ms
```

#### TC-PERF-002: Listagem de Reservas com Paginação
```python
async def test_performance_listagem_reservas():
    # Criar 1000 reservas
    for i in range(1000):
        await criar_reserva_teste()
    
    # Medir tempo de consulta paginada
    start = time.time()
    
    response = await client.get("/reservas?limit=20&offset=0")
    
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert len(response.json()["reservas"]) == 20
    assert response.json()["total"] == 1000
    assert elapsed < 0.3  # Deve responder em menos de 300ms
```

---

## ✅ CRITÉRIOS DE ACEITAÇÃO GLOBAIS

### Para TODOS os itens do backlog:

1. **Código**:
   - [ ] Code review aprovado por 2 pessoas
   - [ ] Cobertura de testes >= 80%
   - [ ] Sem warnings de linter
   - [ ] Documentação atualizada (README, API docs)

2. **Testes**:
   - [ ] Testes unitários passam (100%)
   - [ ] Testes de integração passam (100%)
   - [ ] Testes E2E passam (smoke tests mínimo)
   - [ ] Testes de regressão passam

3. **Performance**:
   - [ ] Endpoints respondem em < 500ms (p95)
   - [ ] Queries de banco otimizadas (EXPLAIN ANALYZE)
   - [ ] Cache implementado onde aplicável

4. **Segurança**:
   - [ ] Validação de inputs
   - [ ] Proteção contra SQL injection
   - [ ] Sanitização de outputs
   - [ ] HTTPS obrigatório
   - [ ] CORS configurado corretamente

5. **Observabilidade**:
   - [ ] Logs estruturados
   - [ ] Métricas de negócio
   - [ ] Alertas configurados
   - [ ] Rastreamento de erros (Sentry/similar)

6. **Deployment**:
   - [ ] Migrations rodadas com sucesso
   - [ ] Rollback plan documentado
   - [ ] Feature flags (se aplicável)
   - [ ] Smoke tests em staging passam

---

**FIM DO BACKLOG E PLANO DE TESTES**
