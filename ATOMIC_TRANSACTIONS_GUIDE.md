# Guia de Transações Atômicas - Sistema de Pontos

## 🎯 Objetivo

Eliminar completamente as vulnerabilidades de **race condition** no sistema de pontos através de transações atômicas com lock pessimista.

---

## 🔒 O Que São Transações Atômicas?

Uma transação atômica garante que um conjunto de operações seja executado como uma **unidade indivisível**:
- **Tudo ou nada:** Todas as operações são commitadas juntas, ou todas são revertidas (rollback)
- **Isolamento:** Outras transações não veem estados intermediários
- **Lock pessimista:** `SELECT FOR UPDATE` trava registros durante a transação

---

## 📊 Comparação: Antes vs Depois

### ❌ **ANTES (Vulnerável a Race Condition)**

```python
# pontos_repo.py - VULNERÁVEL
async def ajustar_pontos(self, request, funcionario_id):
    # 1. Busca saldo (SEM LOCK)
    usuario_pontos = await self.db.usuariopontos.find_first(
        where={"clienteId": request.cliente_id}
    )
    saldo_anterior = usuario_pontos.saldo
    
    # ⚠️ PROBLEMA: Outra requisição pode modificar o saldo aqui!
    
    # 2. Calcula novo saldo
    novo_saldo = saldo_anterior + request.pontos
    
    # 3. Atualiza saldo
    await self.db.usuariopontos.update(...)
    
    # 4. Cria transação
    await self.db.transacaopontos.create(...)
```

**Cenário de ataque:**
1. Requisição A lê saldo: 100 pontos
2. Requisição B lê saldo: 100 pontos (ainda não foi atualizado)
3. Requisição A adiciona +10: saldo = 110
4. Requisição B adiciona +20: saldo = 120 (deveria ser 130!)
5. **Resultado:** 10 pontos perdidos!

---

### ✅ **DEPOIS (Protegido com Transação Atômica)**

```python
# pontos_repo_atomic.py - SEGURO
async def ajustar_pontos_atomic(self, request, funcionario_id):
    # TRANSAÇÃO ATÔMICA
    async with self.db.tx() as transaction:
        # 1. Busca saldo COM LOCK (SELECT FOR UPDATE)
        usuario_pontos_raw = await transaction.query_raw(
            """
            SELECT * FROM usuario_pontos 
            WHERE cliente_id = $1 
            FOR UPDATE
            """,
            request.cliente_id
        )
        
        # ✅ LOCK ATIVO: Outras requisições esperam aqui!
        
        # 2. Calcula novo saldo
        novo_saldo = saldo_anterior + request.pontos
        
        # 3. Atualiza saldo (dentro da transação)
        await transaction.execute_raw(...)
        
        # 4. Cria transação (dentro da mesma transação)
        await transaction.transacaopontos.create(...)
        
        # 5. COMMIT AUTOMÁTICO ao sair do bloco
        # Se qualquer operação falhar, ROLLBACK automático
```

**Proteção:**
1. Requisição A adquire LOCK no registro
2. Requisição B tenta ler → **ESPERA** até A terminar
3. Requisição A adiciona +10: saldo = 110, COMMIT
4. Requisição B agora lê saldo atualizado: 110
5. Requisição B adiciona +20: saldo = 130
6. **Resultado:** 130 pontos (correto!)

---

## 🔧 Implementações Disponíveis

### 1. **PontosRepositoryAtomic**
**Arquivo:** `backend/app/repositories/pontos_repo_atomic.py`

**Métodos protegidos:**
- `ajustar_pontos_atomic()` - Ajuste manual de pontos
- `criar_transacao_pontos_atomic()` - Criar transação genérica

**Uso:**
```python
from app.repositories.pontos_repo_atomic import PontosRepositoryAtomic

db = get_db()
repo = PontosRepositoryAtomic(db)

# Ajuste atômico
result = await repo.ajustar_pontos_atomic(
    request=AjustarPontosRequest(
        cliente_id=1,
        pontos=10,
        motivo="Bônus de aniversário"
    ),
    funcionario_id=5
)
```

### 2. **PremioRepositoryAtomic**
**Arquivo:** `backend/app/repositories/premio_repo_atomic.py`

**Métodos protegidos:**
- `resgatar_atomic()` - Resgate de prêmio com lock em prêmio e pontos

**Uso:**
```python
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic

db = get_db()
repo = PremioRepositoryAtomic(db)

# Resgate atômico
result = await repo.resgatar_atomic(
    premio_id=1,
    cliente_id=10,
    funcionario_id=5
)
```

---

## 🚀 Guia de Migração

### **Passo 1: Atualizar Rotas de Pontos**

**Arquivo:** `backend/app/api/v1/pontos_routes.py`

```python
# ANTES
from app.repositories.pontos_repo import PontosRepository

@router.post("/ajustes", response_model=TransacaoResponse)
async def criar_ajuste_pontos(request, current_user, ...):
    db = get_db()
    repo = PontosRepository(db)
    return await repo.ajustar_pontos(request, funcionario_id=current_user.id)
```

```python
# DEPOIS
from app.repositories.pontos_repo_atomic import PontosRepositoryAtomic

@router.post("/ajustes", response_model=TransacaoResponse)
async def criar_ajuste_pontos(request, current_user, ...):
    db = get_db()
    repo = PontosRepositoryAtomic(db)  # ← Usar versão atômica
    return await repo.ajustar_pontos_atomic(request, funcionario_id=current_user.id)
```

### **Passo 2: Atualizar Rotas de Prêmios**

**Arquivo:** `backend/app/api/v1/premios_routes.py`

```python
# ANTES
from app.repositories.premio_repo import PremioRepository

@router.post("/resgatar", response_model=ResgatePremioResponse)
async def resgatar_premio(request, current_user, ...):
    db = get_db()
    repo = PremioRepository(db)
    return await repo.resgatar(...)
```

```python
# DEPOIS
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic

@router.post("/resgatar", response_model=ResgatePremioResponse)
async def resgatar_premio(request, current_user, ...):
    db = get_db()
    repo = PremioRepositoryAtomic(db)  # ← Usar versão atômica
    return await repo.resgatar_atomic(...)  # ← Método atômico
```

### **Passo 3: Atualizar Serviços**

Se houver serviços que usam os repositórios diretamente:

```python
# backend/app/services/pontos_service.py

# ANTES
from app.repositories.pontos_repo import PontosRepository

class PontosService:
    def __init__(self):
        self.repo = PontosRepository(get_db())
```

```python
# DEPOIS
from app.repositories.pontos_repo_atomic import PontosRepositoryAtomic

class PontosService:
    def __init__(self):
        self.repo = PontosRepositoryAtomic(get_db())  # ← Versão atômica
```

---

## 🧪 Testes de Validação

### **Teste 1: Race Condition em Ajuste**

```python
import asyncio
import httpx

async def test_race_condition_ajuste():
    """Testar se transações atômicas previnem race condition"""
    cliente_id = 1
    
    # Zerar saldo
    await reset_saldo(cliente_id, 0)
    
    # Fazer 10 ajustes simultâneos de +10 pontos
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post("/api/v1/pontos/ajustes", json={
                "cliente_id": cliente_id,
                "pontos": 10,
                "motivo": f"Teste {i}"
            })
            for i in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
    
    # Verificar saldo final
    saldo_final = await get_saldo(cliente_id)
    
    # Com transações atômicas, deve ser exatamente 100
    assert saldo_final == 100, f"Race condition detectada! Saldo: {saldo_final}"
    print("✅ Transações atômicas funcionando corretamente!")
```

### **Teste 2: Race Condition em Resgate**

```python
async def test_race_condition_resgate():
    """Testar se apenas 1 resgate é permitido quando há saldo para 1"""
    cliente_id = 1
    premio_id = 1  # Prêmio que custa 100 pontos
    
    # Dar exatamente 100 pontos ao cliente
    await set_saldo(cliente_id, 100)
    
    # Tentar resgatar 10 vezes simultaneamente
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post("/api/v1/premios/resgatar", json={
                "cliente_id": cliente_id,
                "premio_id": premio_id
            })
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Contar sucessos
    sucessos = sum(1 for r in responses if r.status_code == 200)
    
    # Deve ter apenas 1 sucesso
    assert sucessos == 1, f"Race condition! {sucessos} resgates permitidos"
    print("✅ Lock atômico no resgate funcionando!")
```

---

## 📈 Benefícios das Transações Atômicas

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Race Conditions** | ❌ Vulnerável | ✅ Eliminadas |
| **Consistência de Dados** | ⚠️ Possível inconsistência | ✅ Garantida |
| **Saldo Negativo** | ⚠️ Possível | ✅ Impossível |
| **Estoque Negativo** | ⚠️ Possível | ✅ Impossível |
| **Auditoria** | ⚠️ Parcial | ✅ Completa (logs) |
| **Performance** | 🟢 Rápido | 🟡 Ligeiramente mais lento* |

*O overhead de transações é mínimo (< 5ms) e vale a pena pela segurança.

---

## ⚠️ Considerações Importantes

### **1. Deadlocks**
Transações podem causar deadlocks se não forem bem projetadas.

**Prevenção:**
- Sempre adquirir locks na mesma ordem
- Manter transações curtas
- Usar timeout adequado

### **2. Performance**
Locks bloqueiam outros processos.

**Otimização:**
- Minimizar operações dentro da transação
- Fazer validações ANTES da transação
- Usar índices nos campos de lock

### **3. Compatibilidade**
Requer PostgreSQL (ou banco que suporte `SELECT FOR UPDATE`).

**Alternativas:**
- MySQL: `SELECT ... FOR UPDATE`
- SQLite: Não suporta (usar locks em nível de aplicação)

---

## 🔍 Monitoramento

### **Logs de Segurança**

As transações atômicas geram logs detalhados:

```python
security_logger.info(
    f"Ajuste atômico realizado - Cliente: {cliente_id}, "
    f"Pontos: {pontos:+d}, Saldo: {saldo_anterior} → {novo_saldo}"
)
```

**Verificar logs:**
```bash
docker logs hotel_backend | grep "atômico"
```

### **Métricas Recomendadas**

1. **Tempo de transação:** Deve ser < 50ms
2. **Taxa de rollback:** Deve ser < 1%
3. **Deadlocks:** Deve ser 0
4. **Locks esperando:** Monitorar fila de espera

---

## 📚 Referências

- [PostgreSQL - SELECT FOR UPDATE](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
- [Prisma - Transactions](https://www.prisma.io/docs/concepts/components/prisma-client/transactions)
- [ACID Properties](https://en.wikipedia.org/wiki/ACID)

---

## ✅ Checklist de Migração

- [ ] Backup do banco de dados
- [ ] Atualizar `pontos_routes.py` para usar `PontosRepositoryAtomic`
- [ ] Atualizar `premios_routes.py` para usar `PremioRepositoryAtomic`
- [ ] Executar testes de race condition
- [ ] Monitorar logs de segurança
- [ ] Validar performance (< 50ms por transação)
- [ ] Testar em ambiente de staging
- [ ] Deploy em produção
- [ ] Monitorar por 24h

---

**Status:** ✅ Implementação completa  
**Prioridade:** 🔴 P0 - Crítico  
**Impacto:** Elimina vulnerabilidades de race condition  
**Esforço:** Médio (2-4 horas de migração + testes)
