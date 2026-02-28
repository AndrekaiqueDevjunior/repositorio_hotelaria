# 🧪 Guia de Testes End-to-End - Sistema Hotel Cabo Frio

## 🎯 Objetivo
Testar fluxo completo: **Backend (Prisma) → API → Frontend → Banco de Dados**

---

## ✅ Pré-requisitos
- ✅ Backend rodando: http://localhost:8080/api/v1
- ✅ Frontend rodando: http://localhost:8080
- ✅ Prisma conectado ao banco de dados
- ✅ Redis conectado

---

## 🧪 Teste 1: Autenticação e Acesso

### Passo 1: Login
1. Acessar: http://localhost:8080
2. Credenciais padrão:
   - **Email:** `admin@hotelreal.com.br`
   - **Senha:** `admin123`
3. ✅ **Esperado:** Redirecionamento para dashboard

---

## 🧪 Teste 2: Gestão de Clientes

### Passo 1: Criar Cliente
1. Ir para: `/clientes`
2. Clicar em **"Novo Cliente"**
3. Preencher dados:
   - Nome Completo: `João da Silva Teste`
   - Documento (CPF): `123.456.789-00`
   - Telefone: `(22) 98765-4321`
   - Email: `joao.teste@email.com`
4. Clicar em **"Criar Cliente"**
5. ✅ **Esperado:** Cliente criado e visível na lista

### Validações Automáticas (Backend):
- ✅ CPF único no banco
- ✅ Relacionamento Prisma: `Cliente` → `Reservas`

---

## 🧪 Teste 3: Gestão de Quartos

### Passo 1: Verificar Quartos Disponíveis
1. Ir para: `/quartos`
2. ✅ **Esperado:** Lista de quartos com status (LIVRE, OCUPADO, etc.)

### Passo 2: Criar Novo Quarto (se necessário)
1. Clicar em **"Novo Quarto"**
2. Preencher:
   - Número: `501`
   - Tipo de Suíte: `LUXO`
   - Status: `LIVRE`
3. ✅ **Esperado:** Quarto criado

---

## 🧪 Teste 4: Criar Reserva (FLUXO PRINCIPAL)

### Passo 1: Ir para Reservas
1. Acessar: `/reservas`
2. ✅ **Esperado:** Ver indicadores no topo:
   - Total de Reservas
   - Pendentes
   - Hospedadas
   - Check-outs
   - Valor Previsto

### Passo 2: Criar Nova Reserva
1. Clicar em **"➕ Nova Reserva"**
2. Preencher formulário:
   - Cliente: Selecionar `João da Silva Teste`
   - Quarto: Selecionar `501 - LUXO (LIVRE)`
   - Check-in: Data futura (ex: amanhã)
   - Check-out: Data futura +3 dias
   - Valor Diária: `350.00`
3. Clicar em **"Criar Reserva"**
4. ✅ **Esperado:**
   - Reserva criada com sucesso
   - Código de reserva gerado automaticamente
   - Status inicial: `PENDENTE`
   - Aparecer na aba "Reservas Ativas"

### Validações Automáticas (Backend via Prisma):
- ✅ Cliente existe
- ✅ Quarto disponível (sem conflito de datas)
- ✅ Valor total calculado automaticamente
- ✅ Relacionamentos carregados: `Reserva` → `Cliente`, `Reserva` → `Pagamentos`

---

## 🧪 Teste 5: Visão Operacional de Reservas

### Passo 1: Testar Indicadores
1. Na página `/reservas`, verificar cards no topo
2. ✅ **Esperado:**
   - Total de Reservas: atualizado
   - Pendentes: +1
   - Valor Previsto: soma atualizada

### Passo 2: Validador de Código de Reserva
1. Copiar código da reserva criada (ex: `RES-2024-001`)
2. Colar no campo **"Validador de Código de Reserva"**
3. Clicar em **"Validar"**
4. ✅ **Esperado:**
   - ✅ Mensagem: "Reserva válida!"
   - Exibir: Cliente, Quarto, Status
   - **API chamada:** `GET /api/v1/reservas?search={codigo}`

### Passo 3: Testar Filtros
1. **Filtro por Status:**
   - Selecionar "Pendente"
   - ✅ **Esperado:** Mostrar apenas reservas pendentes
   
2. **Busca por Cliente:**
   - Digitar: `João`
   - ✅ **Esperado:** Filtrar reservas do João

3. **Filtro por Período:**
   - Definir Check-in de/até
   - ✅ **Esperado:** Filtrar por data

4. **Limpar Filtros:**
   - Clicar em "Limpar"
   - ✅ **Esperado:** Voltar à lista completa

### Passo 4: Testar Abas
1. **Aba "Reservas Ativas":**
   - ✅ Ver reservas com status: PENDENTE, CONFIRMADA, HOSPEDADO
   
2. **Aba "Excluídas/Finalizadas":**
   - ✅ Ver reservas: CANCELADO, CHECKED_OUT
   
3. **Aba "Quartos":**
   - ✅ Ver lista de quartos com status

### Passo 5: Testar Ações Contextuais
1. Na reserva criada, verificar botões disponíveis:
   - ✅ **👁️ Detalhes** (sempre visível)
   - ✅ **💳 Pagar** (só se PENDENTE/CONFIRMADA)
   - 🔑 Check-in (desabilitado se não CONFIRMADA)
   - 🏃 Checkout (desabilitado se não HOSPEDADO)
   - ❌ Cancelar (só se PENDENTE/CONFIRMADA)

---

## 🧪 Teste 6: Processar Pagamento

### Passo 1: Clicar em "💳 Pagar"
1. Abrir modal de pagamento
2. Preencher dados do cartão de teste:
   - Número: `4000 0000 0000 0010`
   - Validade: `12/25`
   - CVV: `123`
   - Nome: `João Silva`
3. Clicar em **"Processar Pagamento"**
4. ✅ **Esperado:**
   - Status da reserva: `PENDENTE` → `CONFIRMADA`
   - Pagamento registrado no banco via Prisma
   - Relacionamento `Reserva` → `Pagamentos` populado

### Validações Automáticas (Backend):
- ✅ Status da reserva válido para pagamento
- ✅ Pagamento não duplicado (idempotência)
- ✅ Integração com gateway Cielo (ou mock)

---

## 🧪 Teste 7: Exportação de Dados

### Passo 1: Exportar CSV
1. Aplicar filtros desejados
2. Clicar em **"📄 Exportar CSV"**
3. ✅ **Esperado:**
   - Download de arquivo `reservas_YYYY-MM-DD.csv`
   - Conteúdo: Código, Cliente, Quarto, Datas, Valor, Status

### Passo 2: Exportar PDF (futuro)
1. Clicar em **"📕 Exportar PDF"**
2. ✅ **Esperado:** Mensagem "Em desenvolvimento"

---

## 🧪 Teste 8: Paginação

### Passo 1: Testar Navegação
1. Se houver mais de 10 reservas:
2. Verificar contador: "Mostrando 1 a 10 de X resultados"
3. Clicar em **"Próxima →"**
4. ✅ **Esperado:**
   - Página incrementada
   - Novos registros carregados
5. Clicar em **"← Anterior"**
6. ✅ **Esperado:** Voltar à página anterior

---

## 🧪 Teste 9: Relacionamentos Prisma (Validação Técnica)

### Verificar no Backend:
```bash
# Verificar logs do backend
docker-compose logs backend --tail=50

# Deve mostrar:
# - [Prisma] Conectado ao banco
# - Queries carregando relacionamentos (include: pagamentos, cliente, etc.)
```

### Relacionamentos Testados:
- ✅ `Cliente` → `Reservas` (one-to-many)
- ✅ `Reserva` → `Cliente` (many-to-one)
- ✅ `Reserva` → `Pagamentos` (one-to-many)
- ✅ `Pagamento` → `Reserva` (many-to-one)

---

## 🧪 Teste 10: Check-in (Quando implementado)

### Passo 1: Validar Check-in
1. Clicar em **"🔑 Check-in"** (só aparece se CONFIRMADA)
2. ✅ **Esperado:**
   - Modal com validações:
     - ✅ Pagamento aprovado
     - ✅ Documentos conferidos
     - ✅ Quarto disponível
3. Preencher dados:
   - Nº adultos: `2`
   - Nº crianças: `0`
   - Placa veículo: `ABC-1234`
4. Confirmar Check-in
5. ✅ **Esperado:**
   - Status: `CONFIRMADA` → `HOSPEDADO`
   - Quarto: `LIVRE` → `OCUPADO`

---

## 🧪 Teste 11: Check-out (Quando implementado)

### Passo 1: Realizar Check-out
1. Clicar em **"🏃 Checkout"** (só aparece se HOSPEDADO)
2. Preencher:
   - Consumo frigobar: `50.00`
   - Serviços extras: `100.00`
   - Avaliação: 5 estrelas
   - Comentário: "Excelente hospedagem!"
3. Confirmar Checkout
4. ✅ **Esperado:**
   - Status: `HOSPEDADO` → `CHECKED_OUT`
   - Quarto: `OCUPADO` → `LIVRE`
   - Valor final calculado (hospedagem + consumos)

---

## ✅ Checklist de Validação Final

### Frontend:
- [ ] Todas as telas carregam sem erros de console
- [ ] Indicadores calculando corretamente
- [ ] Filtros funcionando
- [ ] Paginação navegando corretamente
- [ ] Ações contextuais aparecendo conforme status
- [ ] Modais abrindo e fechando corretamente

### Backend:
- [ ] API respondendo sem erros 500
- [ ] Relacionamentos Prisma carregando corretamente
- [ ] Validações de negócio funcionando
- [ ] Logs sem erros críticos

### Banco de Dados (Prisma):
- [ ] Dados sendo salvos corretamente
- [ ] Relacionamentos mantidos (foreign keys)
- [ ] Queries otimizadas (include para evitar N+1)

---

## 🐛 Problemas Conhecidos

### Temporariamente Desabilitado:
- ⚠️ Rotas avançadas de check-in/checkout robusto (requerem refatoração para Prisma)
- ⚠️ Sistema de consumos durante hospedagem
- ⚠️ Políticas de cancelamento
- ⚠️ Visão operacional avançada (mapa de ocupação)

### Funcionando:
- ✅ CRUD completo de Clientes, Quartos, Reservas
- ✅ Sistema de Pagamentos
- ✅ Visão operacional de reservas (frontend)
- ✅ Validador de código de reserva
- ✅ Filtros e buscas
- ✅ Exportação CSV

---

## 📊 Métricas de Sucesso

### ✅ Sistema Aprovado Se:
1. Possível criar cliente → reserva → pagamento sem erros
2. Relacionamentos Prisma carregando corretamente
3. Frontend refletindo mudanças do backend em tempo real
4. Validações de negócio funcionando (ex: não permitir reserva duplicada)
5. Logs sem erros críticos

---

## 🚀 Próximos Passos (Após Testes)

1. **Refatorar rotas avançadas para Prisma**
   - Check-in robusto
   - Checkout com consumos
   - Sistema de cancelamento
   
2. **Implementar testes automatizados**
   - Unit tests (Jest)
   - Integration tests (Playwright)
   
3. **Monitoramento em produção**
   - Sentry para erros
   - Analytics para uso

---

**Versão:** 1.0
**Data:** 07/01/2026
**Status:** 🧪 Pronto para testes
