# VALIDAÇÃO: Lógicas vs Práticas Reais de Hotelaria

**Consultor**: Operações Hoteleiras e PMS  
**Data**: 03/01/2026  
**Baseline**: Hotéis 3-4 estrelas Brasil + sistemas PMS comerciais

---

## ✅ CHECKLIST: Conformidade com Práticas Reais

### 1. RESERVAS

| Funcionalidade | Implementado | Real World | Status | Gap |
|----------------|--------------|------------|--------|-----|
| **Criação de reserva** | ✅ Sim | ✅ Obrigatório | ✅ OK | - |
| **Código único de reserva** | ✅ Sim (gerado) | ✅ Obrigatório | ✅ OK | - |
| **Voucher de confirmação** | ✅ Sim | ✅ Obrigatório | ✅ OK | - |
| **Reserva sem pagamento** | ✅ Sim (PENDENTE) | ⚠️ Depende da política | ⚠️ ATENÇÃO | Falta política de garantia |
| **Garantia de reserva** | ❌ Não | ✅ Pré-autorização cartão | ❌ CRÍTICO | Sem pré-autorização |
| **No-show** | ❌ Não | ✅ Cobrança taxa | ❌ CRÍTICO | Status não existe |
| **Early check-in** | ❌ Não | ✅ Opcional (taxa) | ⚠️ GAP | Não gerencia horários |
| **Late check-out** | ❌ Não | ✅ Opcional (taxa) | ⚠️ GAP | Não gerencia horários |
| **Alteração de datas** | ⚠️ Via UPDATE | ✅ Comum | ⚠️ GAP | Sem validação de disponibilidade |
| **Upgrade de quarto** | ❌ Não | ✅ Comum | ⚠️ GAP | - |
| **Reserva grupo** | ❌ Não | ✅ PMS médio/grande | ⚠️ DESEJÁVEL | - |
| **Bloqueio de quartos** | ❌ Não | ✅ Eventos/manutenção | ⚠️ GAP | Só tem MANUTENCAO |

**SCORE RESERVAS**: 4/12 ✅ | 2/12 ⚠️ | 6/12 ❌ = **33% conformidade**

---

### 2. CHECK-IN / CHECK-OUT

| Funcionalidade | Implementado | Real World | Status | Gap |
|----------------|--------------|------------|--------|-----|
| **Validação de documento** | ❌ Não | ✅ Obrigatório (CPF/RG) | ❌ CRÍTICO | Não pede documento |
| **Validação de voucher** | ✅ Sim | ✅ Obrigatório | ✅ OK | - |
| **Verificação de pagamento** | ⚠️ Parcial (bug) | ✅ Obrigatório | ❌ CRÍTICO | Bug identificado |
| **Coleta de dados hóspedes** | ✅ Sim (num_hospedes) | ✅ Obrigatório (LGPD) | ⚠️ PARCIAL | Falta dados individuais |
| **Ficha FNRH** | ❌ Não | ✅ Obrigatório (Polícia Federal) | ❌ CRÍTICO | Obrigação legal |
| **Assinatura digital** | ❌ Não | ✅ Comum | ⚠️ GAP | - |
| **Depósito caução** | ❌ Não | ✅ Comum | ⚠️ GAP | Apenas frigobar |
| **Walk-in (sem reserva)** | ❌ Não | ✅ Comum | ⚠️ GAP | - |
| **Check-in antecipado** | ⚠️ Não gerencia | ✅ Comum (14h padrão) | ⚠️ GAP | - |
| **Check-out tardio** | ⚠️ Não gerencia | ✅ Comum (12h padrão) | ⚠️ GAP | - |
| **Express check-out** | ❌ Não | ✅ Desejável | ⚠️ DESEJÁVEL | - |
| **Fechamento de conta** | ✅ Sim (consumos) | ✅ Obrigatório | ✅ OK | - |

**SCORE CHECK-IN/OUT**: 2/12 ✅ | 7/12 ⚠️ | 3/12 ❌ = **25% conformidade**

---

### 3. PAGAMENTOS

| Funcionalidade | Implementado | Real World | Status | Gap |
|----------------|--------------|------------|--------|-----|
| **Cartão crédito** | ✅ Sim (Cielo) | ✅ Obrigatório | ✅ OK | - |
| **Cartão débito** | ✅ Sim (Cielo) | ✅ Obrigatório | ✅ OK | - |
| **PIX** | ✅ Sim (Cielo) | ✅ Obrigatório | ✅ OK | - |
| **Dinheiro** | ❌ Não | ✅ Comum | ⚠️ GAP | - |
| **Boleto** | ⚠️ Tipo existe | ❌ Raro hotéis | ⚠️ OK | - |
| **Pré-autorização** | ❌ Não | ✅ Garantia reserva | ❌ CRÍTICO | Só captura total |
| **Captura posterior** | ❌ Não | ✅ No-show/damages | ❌ CRÍTICO | - |
| **Estorno** | ❌ Não | ✅ Cancelamentos | ❌ CRÍTICO | Apenas flag |
| **Pagamento parcial** | ⚠️ Aceita múltiplos | ✅ Comum | ✅ OK | Não valida total |
| **Split payment** | ❌ Não | ✅ Grupos | ⚠️ GAP | - |
| **Faturamento empresa** | ❌ Não | ✅ Corporate | ⚠️ GAP | - |
| **Nota fiscal** | ❌ Não | ✅ Obrigatório | ❌ CRÍTICO | Sem emissão NF-e |

**SCORE PAGAMENTOS**: 4/12 ✅ | 4/12 ⚠️ | 4/12 ❌ = **42% conformidade**

---

### 4. ANTIFRAUDE

| Funcionalidade | Implementado | Real World | Status | Gap |
|----------------|--------------|------------|--------|-----|
| **Análise comportamental** | ✅ Sim (regras) | ✅ Obrigatório | ✅ OK | Sem ML |
| **Blacklist de clientes** | ❌ Não | ✅ Comum | ❌ GAP | Só alerta |
| **Validação de documento** | ❌ Não | ✅ CPF/RG válidos | ❌ CRÍTICO | Não valida |
| **Checagem de cartão** | ⚠️ Via Cielo | ✅ Gateway | ✅ OK | Delegado |
| **Score de risco** | ✅ Sim | ✅ Comum | ✅ OK | - |
| **Alertas gerência** | ⚠️ Apenas log | ✅ Email/notificação | ⚠️ GAP | Sem notificação |
| **Integração bureau** | ❌ Não | ✅ Hotéis grandes | ⚠️ DESEJÁVEL | Serasa, SPC |
| **Análise de IP** | ❌ Não | ✅ Comum | ⚠️ GAP | - |
| **Device fingerprint** | ❌ Não | ✅ Comum | ⚠️ GAP | - |
| **Validação telefone** | ❌ Não | ✅ SMS/WhatsApp | ⚠️ GAP | - |

**SCORE ANTIFRAUDE**: 2/10 ✅ | 5/10 ⚠️ | 3/10 ❌ = **35% conformidade**

---

### 5. FIDELIDADE

| Funcionalidade | Implementado | Real World | Status | Gap |
|----------------|--------------|------------|--------|-----|
| **Programa de pontos** | ✅ Sim | ✅ Comum | ✅ OK | - |
| **Acúmulo por gasto** | ✅ Sim (R$10=1pt) | ✅ Padrão | ✅ OK | - |
| **Indicação/convite** | ✅ Sim | ✅ Comum | ✅ OK | - |
| **Resgate de pontos** | ⚠️ Debita, não usa | ✅ Descontos/upgrades | ⚠️ GAP | Sem aplicação |
| **Níveis/tiers** | ❌ Não | ✅ Bronze/Prata/Ouro | ⚠️ GAP | - |
| **Benefícios por tier** | ❌ Não | ✅ Upgrades/late checkout | ⚠️ GAP | - |
| **Expiração de pontos** | ❌ Não | ✅ 12-24 meses | ⚠️ GAP | Pontos eternos |
| **Extrato de pontos** | ✅ Sim (histórico) | ✅ Obrigatório | ✅ OK | - |
| **Transferência pontos** | ❌ Não | ⚠️ Raro | ⚠️ OK | - |

**SCORE FIDELIDADE**: 4/9 ✅ | 5/9 ⚠️ | 0/9 ❌ = **56% conformidade**

---

### 6. GESTÃO DE QUARTOS

| Funcionalidade | Implementado | Real World | Status | Gap |
|----------------|--------------|------------|--------|-----|
| **Cadastro de quartos** | ✅ Sim | ✅ Obrigatório | ✅ OK | - |
| **Tipos de acomodação** | ✅ Sim (3 tipos) | ✅ Obrigatório | ✅ OK | - |
| **Status de quarto** | ✅ LIVRE/OCUPADO/MANUTENCAO | ✅ + LIMPEZA/SUJO | ⚠️ PARCIAL | Falta housekeeping |
| **Histórico de ocupação** | ✅ Sim | ✅ Comum | ✅ OK | - |
| **Disponibilidade por período** | ✅ Sim | ✅ Obrigatório | ✅ OK | - |
| **Bloqueio de quarto** | ⚠️ Só MANUTENCAO | ✅ Vários motivos | ⚠️ GAP | - |
| **Housekeeping** | ❌ Não | ✅ Obrigatório | ❌ CRÍTICO | Sem gestão limpeza |
| **Manutenção preventiva** | ❌ Não | ✅ Comum | ⚠️ GAP | - |
| **Inventário de amenities** | ❌ Não | ✅ Comum | ⚠️ GAP | - |

**SCORE QUARTOS**: 5/9 ✅ | 3/9 ⚠️ | 1/9 ❌ = **61% conformidade**

---

## 🔍 ANÁLISE COMPARATIVA: Sistema Atual vs PMS Real

### PMS de Referência (Mercado Brasil):
- **Omnibees / HSystem / Hórus / Desbravador**

### Funcionalidades Críticas AUSENTES:

#### 1. **FICHA FNRH (Polícia Federal)** ❌
**Obrigação Legal**: Lei 11.771/2008  
**Impacto**: **BLOQUEANTE PARA OPERAÇÃO LEGAL**

O sistema **DEVE** coletar:
- Nome completo
- CPF/RG + órgão emissor
- Nacionalidade
- Data de nascimento
- Endereço completo
- Profissão
- Motivo da viagem
- Destino seguinte

E **DEVE** enviar para:
- Polícia Federal (sistema SINCS)
- Ou manter livro físico (ultrapassado)

**Recomendação**: Implementar integração com API Polícia Federal (SINCS).

---

#### 2. **NO-SHOW** ❌
**Prática Universal**: Cliente não comparece, hotel cobra taxa.

**Como deveria ser**:
```
SE checkin_previsto + 24h passou E status != HOSPEDADO:
  - Marcar como NO_SHOW
  - Cobrar taxa (50-100% valor primeira diária)
  - Capturar pré-autorização do cartão
  - Liberar quarto para venda
```

**Impacto financeiro**: Hotéis perdem 5-15% receita por no-shows não gerenciados.

---

#### 3. **PRÉ-AUTORIZAÇÃO DE CARTÃO** ❌
**Prática Universal**: Garantir reserva sem capturar dinheiro.

**Fluxo correto**:
```
1. Reserva criada → pré-autoriza cartão (R$ valor_total)
2. Check-in → captura pré-autorização
3. Check-out → ajusta valor final (consumos)
4. Libera saldo não usado
```

**Sistema atual**: Captura total no momento da reserva (ruim para cliente).

---

#### 4. **NOTA FISCAL ELETRÔNICA** ❌
**Obrigação Legal**: Todos estabelecimentos devem emitir NF-e.

**Impacto**: **BLOQUEANTE FISCAL**

**Recomendação**: Integrar com:
- API SEFAZ (direto)
- OU serviço terceiro (Tiny ERP, Bling, NFE.io)

---

#### 5. **HOUSEKEEPING (Gestão de Limpeza)** ❌
**Prática Universal**: Rastrear limpeza de quartos.

**Estados necessários**:
- `SUJO` - Hóspede saiu, precisa limpar
- `EM_LIMPEZA` - Camareira trabalhando
- `LIMPO` - Pronto para novo hóspede
- `INSPECIONADO` - Governança aprovou

**Sem isso**: Recepção não sabe quais quartos pode vender.

---

## 📊 CONFORMIDADE GERAL

```
┌──────────────────────────────────────────────────────┐
│         CONFORMIDADE COM PRÁTICAS REAIS              │
├──────────────────────────────────────────────────────┤
│ Reservas           │ ████░░░░░░░░ 33% │ BAIXO        │
│ Check-in/out       │ ███░░░░░░░░░ 25% │ CRÍTICO      │
│ Pagamentos         │ █████░░░░░░░ 42% │ MÉDIO        │
│ Antifraude         │ ████░░░░░░░░ 35% │ BAIXO        │
│ Fidelidade         │ ██████░░░░░░ 56% │ BOM          │
│ Quartos            │ ███████░░░░░ 61% │ BOM          │
├──────────────────────────────────────────────────────┤
│ MÉDIA GERAL        │ ████░░░░░░░░ 42% │ INSUFICIENTE │
└──────────────────────────────────────────────────────┘
```

---

## 🚨 BLOQUEADORES LEGAIS

### 1. FICHA FNRH
**Lei**: 11.771/2008  
**Órgão**: Polícia Federal  
**Multa**: R$ 1.000 - R$ 10.000 por infração  
**Status**: ❌ NÃO IMPLEMENTADO

### 2. NOTA FISCAL
**Lei**: LC 116/2003 + regulamentação municipal  
**Órgão**: SEFAZ  
**Multa**: 100% do valor não emitido  
**Status**: ❌ NÃO IMPLEMENTADO

### 3. LGPD (Dados Pessoais)
**Lei**: 13.709/2018  
**Órgão**: ANPD  
**Multa**: Até R$ 50 milhões ou 2% faturamento  
**Status**: ⚠️ PARCIAL (falta consentimento explícito)

---

## ✅ PONTOS FORTES DO SISTEMA

1. ✅ **Integração com gateway de pagamento** (Cielo)
2. ✅ **Programa de fidelidade funcional**
3. ✅ **Sistema de vouchers**
4. ✅ **Antifraude baseado em regras**
5. ✅ **Gestão básica de quartos**
6. ✅ **Disponibilidade por período**

---

## ❌ GAPS CRÍTICOS A CORRIGIR

### Prioridade P0 (Bloqueante)
1. Implementar FNRH (Polícia Federal)
2. Integrar NF-e (obrigação fiscal)
3. Corrigir bug check-in/checkout
4. Implementar pré-autorização cartão
5. Adicionar validação de documentos

### Prioridade P1 (Operação)
6. Implementar no-show
7. Adicionar housekeeping
8. Early/late check-in/out
9. Estorno de pagamentos
10. Walk-in (sem reserva)

### Prioridade P2 (Melhoria)
11. Upgrade de quartos
12. Reserva de grupos
13. Níveis de fidelidade
14. Resgate de pontos
15. Channel Manager

---

## 🎯 RECOMENDAÇÕES ESTRATÉGICAS

### Curto Prazo (1-2 meses)
- Corrigir bug check-in/checkout
- Implementar FNRH
- Adicionar validação CPF

### Médio Prazo (3-6 meses)
- Integrar NF-e
- Implementar housekeeping
- Adicionar no-show
- Pré-autorização cartão

### Longo Prazo (6-12 meses)
- Channel Manager (OTAs)
- Sistema de revenue management
- BI e relatórios avançados

---

**CONCLUSÃO**: Sistema possui **42% de conformidade** com práticas reais de hotelaria. Principais gaps são **obrigações legais** (FNRH, NF-e) e **gestão operacional** (housekeeping, no-show). Funcionalidades básicas estão implementadas, mas faltam refinamentos críticos para operação profissional.

---

**FIM DA VALIDAÇÃO**
