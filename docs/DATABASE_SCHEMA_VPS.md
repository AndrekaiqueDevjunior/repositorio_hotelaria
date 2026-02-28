# Documentação Oficial - Schema do Banco de Dados
## Hotel Real Cabo Frio - Ambiente Produção VPS

**Servidor:** 72.61.27.152  
**Database:** hotel_cabo_frio  
**SGDB:** PostgreSQL 16  
**Data:** 04/02/2026  
**Total de Tabelas:** 23

---

## Índice
1. [Visão Geral](#visão-geral)
2. [Tabelas Principais](#tabelas-principais)
3. [Relacionamentos](#relacionamentos)
4. [Índices e Performance](#índices-e-performance)
5. [Diferenças vs. Ambiente Local](#diferenças-vs-ambiente-local)
6. [Diagrama ER](#diagrama-er)

---

## Visão Geral

O banco de dados de produção do Hotel Real Cabo Frio contém **23 tabelas** que gerenciam todo o ciclo de vida de operações hoteleiras, incluindo:

- Gestão de clientes e reservas
- Sistema de pontos e fidelidade
- Processamento de pagamentos
- Controle de check-in/check-out
- Sistema de antifraude
- Auditoria completa
- Sistema de vouchers
- Gestão de tarifas dinâmicas

---

## Tabelas Principais

### 1. 🔐 **usuarios**
**Propósito:** Autenticação e controle de acesso do sistema

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('usuarios_id_seq') |
| nome | text | NOT NULL | - |
| email | text | NOT NULL | - |
| senha_hash | text | NOT NULL | - |
| perfil | text | NOT NULL | - |
| status | text | NOT NULL | 'ATIVO' |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NOT NULL | - |

---

### 2. 👥 **clientes**
**Propósito:** Cadastro completo de clientes do hotel

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('clientes_id_seq') |
| nomeCompleto | text | NOT NULL | - |
| documento | text | NOT NULL | - |
| telefone | text | NULL | - |
| email | text | NULL | - |
| dataNascimento | timestamp | NULL | - |
| nacionalidade | text | NULL | - |
| enderecoCompleto | text | NULL | - |
| cidade | text | NULL | - |
| estado | text | NULL | - |
| pais | text | NULL | - |
| observacoes | text | NULL | - |
| tipoHospede | text | NOT NULL | 'NORMAL' |
| nivelFidelidade | integer | NOT NULL | 0 |
| totalGasto | double precision | NOT NULL | 0 |
| totalReservas | integer | NOT NULL | 0 |
| ultimaVisita | timestamp | NULL | - |
| status | text | NOT NULL | 'ATIVO' |
| createdAt | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updatedAt | timestamp | NULL | - |

---

### 3. 🏨 **reservas**
**Propósito:** Gestão completa de reservas

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('reservas_id_seq') |
| codigo_reserva | text | NOT NULL | - |
| cliente_id | integer | NOT NULL, FK | - |
| status_reserva | text | NOT NULL | 'PENDENTE' |
| checkin_previsto | timestamp | NOT NULL | - |
| checkout_previsto | timestamp | NOT NULL | - |
| checkin_real | timestamp | NULL | - |
| checkout_real | timestamp | NULL | - |
| valor_diaria | numeric | NOT NULL | - |
| quarto_numero | text | NOT NULL | - |
| num_diarias | integer | NOT NULL | - |
| cliente_nome | text | NOT NULL | - |
| tipo_suite | text | NOT NULL | - |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |
| origem | text | NOT NULL | 'PARTICULAR' |
| responsavel_nome | text | NULL | - |
| quarto_id | integer | NOT NULL, FK | - |

---

### 4. 🛏️ **quartos**
**Propósito:** Controle de unidades habitacionais

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('quartos_id_seq') |
| numero | text | NOT NULL | - |
| tipo_suite | text | NOT NULL | - |
| status | text | NOT NULL | 'LIVRE' |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |

---

### 5. 💳 **pagamentos**
**Propósito:** Processamento financeiro

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('pagamentos_id_seq') |
| reserva_id | integer | NOT NULL, FK | - |
| cliente_id | integer | NOT NULL, FK | - |
| valor | numeric | NOT NULL | - |
| metodo | text | NOT NULL | - |
| parcelas | integer | NULL | - |
| cielo_payment_id | text | NULL | - |
| url_pagamento | text | NULL | - |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |
| cartao_token | varchar | NULL | - |
| dados_mascarados | boolean | NULL | true |
| idempotency_key | text | NULL | - |
| cartao_ultimos4 | varchar | NULL | - |
| cartao_bandeira | varchar | NULL | - |
| status_pagamento | text | NULL | 'PENDENTE' |

---

### 6. ⭐ **usuarios_pontos**
**Propósito:** Sistema de fidelidade

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('usuarios_pontos_id_seq') |
| cliente_id | integer | NOT NULL, FK | - |
| saldo | integer | NOT NULL | 0 |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |

---

### 7. 📊 **transacoes_pontos**
**Propósito:** Histórico de movimentação de pontos

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('transacoes_pontos_id_seq') |
| usuario_pontos_id | integer | NOT NULL, FK | - |
| tipo | text | NOT NULL | - |
| origem | text | NOT NULL | - |
| pontos | integer | NOT NULL | - |
| motivo | text | NULL | - |
| reserva_id | integer | NULL, FK | - |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |

---

### 8. 🎁 **premios**
**Propósito:** Catálogo de prêmios do sistema de fidelidade

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('premios_id_seq') |
| nome | text | NOT NULL | - |
| descricao | text | NULL | - |
| preco_em_pontos | integer | NOT NULL | - |
| preco_em_rp | integer | NOT NULL | 0 |
| categoria | text | NOT NULL | 'GERAL' |
| estoque | integer | NULL | - |
| imagem_url | text | NULL | - |
| ativo | boolean | NOT NULL | true |
| created_at | timestamptz | NOT NULL | now() |
| updated_at | timestamptz | NOT NULL | now() |

---

### 9. 🏠 **hospedagens**
**Propósito:** Controle operacional de hospedagens

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('hospedagens_id_seq') |
| reserva_id | integer | NOT NULL, FK | - |
| status_hospedagem | varchar | NULL | 'NAO_INICIADA' |
| checkin_realizado_em | timestamp | NULL | - |
| checkin_realizado_por | integer | NULL | - |
| checkout_realizado_em | timestamp | NULL | - |
| checkout_realizado_por | integer | NULL | - |
| num_hospedes | integer | NULL | - |
| num_criancas | integer | NULL | - |
| placa_veiculo | varchar | NULL | - |
| observacoes | text | NULL | - |
| created_at | timestamp | NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | CURRENT_TIMESTAMP |

---

### 10. 🎫 **vouchers**
**Propósito:** Emissão e controle de vouchers

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('vouchers_id_seq') |
| codigo | text | NOT NULL | - |
| reserva_id | integer | NOT NULL, FK | - |
| status | text | NOT NULL | 'EMITIDO' |
| data_emissao | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| emitido_por | integer | NULL | - |
| checkin_realizado_em | timestamp | NULL | - |
| checkin_realizado_por | integer | NULL | - |
| checkout_realizado_em | timestamp | NULL | - |
| checkout_realizado_por | integer | NULL | - |
| observacoes | text | NULL | - |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |

---

### 11. 🔍 **auditorias**
**Propósito:** Log completo de operações

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('auditorias_id_seq') |
| funcionario_id | integer | NOT NULL, FK | - |
| entidade | varchar | NOT NULL | - |
| entidade_id | varchar | NOT NULL | - |
| acao | varchar | NOT NULL | - |
| payload_resumo | text | NULL | - |
| ip_address | varchar | NULL | - |
| user_agent | varchar | NULL | - |
| created_at | timestamptz | NOT NULL | now() |
| updated_at | timestamptz | NOT NULL | now() |

---

### 12. 🔔 **notificacoes**
**Propósito:** Sistema de notificações internas

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('notificacoes_id_seq') |
| titulo | text | NOT NULL | - |
| mensagem | text | NOT NULL | - |
| tipo | text | NOT NULL | 'info' |
| categoria | text | NOT NULL | - |
| perfil | text | NULL | - |
| lida | boolean | NOT NULL | false |
| data_criacao | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| dataExpiracao | timestamp | NULL | - |
| urlAcao | text | NULL | - |
| pagamento_id | integer | NULL, FK | - |
| reserva_id | integer | NULL, FK | - |

---

### 13. 🛡️ **operacoes_antifraude**
**Propósito:** Sistema de prevenção a fraudes

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('operacoes_antifraude_id_seq') |
| pagamento_id | integer | NOT NULL, FK | - |
| cliente_id | integer | NOT NULL, FK | - |
| status | text | NOT NULL | 'PENDENTE' |
| risk_score | integer | NULL | - |
| fatores | text | NULL | - |
| analise_em | timestamp | NULL | - |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |

---

### 14. 📄 **comprovantes_pagamento**
**Propósito:** Validação de comprovantes

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('comprovantes_pagamento_id_seq') |
| pagamento_id | integer | NOT NULL, FK | - |
| tipo_comprovante | varchar | NOT NULL | - |
| nome_arquivo | varchar | NOT NULL | - |
| caminho_arquivo | varchar | NOT NULL | - |
| observacoes | text | NULL | - |
| valor_confirmado | numeric | NULL | - |
| status_validacao | varchar | NULL | 'EM_ANALISE' |
| data_upload | timestamp | NULL | CURRENT_TIMESTAMP |
| data_validacao | timestamp | NULL | - |
| validador_id | integer | NULL | - |
| motivo_recusa | text | NULL | - |
| observacoes_internas | text | NULL | - |
| created_at | timestamp | NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | CURRENT_TIMESTAMP |

---

### 15. 💌 **convites**
**Propósito:** Sistema de convites para indicações

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('convites_id_seq') |
| codigo | text | NOT NULL | - |
| convidante_id | integer | NOT NULL, FK | - |
| usos_maximos | integer | NOT NULL | 5 |
| usos_restantes | integer | NOT NULL | 5 |
| ativo | boolean | NOT NULL | true |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| expires_at | timestamp | NULL | - |

---

### 16. ✅ **convite_usos**
**Propósito:** Controle de utilização de convites

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('convite_usos_id_seq') |
| convite_id | integer | NOT NULL, FK | - |
| convidado_id | integer | NOT NULL, FK | - |
| pontos_ganhos | integer | NOT NULL | - |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |

---

### 17. 👤 **funcionarios**
**Propósito:** Gestão de equipe interna

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('funcionarios_id_seq') |
| nome | text | NOT NULL | - |
| email | text | NOT NULL | - |
| senha | text | NOT NULL | - |
| perfil | text | NOT NULL | 'FUNCIONARIO' |
| status | text | NOT NULL | 'ATIVO' |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |
| foto_url | text | NULL | - |
| primeiro_acesso | boolean | NULL | - |

---

### 18. 📈 **historico_pontos**
**Propósito:** Histórico detalhado de pontos

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('historico_pontos_id_seq') |
| cliente_id | integer | NOT NULL, FK | - |
| usuario_pontos_id | integer | NULL, FK | - |
| tipo | text | NOT NULL | - |
| pontos | integer | NOT NULL | - |
| origem | text | NOT NULL | - |
| motivo | text | NULL | - |
| data | timestamp | NOT NULL | - |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |

---

### 19. 📋 **pontos_regras**
**Propósito:** Regras de cálculo de pontos

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('pontos_regras_id_seq') |
| suite_tipo | text | NOT NULL | - |
| diarias_base | integer | NOT NULL | - |
| rp_por_base | integer | NOT NULL | - |
| temporada | text | NULL | - |
| data_inicio | date | NOT NULL | - |
| data_fim | date | NOT NULL | - |
| ativo | boolean | NOT NULL | true |
| created_at | timestamp | NOT NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | - |

---

### 20. 🎯 **resgates_premios**
**Propósito:** Controle de resgates de prêmios

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('resgates_premios_id_seq') |
| cliente_id | integer | NOT NULL, FK | - |
| premio_id | integer | NOT NULL, FK | - |
| pontos_usados | integer | NOT NULL | - |
| status | text | NOT NULL | 'PENDENTE' |
| funcionario_id | integer | NULL, FK | - |
| funcionario_entrega_id | integer | NULL, FK | - |
| created_at | timestamptz | NOT NULL | now() |
| updated_at | timestamptz | NOT NULL | now() |

---

### 21. 💰 **tarifas**
**Propósito:** Gestão de tarifas básicas

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('tarifas_id_seq') |
| nome | varchar | NOT NULL | - |
| valor_diaria | numeric | NOT NULL | - |
| suite_tipo | varchar | NOT NULL | - |
| data_inicio | date | NOT NULL | - |
| data_fim | date | NOT NULL | - |
| status | varchar | NULL | 'ATIVA' |
| created_at | timestamp | NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | CURRENT_TIMESTAMP |

---

### 22. 🏷️ **tarifas_suites**
**Propósito:** Tarifas dinâmicas por suite

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | nextval('tarifas_suites_id_seq') |
| nome | varchar | NOT NULL | - |
| suite_tipo | varchar | NOT NULL | - |
| valor_diaria | numeric | NOT NULL | - |
| data_inicio | date | NOT NULL | - |
| data_fim | date | NOT NULL | - |
| status | varchar | NULL | 'ATIVA' |
| created_at | timestamp | NULL | CURRENT_TIMESTAMP |
| updated_at | timestamp | NULL | CURRENT_TIMESTAMP |
| temporada | varchar | NULL | 'ALTA' |
| descricao | text | NULL | - |
| min_noites | integer | NULL | 1 |
| max_noites | integer | NULL | 30 |
| taxa_cancelamento | numeric | NULL | 10.00 |
| preco_diaria | numeric | NULL | - |
| preco_semana | numeric | NULL | - |
| preco_fim_semana | numeric | NULL | - |
| preco_promocional | numeric | NULL | - |
| ativo | boolean | NULL | true |
| ordem | integer | NULL | 0 |
| cor_hex | varchar | NULL | '#000000' |
| icone | varchar | NULL | 'default' |
| destaque | boolean | NULL | false |

---

### 23. 🔧 **_prisma_migrations**
**Propósito:** Controle de migrações do Prisma ORM

| Coluna | Tipo | Restrições | Default |
|--------|------|------------|---------|
| id | integer | PK, Auto-increment | - |
| checksum | varchar | NOT NULL | - |
| finished_at | timestamp | NULL | - |
| migration_name | varchar | NOT NULL | - |
| logs | text | NULL | - |
| rolled_back_at | timestamp | NULL | - |
| started_at | timestamp | NOT NULL | - |
| applied_steps_count | integer | NOT NULL | - |

---

## Relacionamentos

### Relacionamentos Principais

```
clientes (1:N) reservas
clientes (1:1) usuarios_pontos
clientes (1:N) historico_pontos
clientes (1:N) resgates_premios

reservas (1:N) pagamentos
reservas (1:N) hospedagens
reservas (1:N) vouchers
reservas (1:N) transacoes_pontos

usuarios_pontos (1:N) transacoes_pontos

quartos (1:N) reservas

funcionarios (1:N) auditorias
funcionarios (1:N) resgates_premios

pagamentos (1:N) comprovantes_pagamento
pagamentos (1:N) operacoes_antifraude

convites (1:N) convite_usos

premios (1:N) resgates_premios
```

### Chaves Estrangeiras Principais

- **reservas.cliente_id** → **clientes.id**
- **reservas.quarto_id** → **quartos.id**
- **pagamentos.reserva_id** → **reservas.id**
- **pagamentos.cliente_id** → **clientes.id**
- **usuarios_pontos.cliente_id** → **clientes.id**
- **transacoes_pontos.usuario_pontos_id** → **usuarios_pontos.id**
- **hospedagens.reserva_id** → **reservas.id**
- **vouchers.reserva_id** → **reservas.id**

---

## Índices e Performance

### Índices Automáticos (Primary Keys)
Todas as tabelas possuem índices automáticos nas colunas de chave primária.

### Índices Recomendados (Baseado na Análise)
```sql
-- Performance para consultas frequentes
CREATE INDEX IF NOT EXISTS idx_reservas_cliente_id ON reservas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_reservas_status ON reservas(status_reserva);
CREATE INDEX IF NOT EXISTS idx_reservas_checkin ON reservas(checkin_previsto);
CREATE INDEX IF NOT EXISTS idx_pagamentos_reserva_id ON pagamentos(reserva_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_pontos_cliente_id ON usuarios_pontos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_usuario_id ON transacoes_pontos(usuario_pontos_id);
CREATE INDEX IF NOT EXISTS idx_quartos_status ON quartos(status);
CREATE INDEX IF NOT EXISTS idx_clientes_documento ON clientes(documento);
CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes(status);
```

---

## Diferenças vs. Ambiente Local

### 🔴 Diferenças Críticas

| Tabela | VPS | Local | Impacto |
|--------|-----|-------|---------|
| **clientes** | camelCase (nomeCompleto) | snake_case (nome_completo) | **Alto** - Incompatibilidade de código |
| **usuarios_pontos** | campo "saldo" | campos "saldo_atual" e "rp_points" | **Alto** - Sistema de pontos diferente |
| **Funcionários** | Tabela separada | Integrado em "usuarios" | **Médio** - Lógica de autenticação |
| **Pontos** | "historico_pontos" adicional | Não existe | **Médio** - Auditoria de pontos |
| **Tarifas** | 2 tabelas completas | Não implementado | **Baixo** - Funcionalidade extra |

### 🟡 Diferenças Funcionais

| Funcionalidade | VPS | Local | Status |
|----------------|-----|-------|---------|
| Sistema de Convites | ✅ Completo | ❌ Não existe | Novo na VPS |
| Validação de Comprovantes | ✅ Completo | ❌ Não existe | Novo na VPS |
| Tarifas Dinâmicas | ✅ Completo | ❌ Não existe | Novo na VPS |
| Antifraude | ✅ Simplificado | ✅ Completo | Diferente |
| Check-in/Checkout | ✅ Simplificado | ✅ Completo | Diferente |

---

## Diagrama ER (Resumo)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   clientes  │────│  reservas   │────│  quartos    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│usuarios_pts │────│transacoes   │    │ pagamentos  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│historico_pt │    │hospedagens  │    │comprovantes │
└─────────────┘    └─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  premios    │────│resgates_pr  │    │  vouchers   │
└─────────────┘    └─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│funcionarios │────│ auditorias  │    │ notificacoes│
└─────────────┘    └─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐
│  convites   │────│convite_usos │
└─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐
│   tarifas   │    │tarifas_suit │
└─────────────┘    └─────────────┘
```

---

## 📋 Checklist de Manutenção

### ✅ Verificações Diárias
- [ ] Backup automático executado
- [ ] Espaço em disco > 20%
- [ ] Logs de erro verificados
- [ ] Performance das consultas

### ✅ Verificações Semanais
- [ ] Índices fragmentados
- [ ] Estatísticas do PostgreSQL
- [ ] Tabelas com crescimento anormal
- [ ] Integridade dos dados

### ✅ Verificações Mensais
- [ ] Plano de manutenção
- [ ] Atualizações de segurança
- [ ] Otimização de queries
- [ ] Limpeza de logs antigos

---

## 🚨 Alertas Críticos

### ⚠️ Incompatibilidades Código vs. Produção

1. **clientes.nomeCompleto** vs **clientes.nome_completo**
2. **usuarios_pontos.saldo** vs **usuarios_pontos.saldo_atual**
3. **Sistema de funcionários separado**
4. **Sistema de pontos com RP points**

### 🔧 Ações Necessárias

1. **IMEDIATA:** Alinhar modelos locais com VPS
2. **CURTO PRAZO:** Implementar migração segura
3. **MÉDIO PRAZO:** Unificar sistemas de autenticação
4. **LONGO PRAZO:** Padronizar nomenclatura

---

## 📞 Contatos e Suporte

- **Banco de Dados:** PostgreSQL 16
- **Acesso:** Via Docker Container
- **Backup:** Diário automático
- **Monitoramento:** 24/7

---

**Documento Gerado:** 04/02/2026  
**Versão:** 1.0  
**Próxima Revisão:** 04/03/2026  
**Responsável:** Sistema de Documentação Automática
