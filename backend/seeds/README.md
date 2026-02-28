# 🌱 Seeds - Dados Iniciais do Sistema

Esta pasta contém todos os scripts para popular o banco de dados com informações iniciais do Hotel Cabo Frio.

## 📁 Estrutura dos Seeds

### 👥 Usuários e Funcionários
- `seed_5_users.py` - Cria usuários administrativos iniciais
- `seed_clientes.py` - Popula com clientes de exemplo

### 🏨 Quartos e Tarifas  
- `seed_quartos.py` - Cria todos os quartos do hotel (50 quartos)
- `seed_quarto_standard.py` - Quartos padrão (se necessário)
- `seed_tarifas.py` - **PROBLEMA** (não funciona)
- `seed_tarifas_fix.py` - **PROBLEMA** (não funciona) 
- `seed_tarifas_simple.py` - ✅ **FUNCIONAL** - Cria tarifas via SQL direto

### 🎯 Sistema de Pontos e Prêmios
- `seed_pontos_regras.py` - ✅ **FUNCIONAL** - Regras de pontuação por tipo de suíte
- `seed_premios.py` - ✅ **FUNCIONAL** - Cria 10 prêmios resgatáveis

### 📊 Dados Completos
- `seed_demo_data.py` - ✅ **FUNCIONAL** - Cria cenário completo (clientes, reservas, pagamentos)

## 🚀 Como Executar

### Executar seeds individuais em desenvolvimento local:
```bash
cd backend
python seeds/seed_quartos.py
python seeds/seed_tarifas_simple.py
```

### Forçar um arquivo de ambiente seguro:
```bash
SEED_ENV_FILE=backend/.env.test python backend/seeds/seed_quartos.py
```

### Se realmente quiser rodar contra produção:
```bash
SEED_ALLOW_PROD=true python backend/seeds/seed_quartos.py
```

### Executar via Docker:
```bash
docker exec hotel_backend python seeds/nome_do_arquivo.py
```

### Executar na ordem recomendada:
```bash
# Opção 1: Executar todos de uma vez
docker exec hotel_backend python seeds/run_all_seeds.py

# Opção 2: Executar individualmente em dev local
python backend/seeds/seed_5_users.py
python backend/seeds/seed_clientes.py
python backend/seeds/seed_quartos.py
python backend/seeds/seed_tarifas_simple.py
python backend/seeds/seed_pontos_regras.py
python backend/seeds/seed_premios.py
python backend/seeds/seed_demo_data.py
```

## 📋 Status dos Seeds

| Seed | Status | Observações |
|------|--------|-------------|
| `seed_5_users.py` | ✅ OK | Funcionários admin |
| `seed_clientes.py` | ✅ OK | 3+ clientes |
| `seed_quartos.py` | ✅ OK | 50 quartos |
| `seed_tarifas_simple.py` | ✅ OK | 7 tarifas ativas |
| `seed_pontos_regras.py` | ✅ OK | 4 regras de pontos |
| `seed_premios.py` | ✅ OK | 10 prêmios |
| `seed_demo_data.py` | ✅ OK | Reservas + pagamentos |
| `seed_tarifas.py` | ❌ ERRO | Problema Prisma |
| `seed_tarifas_fix.py` | ❌ ERRO | Problema Prisma |

## 🔧 Problemas Conhecidos

### Tarifas com Prisma
Os seeds `seed_tarifas.py` e `seed_tarifas_fix.py` apresentam problemas com o modelo Prisma. 
**Solução:** Usar `seed_tarifas_simple.py` que executa SQL diretamente.

### Demo Data
O `seed_demo_data.py` pode apresentar erro no check-in se as reservas não estiverem com status correto. Isso é normal e não afeta a criação dos dados.

## 📊 Resumo dos Dados Criados

- **50 Quartos** em diferentes categorias
- **6+ Clientes** para testes  
- **3 Funcionários** (admins)
- **7 Tarifas** ativas por tipo de suíte
- **4 Regras** de pontuação Real Points
- **10 Prêmios** resgatáveis
- **2+ Reservas** de exemplo

## 🔄 Manutenção

Para resetar o banco:
1. Pare os containers Docker
2. Remova o volume do PostgreSQL: `docker volume rm app_hotel_cabo_frio_postgres_data`
3. Suba os containers novamente
4. Execute os seeds na ordem recomendada

---

**Última atualização:** 27/01/2026  
**Banco:** hotel_cabo_frio (PostgreSQL)
