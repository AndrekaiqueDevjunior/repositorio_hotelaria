# 📋 **GUIA DE APLICAÇÃO DA MIGRATION**

## ⚠️ **IMPORTANTE: LEIA ANTES DE EXECUTAR**

Esta migration modifica a estrutura do banco de dados do sistema de pontos. É **OBRIGATÓRIO** fazer backup antes de aplicar.

---

## 🔧 **PRÉ-REQUISITOS**

- PostgreSQL instalado
- Acesso ao banco de dados como usuário com permissões DDL
- Backup recente do banco de dados
- Sistema parado (recomendado)

---

## 📋 **PASSO A PASSO**

### **1. Fazer Backup** ✅

#### **Opção A: Usando o script automático (Linux/Mac)**
```bash
cd backend/migrations
chmod +x backup_pontos.sh
./backup_pontos.sh
```

#### **Opção B: Manualmente**
```bash
# Backup completo
pg_dump -h localhost -p 5432 -U postgres -d hotel_cabo_frio > backup_antes_migration.sql

# Comprimir
gzip backup_antes_migration.sql
```

#### **Opção C: Windows**
```powershell
# Abrir PowerShell como Administrador
cd backend\migrations

# Fazer backup
pg_dump -h localhost -p 5432 -U postgres -d hotel_cabo_frio -F p -f backup_antes_migration.sql
```

---

### **2. Parar o Sistema (Recomendado)** ✅

```bash
# Parar backend
cd backend
# Ctrl+C no terminal onde está rodando

# Parar frontend
cd frontend
# Ctrl+C no terminal onde está rodando
```

---

### **3. Aplicar Migration** ✅

#### **Opção A: Script automático (Linux/Mac)**
```bash
cd backend/migrations
chmod +x aplicar_migration_pontos.sh
./aplicar_migration_pontos.sh
```

#### **Opção B: Script automático (Windows)**
```powershell
cd backend\migrations
powershell -ExecutionPolicy Bypass -File .\aplicar_migration_pontos.ps1
```

#### **Opção C: Manualmente**
```bash
# Linux/Mac
psql -h localhost -p 5432 -U postgres -d hotel_cabo_frio -f 002_corrigir_sistema_pontos.sql

# Windows
psql -h localhost -p 5432 -U postgres -d hotel_cabo_frio -f 002_corrigir_sistema_pontos.sql
```

---

### **4. Verificar Resultado** ✅

A migration deve exibir algo como:

```
NOTICE: Validação OK: Todas as transações têm cliente_id
NOTICE: ========================================
NOTICE: MIGRATION CONCLUÍDA COM SUCESSO!
NOTICE: ========================================
NOTICE: Total de transações: 42
NOTICE: Transações com reserva: 18
NOTICE: Transações com funcionário: 5
NOTICE: ========================================
COMMIT
```

---

### **5. Atualizar Schema do Prisma** ✅

```bash
cd backend

# Gerar cliente Prisma com novo schema
npx prisma generate

# OU usar Prisma migrate (se preferir)
npx prisma migrate dev --name add_pontos_relationships --skip-seed
```

---

### **6. Reiniciar Sistema** ✅

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## ✅ **VALIDAÇÃO PÓS-MIGRATION**

### **1. Verificar Estrutura**
```sql
-- Conectar ao banco
psql -h localhost -U postgres -d hotel_cabo_frio

-- Verificar colunas adicionadas
\d transacoes_pontos

-- Deve mostrar:
-- - cliente_id (integer, NOT NULL)
-- - funcionario_id (integer, nullable)
-- - reserva_id (integer, nullable)
-- - saldo_anterior (integer, nullable)
-- - saldo_posterior (integer, nullable)

-- Verificar foreign keys
\d+ transacoes_pontos

-- Verificar índices
\di transacoes_pontos*
```

### **2. Verificar Dados**
```sql
-- Todas as transações devem ter cliente_id
SELECT COUNT(*) as total,
       COUNT(cliente_id) as com_cliente_id
FROM transacoes_pontos;
-- total deve ser igual a com_cliente_id

-- Verificar transações com relacionamentos
SELECT 
    COUNT(*) as total,
    COUNT(reserva_id) as com_reserva,
    COUNT(funcionario_id) as com_funcionario
FROM transacoes_pontos;
```

### **3. Testar Frontend**
1. Acessar `http://localhost:3000/pontos`
2. Clicar em "Histórico"
3. Verificar se aparecem as novas colunas:
   - ✅ Tipo
   - ✅ Reserva (com link clicável)
   - ✅ Ajustado Por
   - ✅ Saldo Anterior
   - ✅ Saldo Posterior

---

## 🔄 **ROLLBACK (Em caso de problemas)**

Se algo der errado:

### **Opção 1: Restaurar backup**
```bash
# Descomprimir backup
gunzip backup_antes_migration.sql.gz

# Restaurar
psql -h localhost -U postgres -d hotel_cabo_frio < backup_antes_migration.sql
```

### **Opção 2: Rollback SQL (se backup não disponível)**
Executar o script de rollback que está no final do arquivo `002_corrigir_sistema_pontos.sql`

---

## 📊 **O QUE A MIGRATION FAZ**

1. ✅ Cria ENUMs `TipoTransacaoPontos` e `OrigemTransacaoPontos`
2. ✅ Adiciona campos:
   - `cliente_id` (relacionamento direto)
   - `funcionario_id` (rastreabilidade)
   - `saldo_anterior` (auditoria)
   - `saldo_posterior` (auditoria)
3. ✅ Preenche `cliente_id` baseado em `usuario_id` existente
4. ✅ Cria foreign keys para `clientes`, `funcionarios`, `reservas`
5. ✅ Cria índices para performance
6. ✅ Atualiza valores antigos para novos ENUMs
7. ✅ Valida integridade dos dados

---

## 🚨 **TROUBLESHOOTING**

### **Erro: "relation already exists"**
- Causa: Migration já foi aplicada antes
- Solução: Verificar se o banco já tem as colunas novas

### **Erro: "column cliente_id does not exist"**
- Causa: Migration não foi aplicada ainda
- Solução: Aplicar a migration

### **Erro: "permission denied"**
- Causa: Usuário sem permissões DDL
- Solução: Usar usuário com permissões (ex: postgres)

### **Transações sem cliente_id**
- Causa: Dados corrompidos ou usuarios_pontos deletados
- Solução: Investigar e corrigir dados antes de re-executar

---

## 📞 **SUPORTE**

Em caso de dúvidas ou problemas:
1. Verificar logs do PostgreSQL
2. Verificar logs do backend (FastAPI)
3. Consultar documentação em `ANALISE_RELACIONAMENTO_PONTOS.md`

---

## ✅ **CHECKLIST**

Antes de aplicar:
- [ ] Backup do banco criado
- [ ] Sistema parado
- [ ] Acesso ao banco confirmado

Após aplicar:
- [ ] Migration executada sem erros
- [ ] Schema Prisma atualizado (`npx prisma generate`)
- [ ] Sistema reiniciado
- [ ] Frontend testado
- [ ] Histórico de pontos exibindo novas colunas
- [ ] Transações com reserva_id vinculadas

---

**Criado em:** 21/12/2024  
**Versão da Migration:** 002
**Status:** ✅ Pronto para aplicação

