# 🎁 Fluxo de Resgate de Prêmios - Hotel Real Cabo Frio

## 📋 Visão Geral

Este documento descreve o fluxo completo de resgate de prêmios no sistema de fidelidade do Hotel Real Cabo Frio.

---

## 🔄 Fluxo Completo

### 1️⃣ **Consulta de Pontos**
**URL:** `http://localhost:8080/consultar-pontos`

**Passos:**
1. Cliente acessa a página pública de consulta
2. Insere CPF/CNPJ (formato: `483.736.638-43` ou `48373663843`)
3. Clica em "🔍 Consultar Pontos"

**Backend:**
- **Endpoint:** `GET /api/v1/premios/consulta/{documento}`
- **Arquivo:** `backend/app/routers/premios.py`
- **Retorno:**
```json
{
  "cliente": {
    "nome": "Nome do Cliente",
    "documento": "48373663843"
  },
  "saldo_pontos": 1000,
  "premios_disponiveis": [...],
  "premios_proximos": [...],
  "todos_premios": [...]
}
```

---

### 2️⃣ **Exibição de Prêmios**

O sistema categoriza os prêmios em 3 grupos:

#### 🟢 **Prêmios Disponíveis** (Cliente TEM pontos suficientes)
- Badge verde: "✓ Você pode resgatar!"
- Botão **"🎁 Resgatar Agora"** VISÍVEL
- Condição: `saldo_pontos >= premio.preco_em_pontos`

#### 🟡 **Prêmios Próximos** (Faltam até 50% dos pontos)
- Badge amarelo: "Faltam X pontos"
- Botão de resgate NÃO aparece
- Condição: `saldo_pontos < premio.preco_em_pontos && faltam <= 50%`

#### ⚪ **Todos os Prêmios**
- Catálogo completo
- Botão de resgate NÃO aparece
- Apenas visualização

**Código relevante:** `frontend/app/consultar-pontos/page.js` (linhas 350-450)

---

### 3️⃣ **Iniciando o Resgate**

**Ação:** Cliente clica em "🎁 Resgatar Agora"

**Frontend:**
```javascript
const abrirModalResgate = (premio) => {
  setPremioSelecionado(premio)
  setObservacoes('')
  setShowResgateModal(true)
}
```

**Modal de Confirmação exibe:**
- 🖼️ Imagem do prêmio
- 📝 Nome e descrição
- 💰 Resumo financeiro:
  - Saldo atual
  - Custo do prêmio
  - Novo saldo (após resgate)
- 📄 Campo de observações (opcional)

---

### 4️⃣ **Confirmação do Resgate**

**Ação:** Cliente clica em "✓ Confirmar Resgate"

**Frontend:**
```javascript
const confirmarResgate = async () => {
  const res = await api.post('/premios/resgatar-publico', {
    premio_id: premioSelecionado.id,
    cliente_documento: resultado.cliente.documento,
    observacoes: observacoes || null
  })
  setResgateSuccess(res.data)
}
```

**Backend:**
- **Endpoint:** `POST /api/v1/premios/resgatar-publico`
- **Arquivo:** `backend/app/routers/premios.py`

**Validações realizadas:**
1. ✅ Cliente existe?
2. ✅ Prêmio existe e está ativo?
3. ✅ Cliente tem pontos suficientes?
4. ✅ Prêmio tem estoque disponível?

**Operações executadas:**
1. Debita pontos do cliente
2. Decrementa estoque do prêmio (se aplicável)
3. Cria registro de resgate na tabela `ResgatePremio`
4. Cria transação de pontos (tipo: DEBITO)
5. Gera código único de retirada

**Retorno:**
```json
{
  "success": true,
  "message": "Prêmio resgatado com sucesso!",
  "data": {
    "resgate_id": 123,
    "premio": {
      "nome": "Café da Manhã Premium",
      "imagem_url": "..."
    },
    "pontos_usados": 500,
    "novo_saldo": 500,
    "codigo_retirada": "#000123"
  }
}
```

---

### 5️⃣ **Tela de Sucesso**

**Exibição:**
- 🎉 Animação de sucesso
- 🔢 **Código de Retirada** em destaque (ex: `#000123`)
- 📊 Resumo:
  - Prêmio resgatado
  - Pontos utilizados
  - Novo saldo
- 📍 Instruções de retirada
- 🖨️ Botão "Imprimir Comprovante"

**Código:** `frontend/app/consultar-pontos/page.js` (linhas 623-816)

---

### 6️⃣ **Atualização Automática**

Após o resgate bem-sucedido:
1. Modal de confirmação fecha
2. Sistema recarrega os dados do cliente
3. Saldo atualizado é exibido
4. Lista de prêmios disponíveis é recalculada

```javascript
// Recarregar dados
const cpfLimpo = resultado.cliente.documento
const resAtualizado = await api.get(`/premios/consulta/${cpfLimpo}`)
setResultado(resAtualizado.data)
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabelas Envolvidas:

#### `Cliente`
```sql
- id (PK)
- nome
- documento (CPF/CNPJ)
- saldo_pontos
- created_at
- updated_at
```

#### `Premio`
```sql
- id (PK)
- nome
- descricao
- categoria
- preco_em_pontos
- preco_em_rp
- estoque
- imagem_url
- ativo
- created_at
- updated_at
```

#### `ResgatePremio`
```sql
- id (PK)
- cliente_id (FK)
- premio_id (FK)
- pontos_usados
- observacoes
- status (PENDENTE, ENTREGUE, CANCELADO)
- created_at
- entregue_at
```

#### `TransacaoPontos`
```sql
- id (PK)
- cliente_id (FK)
- tipo (CREDITO, DEBITO)
- pontos
- descricao
- created_at
```

---

## 🧪 Como Testar

### Pré-requisitos:
1. Docker rodando
2. Serviços iniciados: `docker-compose up -d`
3. Cliente com pontos no banco

### Injetar Pontos para Teste:

```bash
# 1. Acessar container do PostgreSQL
docker exec -it <nome_container_postgres> psql -U postgres -d hotel_cabo_frio

# 2. Executar script de injeção
\i /path/to/inject_points.sql

# OU executar manualmente:
UPDATE "Cliente" 
SET saldo_pontos = 1000 
WHERE documento = '48373663843';
```

### Fluxo de Teste:

1. **Acessar:** `http://localhost:8080/consultar-pontos`
2. **Inserir CPF:** `483.736.638-43`
3. **Consultar:** Verificar saldo de 1000 pontos
4. **Visualizar:** Prêmios disponíveis com botão verde
5. **Clicar:** "🎁 Resgatar Agora" em um prêmio
6. **Preencher:** Observações (opcional)
7. **Confirmar:** Resgate
8. **Verificar:** 
   - Código de retirada gerado
   - Novo saldo atualizado
   - Prêmio removido da lista de disponíveis

---

## 🔐 Regras de Negócio

### ✅ Resgate Permitido quando:
- Cliente existe e está ativo
- Prêmio existe e está ativo
- `saldo_pontos >= preco_em_pontos`
- `estoque > 0` (se controle de estoque estiver ativo)

### ❌ Resgate Bloqueado quando:
- Cliente não encontrado
- Prêmio inativo
- Pontos insuficientes
- Estoque zerado
- Prêmio não existe

### 🎯 Comportamento do Botão "Resgatar Agora":
```javascript
// O botão SÓ aparece se:
resultado.premios_disponiveis.includes(premio)

// Que significa:
saldo_pontos >= premio.preco_em_pontos
```

---

## 📁 Arquivos Principais

### Frontend:
- **Consulta Pública:** `frontend/app/consultar-pontos/page.js`
- **Gerenciamento (Dashboard):** `frontend/app/(dashboard)/pontos/page.js`
- **API Client:** `frontend/lib/api.js`

### Backend:
- **Rotas de Prêmios:** `backend/app/routers/premios.py`
- **Modelos:** `backend/prisma/schema.prisma`
- **Main:** `backend/app/main.py`

---

## 🐛 Troubleshooting

### "Botão Resgatar Agora não aparece"
**Causa:** Cliente tem 0 pontos ou pontos insuficientes
**Solução:** Injetar pontos usando o script `inject_points.sql`

### "Erro ao resgatar prêmio"
**Possíveis causas:**
1. Backend não está rodando
2. Banco de dados não está acessível
3. Prêmio foi desativado
4. Estoque zerado

**Verificar:**
```bash
docker ps  # Verificar containers rodando
docker logs <backend_container>  # Ver logs do backend
```

### "Saldo não atualiza após resgate"
**Causa:** Frontend não recarregou os dados
**Solução:** Sistema já faz reload automático, mas pode dar F5 na página

---

## 📊 Fluxograma Visual

```
┌─────────────────┐
│ Cliente acessa  │
│ /consultar-     │
│ pontos          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Insere CPF/CNPJ │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ API consulta    │─────▶│ Retorna:     │
│ saldo + prêmios │      │ - Saldo      │
└─────────────────┘      │ - Disponíveis│
                         │ - Próximos   │
                         └──────┬───────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Prêmios Disponíveis?  │
                    └───────┬───────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                  SIM              NÃO
                    │               │
                    ▼               ▼
         ┌──────────────────┐  ┌─────────────┐
         │ Botão "Resgatar  │  │ Apenas      │
         │ Agora" VISÍVEL   │  │ visualização│
         └────────┬─────────┘  └─────────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ Cliente clica    │
         │ em Resgatar      │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ Modal de         │
         │ Confirmação      │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ Cliente confirma │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ API processa     │
         │ resgate:         │
         │ - Debita pontos  │
         │ - Cria registro  │
         │ - Gera código    │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ Tela de Sucesso  │
         │ com código de    │
         │ retirada         │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ Dados recarregam │
         │ automaticamente  │
         └──────────────────┘
```

---

## 🎯 Próximas Melhorias

- [ ] Notificação por email/SMS com código de retirada
- [ ] QR Code para validação na recepção
- [ ] Histórico de resgates do cliente
- [ ] Sistema de avaliação de prêmios
- [ ] Prêmios com validade/expiração
- [ ] Programa de cashback em pontos

---

**Última atualização:** Janeiro 2026
**Versão:** 1.0
