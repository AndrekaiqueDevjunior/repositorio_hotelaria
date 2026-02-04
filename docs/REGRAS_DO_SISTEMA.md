# REGRAS DE NEGÓCIO DO SISTEMA - HOTEL REAL CABO FRIO

**Versão:** 2.0  
**Data:** 07/01/2026  
**Sistema:** Real Points - Gestão Hoteleira  

---

## ÍNDICE

1. [Regras de Reservas](#1-regras-de-reservas)
2. [Regras de Check-in](#2-regras-de-check-in)
3. [Regras de Check-out](#3-regras-de-check-out)
4. [Regras de Pagamentos](#4-regras-de-pagamentos)
5. [Regras de Pontos de Fidelidade](#5-regras-de-pontos-de-fidelidade)
6. [Regras de Antifraude](#6-regras-de-antifraude)
7. [Regras de Clientes](#7-regras-de-clientes)
8. [Regras de Quartos](#8-regras-de-quartos)
9. [Regras de Cancelamento e Estorno](#9-regras-de-cancelamento-e-estorno)
10. [Transições de Status](#10-transições-de-status)
11. [Regras de Autorização e Perfis](#11-regras-de-autorização-e-perfis)

---

## 1. REGRAS DE RESERVAS

### 1.1 Criação de Reserva

**RN-RES-001: Validação de Datas**
- Check-in **NÃO pode ser no passado**
- Check-out deve ser **posterior ao check-in**
- Duração máxima: **30 dias**
- Duração mínima: **1 dia**

**RN-RES-002: Disponibilidade de Quarto**
- Sistema verifica conflitos de período antes de criar reserva
- Conflito ocorre quando há overlap de datas com reservas ativas (PENDENTE, CONFIRMADA, HOSPEDADO)
- Algoritmo de detecção:
  ```
  checkin_novo <= checkout_existente AND checkout_novo >= checkin_existente
  ```

**RN-RES-003: Dados Obrigatórios**
- Cliente ID (válido no sistema)
- Número do quarto
- Tipo de suíte
- Datas de check-in e check-out
- Valor da diária
- Número de diárias
- Nome do cliente (cache para performance)

**RN-RES-004: Status Inicial**
- Toda reserva criada inicia com status **PENDENTE**
- Aguarda pagamento para confirmação

**RN-RES-005: Código de Reserva Único**
- Gerado automaticamente no formato: `RES-YYYYMMDD-XXXXX`
- Exemplo: `RES-20260107-00123`
- Único no sistema (chave de busca rápida)

---

## 2. REGRAS DE CHECK-IN

### 2.1 Pré-requisitos para Check-in

**RN-CHK-001: Status da Reserva**
- Reserva deve estar com status **CONFIRMADA**
- **Não permite check-in** em status:
  - PENDENTE (sem pagamento)
  - HOSPEDADO (já está no hotel)
  - CHECKED_OUT (já finalizou)
  - CANCELADO (reserva cancelada)

**RN-CHK-002: Pagamento Aprovado (REGRA CRÍTICA)**
- Deve existir **pelo menos 1 pagamento aprovado** para a reserva
- Status de pagamento aceitos:
  - APROVADO
  - CONFIRMADO
  - PAGO
  - CAPTURED
  - AUTHORIZED

**RN-CHK-003: Disponibilidade do Quarto**
- Quarto deve estar com status **LIVRE**
- Sistema valida em tempo real antes do check-in
- Previne race conditions com lock Redis

**RN-CHK-004: Janela de Check-in**
- Permitido check-in **1 dia antes** da data prevista
- Permitido check-in **1 dia depois** da data prevista
- Fora dessa janela: sistema bloqueia

**RN-CHK-005: Horário Padrão de Check-in**
- Horário padrão: **15:00** (3 PM)
- Flexível mediante disponibilidade

### 2.2 Processo de Check-in

**RN-CHK-006: Atualização de Status**
- Reserva: CONFIRMADA → **HOSPEDADO**
- Quarto: LIVRE → **OCUPADO**
- Ambos os campos `status` e `status_reserva` são atualizados (correção de bug)

**RN-CHK-007: Registro de Data/Hora**
- Campo `checkin_real` recebe timestamp UTC do momento do check-in
- Diferente de `checkin_previsto` (data planejada)

**RN-CHK-008: Geração de Voucher**
- Sistema gera voucher de confirmação após check-in
- Código único no formato: `VHCK-XXXXX`
- Válido para acesso ao hotel

---

## 3. REGRAS DE CHECK-OUT

### 3.1 Pré-requisitos para Check-out

**RN-CHO-001: Status da Reserva**
- Reserva deve estar com status **HOSPEDADO**
- Não permite check-out em outros status

**RN-CHO-002: Saldo Devedor (REGRA CRÍTICA)**
- **Cliente NÃO pode sair com dívidas**
- Sistema calcula:
  - Valor total da reserva = `valor_diaria × num_diarias`
  - Valor pago = soma de pagamentos APROVADOS/CONFIRMADOS
  - Saldo devedor = valor total - valor pago
- Se `saldo_devedor > R$ 0,01`: **CHECK-OUT BLOQUEADO**
- Tolerância de 1 centavo para arredondamento

**RN-CHO-003: Pagamentos Pendentes**
- Todos os pagamentos devem estar quitados
- Verifica pagamentos extras (consumo, taxas adicionais)

### 3.2 Processo de Check-out

**RN-CHO-004: Atualização de Status**
- Reserva: HOSPEDADO → **CHECKED_OUT**
- Quarto: OCUPADO → **LIVRE**
- Ambos os campos `status` e `status_reserva` são atualizados

**RN-CHO-005: Registro de Data/Hora**
- Campo `checkout_real` recebe timestamp UTC do momento do check-out
- Diferente de `checkout_previsto` (data planejada)

**RN-CHO-006: Horário Padrão de Check-out**
- Horário padrão: **12:00** (meio-dia)
- Flexível mediante disponibilidade

**RN-CHO-007: Crédito Automático de Pontos**
- Sistema credita pontos automaticamente após check-out
- **Regra:** 1 ponto para cada R$ 10,00 gastos
- Processo idempotente (não duplica se executado duas vezes)

---

## 4. REGRAS DE PAGAMENTOS

### 4.1 Criação de Pagamento

**RN-PAG-001: Valor Mínimo e Máximo**
- Valor mínimo: **R$ 0,01**
- Valor máximo: **R$ 100.000,00** por transação
- Valores fora desse range são rejeitados

**RN-PAG-002: Métodos de Pagamento Aceitos**
- DINHEIRO
- DEBITO
- CREDITO
- PIX
- TRANSFERENCIA
- CIELO_CARTAO (integração gateway)
- OUTRO

**RN-PAG-003: Idempotência (REGRA CRÍTICA)**
- Cada pagamento deve ter `idempotency_key` único
- Chave baseada em: `reserva_id + timestamp_fixo`
- Previne pagamentos duplicados em caso de timeout/retry
- Sistema rejeita tentativas com mesma chave

**RN-PAG-004: Validação de Reserva**
- Não permite pagamento para reservas:
  - **CANCELADAS** (já foi cancelada)
  - **CHECKED_OUT** (já finalizou)
- Reserva deve existir e estar ativa

**RN-PAG-005: Dados do Cartão**
- Para CREDITO/DEBITO:
  - Número do cartão (armazenado mascarado)
  - Validade (formato MM/AA)
  - CVV (não armazenado - apenas enviado ao gateway)
  - Nome do titular
- Sistema máscara dados sensíveis após processamento

### 4.2 Processamento de Pagamento

**RN-PAG-006: Análise Anti-fraude Obrigatória**
- Todo pagamento passa por análise de risco
- Score < 30: Aprovação automática
- Score 30-69: Revisão manual (delay 2h)
- Score 70-89: Delay de segurança (24h)
- Score ≥ 90: Bloqueio automático

**RN-PAG-007: Status de Pagamento**
- Fluxo normal:
  - PENDENTE → PROCESSANDO → CONFIRMADO/APROVADO
- Fluxo de rejeição:
  - PENDENTE → PROCESSANDO → NEGADO/REJEITADO
- Fluxo de estorno:
  - CONFIRMADO → ESTORNADO

**RN-PAG-008: Timeout de Processamento**
- Pagamentos PROCESSANDO por mais de 10 minutos → status PENDENTE
- Sistema reprocessa automaticamente

### 4.3 Confirmação de Reserva Pós-Pagamento

**RN-PAG-009: Confirmação Automática**
- Quando pagamento é APROVADO/CONFIRMADO
- Sistema atualiza reserva: PENDENTE → **CONFIRMADA**
- Notificação enviada ao cliente
- Voucher de confirmação gerado

---

## 5. REGRAS DE PONTOS DE FIDELIDADE

### 5.1 Cálculo de Pontos

**RN-PON-001: Regra de Conversão (ÚNICA E CENTRALIZADA)**
- **1 ponto = R$ 10,00 gastos**
- Exemplo: Reserva de R$ 850,00 = 85 pontos
- Arredondamento para baixo (R$ 859,00 = 85 pontos)

**RN-PON-002: Crédito Automático no Check-out**
- Pontos são creditados **automaticamente** após check-out
- Baseado no valor total da reserva
- Sistema idempotente (não duplica pontos)

**RN-PON-003: Tipos de Transação**
- CREDITO: Ganho de pontos
- DEBITO: Uso/resgate de pontos
- BONUS: Pontos promocionais
- RESGATE: Troca por benefícios
- AJUSTE_MANUAL: Correção administrativa
- CONVITE: Pontos por indicação

### 5.2 Uso de Pontos

**RN-PON-004: Saldo Suficiente**
- Cliente só pode usar pontos se saldo >= pontos_debito
- Validação em tempo real

**RN-PON-005: Quantidade Mínima**
- Débito/Crédito deve ser > 0 pontos
- Máximo por transação: 1.000.000 pontos

**RN-PON-006: Validade dos Pontos**
- Pontos não expiram (política atual)
- Pode ser alterado no futuro

### 5.3 Sistema de Convites

**RN-PON-007: Indicação de Amigos**
- Cliente pode gerar código de convite
- Código único: `CONV-XXXXX-YYY`
- Quando indicado usa o código:
  - Indicante ganha: **50 pontos**
  - Indicado ganha: **25 pontos**
- Cada código pode ser usado **1 vez apenas**

---

## 6. REGRAS DE ANTIFRAUDE

### 6.1 Análise de Cliente

**RN-FRD-001: Muitas Reservas em Curto Período**
- Limite: **3 reservas em 7 dias**
- Se exceder: +30 pontos de risco
- Alerta: "Muitas reservas recentes"

**RN-FRD-002: Alta Taxa de Cancelamento**
- Limite: **50%** de cancelamentos
- Se exceder: +40 pontos de risco
- Alerta: "Alta taxa de cancelamento"

**RN-FRD-003: Múltiplos Pagamentos Recusados**
- Limite: **2 pagamentos recusados**
- Se exceder: +30 pontos de risco
- Alerta: "Múltiplos pagamentos recusados"

**RN-FRD-004: Cancelamentos Consecutivos**
- Limite: **2 cancelamentos consecutivos**
- Se exceder: +25 pontos de risco
- Alerta: "Cancelamentos consecutivos"

### 6.2 Análise de Reserva

**RN-FRD-005: Reserva Muito Longa**
- Limite: **15 diárias**
- Se exceder: +10 pontos de risco
- Alerta: "Reserva muito longa"

**RN-FRD-006: Valor Muito Alto**
- Limite: **R$ 5.000,00**
- Se exceder: +15 pontos de risco
- Alerta: "Valor acima da média"

### 6.3 Classificação de Risco

**RN-FRD-007: Níveis de Risco**
- **BAIXO:** score < 30 → Aprovação automática
- **MÉDIO:** score 30-69 → Revisão manual (2h)
- **ALTO:** score 70-89 → Delay de segurança (24h)
- **CRÍTICO:** score ≥ 90 → Bloqueio automático

**RN-FRD-008: Ações Baseadas no Risco**
- BAIXO: Processamento normal
- MÉDIO: Notificação ao gerente + delay 2h
- ALTO: Análise manual obrigatória + delay 24h
- CRÍTICO: Bloqueio + notificação ao admin

---

## 7. REGRAS DE CLIENTES

### 7.1 Cadastro de Cliente

**RN-CLI-001: Dados Obrigatórios**
- Nome completo
- Documento (CPF ou Passaporte)
- Telefone (formato com DDD)
- Email (formato válido)

**RN-CLI-002: Validação de CPF**
- Deve ter 11 dígitos
- Validação de dígitos verificadores
- Não aceita CPFs sequenciais (111.111.111-11)
- Algoritmo de validação completo implementado

**RN-CLI-003: Validação de Email**
- Formato: `usuario@dominio.com`
- Regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

**RN-CLI-004: Validação de Telefone**
- Deve ter 10 ou 11 dígitos (com DDD)
- Formato aceito: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX

**RN-CLI-005: Prevenção de Duplicação**
- Sistema verifica CPF/CNPJ duplicado antes de criar
- Sistema verifica nome completo similar (fuzzy matching)
- Alerta se encontrar cliente similar (>80% match)

### 7.2 Tipos de Cliente

**RN-CLI-006: Níveis de Fidelidade**
- **NORMAL:** Cliente padrão
- **VIP:** > R$ 5.000,00 em gastos ou > 10 reservas
- **PREMIUM:** > R$ 20.000,00 em gastos

**RN-CLI-007: Status do Cliente**
- **ATIVO:** Cliente ativo no sistema
- **INATIVO:** Cliente bloqueado/suspenso

---

## 8. REGRAS DE QUARTOS

### 8.1 Status de Quarto

**RN-QRT-001: Estados Possíveis**
- **LIVRE:** Disponível para reserva
- **OCUPADO:** Hóspede no quarto
- **MANUTENCAO:** Indisponível temporariamente
- **ATIVO:** Operacional (metadado)
- **INATIVO:** Fora de operação (metadado)

**RN-QRT-002: Validação de Disponibilidade**
- Quarto só pode ser reservado se status = LIVRE
- Sistema verifica conflitos de datas automaticamente
- Lock Redis previne race conditions

### 8.2 Tipos de Suíte

**RN-QRT-003: Categorias**
- STANDARD
- LUXO
- MASTER
- PRESIDENCIAL
- Cada tipo tem valor de diária específico

---

## 9. REGRAS DE CANCELAMENTO E ESTORNO

### 9.1 Cancelamento de Reserva

**RN-CAN-001: Status Permitidos para Cancelamento**
- PENDENTE → pode cancelar
- CONFIRMADA → pode cancelar (com estorno se pagou)
- HOSPEDADO → **NÃO pode cancelar** (já está no hotel)
- CHECKED_OUT → **NÃO pode cancelar** (já finalizou)
- CANCELADO → **NÃO pode cancelar** (já cancelado)

**RN-CAN-002: Liberação de Quarto**
- Se reserva estava CONFIRMADA ou HOSPEDADO
- Quarto: OCUPADO → **LIVRE**
- Disponibilizado imediatamente para novas reservas

### 9.2 Estornos Automáticos

**RN-EST-001: Processamento de Estorno**
- Sistema processa estornos **automaticamente** ao cancelar
- Busca pagamentos APROVADOS/CONFIRMADOS da reserva
- Verifica se método permite estorno automático

**RN-EST-002: Métodos com Estorno Automático**
- CREDITO (Cielo): Estorno via API
- PIX: Requer estorno manual
- DINHEIRO: Requer devolução manual
- TRANSFERENCIA: Requer estorno manual

**RN-EST-003: Prazo de Estorno**
- Cartão de crédito: Até 120 dias após pagamento
- Após prazo: Estorno manual obrigatório

**RN-EST-004: Status Pós-Estorno**
- Pagamento: CONFIRMADO → **ESTORNADO**
- Notificação enviada ao cliente
- Prazo de estorno: 5-7 dias úteis (política Cielo)

---

## 10. TRANSIÇÕES DE STATUS

### 10.1 Fluxo de Status de Reserva

**RN-STS-001: Transições Válidas**

```
PENDENTE → CONFIRMADA (após pagamento aprovado)
PENDENTE → CANCELADO (cancelamento antes de pagar)

CONFIRMADA → HOSPEDADO (check-in realizado)
CONFIRMADA → CANCELADO (cancelamento após pagar)

HOSPEDADO → CHECKED_OUT (check-out realizado)

CHECKED_OUT → [FINAL] (não permite mais transições)
CANCELADO → [FINAL] (não permite mais transições)
```

**RN-STS-002: Transições Bloqueadas**
- HOSPEDADO → CANCELADO ❌ (não cancela hóspede no hotel)
- CHECKED_OUT → qualquer ❌ (estado final)
- CANCELADO → qualquer ❌ (estado final)

### 10.2 Fluxo de Status de Pagamento

**RN-STS-003: Transições Válidas**

```
PENDENTE → PROCESSANDO (iniciando processamento)
PROCESSANDO → CONFIRMADO (pagamento aprovado)
PROCESSANDO → NEGADO (pagamento rejeitado)

CONFIRMADO → ESTORNADO (estorno solicitado)

NEGADO → PENDENTE (pode tentar novamente)

ESTORNADO → [FINAL]
```

### 10.3 Fluxo de Status de Hospedagem

**RN-STS-004: Transições Válidas**

```
NAO_INICIADA → CHECKIN_REALIZADO (check-in)
CHECKIN_REALIZADO → CHECKOUT_REALIZADO (check-out)
CHECKOUT_REALIZADO → ENCERRADA (limpeza concluída)

ENCERRADA → [FINAL]
```

---

## 11. REGRAS DE AUTORIZAÇÃO E PERFIS

### 11.1 Perfis de Usuário

**RN-AUT-001: Perfis Disponíveis**
- **ADMIN:** Acesso total ao sistema
- **GERENTE:** Gestão operacional, relatórios, aprovações
- **RECEPCIONISTA:** Check-in/out, reservas, pagamentos
- **AUDITOR:** Somente leitura, relatórios
- **HOSPEDE:** Acesso ao app mobile (futuro)

### 11.2 Permissões por Perfil

**RN-AUT-002: RECEPCIONISTA**
- ✅ Criar/editar reservas
- ✅ Realizar check-in/check-out
- ✅ Processar pagamentos
- ✅ Visualizar reservas
- ❌ Deletar reservas
- ❌ Alterar configurações
- ❌ Acessar relatórios financeiros

**RN-AUT-003: GERENTE**
- ✅ Todas as permissões de RECEPCIONISTA
- ✅ Aprovar pagamentos suspeitos
- ✅ Gerenciar quartos
- ✅ Acessar relatórios
- ✅ Deletar reservas
- ❌ Alterar configurações de sistema

**RN-AUT-004: ADMIN**
- ✅ Acesso irrestrito
- ✅ Gerenciar usuários
- ✅ Alterar configurações
- ✅ Acessar logs de auditoria

**RN-AUT-005: AUDITOR**
- ✅ Visualizar todas as informações
- ✅ Gerar relatórios
- ❌ Criar/editar/deletar qualquer recurso

### 11.3 Autenticação

**RN-AUT-006: JWT Tokens**
- Expiração: 24 horas
- Refresh token: 7 dias
- Armazenado em cookie HttpOnly (seguro)

**RN-AUT-007: Rotas Protegidas**
- Todas as rotas de API requerem autenticação
- Header: `Authorization: Bearer <token>`
- Ou cookie: `access_token`

---

## 12. REGRAS DE NOTIFICAÇÕES

### 12.1 Eventos que Geram Notificações

**RN-NOT-001: Notificações Automáticas**
- Reserva criada → Cliente
- Pagamento aprovado → Cliente + Gerente
- Check-in realizado → Cliente + Recepção
- Check-out realizado → Cliente + Financeiro
- Reserva cancelada → Cliente + Gerente
- Estorno processado → Cliente + Financeiro
- Análise anti-fraude (risco alto) → Gerente + Admin

**RN-NOT-002: Canais de Notificação**
- Email (primário)
- SMS (pagamentos e check-in)
- Push notification (app mobile - futuro)
- Dashboard interno (para equipe)

---

## 13. REGRAS DE VOUCHERS

### 13.1 Geração de Voucher

**RN-VOU-001: Quando Gerar**
- Após confirmação de pagamento
- Após check-in realizado
- Contém código QR único

**RN-VOU-002: Dados do Voucher**
- Código único: `VHCK-XXXXX`
- Nome do hóspede
- Número do quarto
- Datas de check-in e check-out
- Valor total
- QR Code para validação

**RN-VOU-003: Validade**
- Voucher de confirmação: válido até check-in
- Voucher de hospedagem: válido durante estadia

---

## 14. REGRAS DE RELATÓRIOS

### 14.1 Exportação de Dados

**RN-REL-001: Formatos Disponíveis**
- CSV (para Excel)
- PDF (para impressão)
- JSON (para integração)

**RN-REL-002: Filtros Disponíveis**
- Por período (datas)
- Por status
- Por cliente
- Por quarto
- Por método de pagamento

**RN-REL-003: Permissões**
- RECEPCIONISTA: Relatórios operacionais
- GERENTE: Todos os relatórios
- AUDITOR: Todos os relatórios
- ADMIN: Todos os relatórios + logs de auditoria

---

## 15. REGRAS DE PERFORMANCE E CACHE

### 15.1 Cache Redis

**RN-PER-001: Dados em Cache**
- Lista de quartos disponíveis (5 min)
- Configurações do sistema (30 min)
- Taxas de câmbio (1 hora)

**RN-PER-002: Locks Distribuídos**
- Lock na criação de reserva (previne overbooking)
- Lock no check-in (previne duplicação)
- Timeout: 10 segundos

### 15.2 Otimizações

**RN-PER-003: Lazy Loading**
- Relacionamentos carregados sob demanda
- Paginação padrão: 20 itens

---

## ANEXO A: GLOSSÁRIO

| Termo | Definição |
|-------|-----------|
| **Idempotência** | Garantia de que uma operação pode ser executada múltiplas vezes sem efeitos colaterais |
| **Race Condition** | Situação onde duas operações concorrentes competem por um recurso |
| **Lock Distribuído** | Mecanismo para garantir exclusividade em ambiente multi-thread/processo |
| **Fuzzy Matching** | Comparação aproximada de strings (similaridade) |
| **Webhook** | Notificação HTTP enviada por sistema externo |
| **Gateway** | Intermediário para processar pagamentos (ex: Cielo) |

---

## ANEXO B: CÓDIGOS DE ERRO HTTP

| Código | Significado | Uso no Sistema |
|--------|-------------|----------------|
| 200 | OK | Operação bem-sucedida |
| 201 | Created | Recurso criado |
| 400 | Bad Request | Validação falhou |
| 401 | Unauthorized | Não autenticado |
| 403 | Forbidden | Sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 409 | Conflict | Conflito de recursos (ex: quarto ocupado) |
| 422 | Unprocessable Entity | Erro de validação de negócio |
| 500 | Internal Server Error | Erro interno |

---

## ANEXO C: CONTATOS TÉCNICOS

**Equipe de Desenvolvimento:**
- Backend: FastAPI + Python 3.12 + Prisma ORM
- Frontend: Next.js 14 + React + TailwindCSS
- Database: PostgreSQL (Prisma Data Platform)
- Cache: Redis
- Gateway: Cielo

**Ambiente:**
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Proxy Reverso: Nginx + ngrok

---

**FIM DO DOCUMENTO**

*Este documento está sujeito a atualizações conforme o sistema evolui.*
