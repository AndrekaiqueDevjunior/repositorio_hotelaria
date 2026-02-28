# Auditoria de Segurança - Sistema de Pontos
**Data:** 26/01/2026  
**Sistema:** Hotel Real Cabo Frio - Programa de Fidelidade

---

## 🔴 VULNERABILIDADES CRÍTICAS IDENTIFICADAS

### 1. **RACE CONDITION - Resgate Simultâneo de Prêmios**
**Severidade:** CRÍTICA  
**Arquivo:** `backend/app/repositories/premio_repo.py:96-175`

**Problema:**
```python
async def resgatar(self, premio_id: int, cliente_id: int, funcionario_id: int):
    # 1. Busca saldo (linha 107-111)
    saldo_data = await pontos_repo.get_saldo(cliente_id)
    saldo_atual = saldo_data.get("saldo", 0)
    
    # 2. Verifica se tem saldo (linha 114-115)
    if saldo_atual < custo:
        return {"success": False, "error": "Saldo insuficiente"}
    
    # ⚠️ VULNERABILIDADE: Entre a verificação e o débito, 
    # outra requisição pode usar os mesmos pontos!
    
    # 3. Debita pontos (linha 118-145)
    result = await pontos_repo.criar_transacao_pontos(...)
```

**Cenário de Ataque:**
1. Cliente tem 100 pontos
2. Prêmio custa 100 pontos
3. Cliente faz 2 requisições simultâneas para resgatar o mesmo prêmio
4. Ambas verificam saldo (100 >= 100) ✅
5. Ambas debitam 100 pontos
6. Cliente fica com -100 pontos e recebe 2 prêmios!

**Impacto:** Cliente pode resgatar múltiplos prêmios com saldo insuficiente.

---

### 2. **RACE CONDITION - Ajuste de Pontos**
**Severidade:** CRÍTICA  
**Arquivo:** `backend/app/repositories/pontos_repo.py:48-103`

**Problema:**
```python
async def ajustar_pontos(self, request: AjustarPontosRequest, funcionario_id: int):
    # 1. Busca saldo atual (linha 55-65)
    usuario_pontos = await self.db.usuariopontos.find_first(...)
    saldo_anterior = usuario_pontos.saldo
    
    # 2. Calcula novo saldo (linha 68)
    novo_saldo = saldo_anterior + request.pontos
    
    # ⚠️ VULNERABILIDADE: Sem lock/transação atômica
    
    # 3. Atualiza saldo (linha 78-81)
    await self.db.usuariopontos.update(...)
```

**Cenário de Ataque:**
1. Saldo atual: 50 pontos
2. Requisição A: +10 pontos (lê 50, calcula 60)
3. Requisição B: +20 pontos (lê 50, calcula 70)
4. Requisição A salva: 60 pontos
5. Requisição B salva: 70 pontos
6. **Resultado:** Cliente tem 70 pontos (deveria ter 80!)

**Impacto:** Perda de pontos em operações concorrentes.

---

### 3. **Falta de Validação de Valores Negativos**
**Severidade:** ALTA  
**Arquivo:** `backend/app/repositories/pontos_repo.py:165-232`

**Problema:**
```python
async def criar_transacao_pontos(
    self, cliente_id: int, pontos: int, tipo: str, origem: str, ...
):
    # ⚠️ Aceita qualquer valor de 'pontos', inclusive negativos extremos
    saldo_posterior = saldo_anterior + pontos
    
    # Validação fraca (linha 201-202)
    if saldo_posterior < 0:
        raise ValueError("Saldo insuficiente")
```

**Cenário de Ataque:**
1. Atacante envia `pontos = -999999`
2. Se `saldo_anterior = 1000000`, passa na validação
3. Cliente perde todos os pontos de uma vez

**Impacto:** Débitos massivos não autorizados.

---

### 4. **Limite de Ajuste Manual Insuficiente**
**Severidade:** MÉDIA  
**Arquivo:** `backend/app/api/v1/pontos_routes.py:196-201`

**Problema:**
```python
# Validação: limite de ±4 pontos
if abs(request.pontos) > 4:
    raise HTTPException(status_code=400, detail="Ajuste manual limitado a ±4 pontos")
```

**Cenário de Ataque:**
1. Funcionário mal-intencionado faz 1000 ajustes de +4 pontos
2. Cliente recebe 4000 pontos fraudulentos
3. Rate limit de 20/min permite 80 pontos/min = 4800 pontos/hora

**Impacto:** Acúmulo fraudulento através de múltiplos ajustes pequenos.

---

### 5. **Falta de Auditoria em Operações Críticas**
**Severidade:** MÉDIA  
**Arquivo:** `backend/app/repositories/premio_repo.py:161-166`

**Problema:**
```python
# Atualizar estoque (se aplicável)
if premio.estoque is not None:
    await self.db.premio.update(
        where={"id": premio_id},
        data={"estoque": premio.estoque - 1}
    )
```

**Vulnerabilidades:**
- Sem verificação se estoque já é 0
- Sem log de quem alterou o estoque
- Possível estoque negativo

---

### 6. **Resgate de Prêmio Sem Autenticação (Público)**
**Severidade:** ALTA  
**Arquivo:** `backend/app/api/v1/premios_routes.py:132-187`

**Problema:**
```python
@router.post("/resgatar-publico", response_model=dict)
async def resgatar_premio_publico(
    request: ResgatePremioPublicoRequest,
    repo: PremioRepository = Depends(get_premio_repo),
    _rate_limit: None = Depends(rate_limit_strict)
):
    # ⚠️ Qualquer pessoa pode resgatar prêmios com apenas CPF/CNPJ
    documento_limpo = ''.join(filter(str.isdigit, request.cliente_documento))
```

**Cenário de Ataque:**
1. Atacante descobre CPF de cliente com muitos pontos
2. Faz requisição pública para resgatar prêmios
3. Cliente perde pontos sem autorização

**Impacto:** Roubo de pontos através de dados pessoais vazados.

---

### 7. **Consulta Pública Expõe Dados Sensíveis**
**Severidade:** MÉDIA  
**Arquivo:** `backend/app/api/v1/pontos_routes.py:313-373`

**Problema:**
```python
@router.get("/consultar/{documento}", response_model=dict)
async def consultar_pontos_publico(documento: str, ...):
    # ⚠️ Retorna saldo e histórico completo sem autenticação
    return {
        "cliente": {"nome": cliente.get('nome_completo'), "documento": documento_limpo},
        "saldo": saldo_data.get('saldo', 0),
        "historico": historico_data.get('transacoes', [])
    }
```

**Impacto:** Vazamento de informações financeiras (saldo, transações).

---

## 🛡️ CORREÇÕES RECOMENDADAS

### 1. **Implementar Transações Atômicas com Lock**
```python
async def resgatar(self, premio_id: int, cliente_id: int, funcionario_id: int):
    async with self.db.tx() as transaction:
        # Lock pessimista no registro de pontos
        usuario_pontos = await transaction.usuariopontos.find_first(
            where={"clienteId": cliente_id},
            # PostgreSQL: SELECT ... FOR UPDATE
        )
        
        if usuario_pontos.saldo < custo:
            raise HTTPException(status_code=400, detail="Saldo insuficiente")
        
        # Operações dentro da transação
        # Se qualquer operação falhar, rollback automático
```

### 2. **Validar Limites de Pontos por Transação**
```python
# Constantes de segurança
MAX_PONTOS_POR_TRANSACAO = 1000
MIN_PONTOS_POR_TRANSACAO = -1000

async def criar_transacao_pontos(self, cliente_id: int, pontos: int, ...):
    # Validação de limites
    if abs(pontos) > MAX_PONTOS_POR_TRANSACAO:
        raise ValueError(f"Transação limitada a ±{MAX_PONTOS_POR_TRANSACAO} pontos")
    
    if pontos == 0:
        raise ValueError("Transação de 0 pontos não permitida")
```

### 3. **Adicionar Auditoria Completa**
```python
# Criar tabela de auditoria
model AuditoriaOperacao {
  id            Int      @id @default(autoincrement())
  operacao      String   // "RESGATE_PREMIO", "AJUSTE_PONTOS", etc
  usuarioId     Int?
  clienteId     Int?
  dadosAntes    Json?
  dadosDepois   Json?
  ipOrigem      String?
  userAgent     String?
  sucesso       Boolean
  erro          String?
  createdAt     DateTime @default(now())
}
```

### 4. **Implementar 2FA para Resgates Públicos**
```python
@router.post("/resgatar-publico", response_model=dict)
async def resgatar_premio_publico(
    request: ResgatePremioPublicoRequest,
    codigo_verificacao: str,  # ← Código enviado por SMS/Email
    ...
):
    # Validar código de verificação antes de prosseguir
    if not await validar_codigo_2fa(request.cliente_documento, codigo_verificacao):
        raise HTTPException(status_code=401, detail="Código de verificação inválido")
```

### 5. **Limitar Ajustes Diários por Funcionário**
```python
# Adicionar verificação
ajustes_hoje = await self.db.transacaopontos.count(
    where={
        "funcionarioId": funcionario_id,
        "tipo": "AJUSTE",
        "createdAt": {"gte": datetime.now().replace(hour=0, minute=0, second=0)}
    }
)

if ajustes_hoje >= 50:  # Limite diário
    raise HTTPException(
        status_code=429,
        detail="Limite diário de ajustes atingido. Contate o supervisor."
    )
```

### 6. **Verificar Estoque Antes de Resgate**
```python
# Verificação atômica de estoque
premio = await self.db.premio.find_unique(where={"id": premio_id})

if premio.estoque is not None and premio.estoque <= 0:
    raise HTTPException(status_code=400, detail="Prêmio sem estoque disponível")

# Atualizar com verificação
await self.db.premio.update(
    where={
        "id": premio_id,
        "estoque": {"gt": 0}  # ← Só atualiza se estoque > 0
    },
    data={"estoque": {"decrement": 1}}
)
```

### 7. **Adicionar Logs de Segurança**
```python
import logging

security_logger = logging.getLogger("security")

async def resgatar_premio_publico(...):
    security_logger.warning(
        f"Resgate público tentado - Cliente: {request.cliente_documento}, "
        f"Prêmio: {request.premio_id}, IP: {request.client.host}"
    )
```

---

## 📊 PRIORIZAÇÃO DE CORREÇÕES

| Prioridade | Vulnerabilidade | Esforço | Impacto |
|------------|----------------|---------|---------|
| 🔴 **P0** | Race Condition - Resgate | Alto | Crítico |
| 🔴 **P0** | Race Condition - Ajuste | Alto | Crítico |
| 🟠 **P1** | Resgate Público sem 2FA | Médio | Alto |
| 🟠 **P1** | Validação de Valores | Baixo | Alto |
| 🟡 **P2** | Limite de Ajustes | Baixo | Médio |
| 🟡 **P2** | Auditoria | Médio | Médio |
| 🟢 **P3** | Consulta Pública | Baixo | Baixo |

---

## 🧪 TESTES DE SEGURANÇA RECOMENDADOS

### Teste 1: Race Condition em Resgate
```python
import asyncio
import httpx

async def test_race_condition_resgate():
    """Tenta resgatar o mesmo prêmio simultaneamente"""
    cliente_id = 1
    premio_id = 1
    
    async with httpx.AsyncClient() as client:
        # Fazer 10 requisições simultâneas
        tasks = [
            client.post(f"/api/v1/premios/resgatar", json={
                "cliente_id": cliente_id,
                "premio_id": premio_id
            })
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar quantas foram bem-sucedidas
        sucessos = sum(1 for r in responses if r.status_code == 200)
        
        # Deve ter apenas 1 sucesso (se saldo permite apenas 1 resgate)
        assert sucessos == 1, f"FALHA: {sucessos} resgates simultâneos permitidos!"
```

### Teste 2: Valores Negativos Extremos
```python
async def test_valores_negativos():
    """Tenta criar transação com valores extremos"""
    test_cases = [
        -999999,  # Valor muito negativo
        -1,       # Valor negativo pequeno
        0,        # Zero
        999999,   # Valor muito positivo
    ]
    
    for pontos in test_cases:
        try:
            result = await pontos_repo.criar_transacao_pontos(
                cliente_id=1,
                pontos=pontos,
                tipo="AJUSTE",
                origem="TESTE"
            )
            print(f"⚠️ VULNERABILIDADE: Aceita {pontos} pontos!")
        except ValueError as e:
            print(f"✅ Bloqueado: {pontos} pontos - {e}")
```

### Teste 3: Múltiplos Ajustes Pequenos
```python
async def test_multiplos_ajustes():
    """Tenta fazer múltiplos ajustes pequenos para burlar limite"""
    for i in range(100):
        try:
            await client.post("/api/v1/pontos/ajustes", json={
                "cliente_id": 1,
                "pontos": 4,  # Máximo permitido
                "motivo": f"Ajuste {i}"
            })
        except Exception as e:
            print(f"Bloqueado no ajuste {i}: {e}")
            break
    
    # Verificar saldo final
    saldo = await pontos_repo.get_saldo(1)
    print(f"Saldo final após {i} ajustes: {saldo['saldo']} pontos")
```

---

## 📝 CONCLUSÃO

O sistema de pontos apresenta **7 vulnerabilidades**, sendo **2 críticas** relacionadas a race conditions que podem resultar em:
- Perda de pontos
- Resgate fraudulento de prêmios
- Manipulação de saldo

**Recomendação imediata:** Implementar transações atômicas com locks pessimistas antes de colocar o sistema em produção.

---

**Auditor:** Cascade AI  
**Revisão:** Pendente  
**Status:** 🔴 AÇÃO REQUERIDA
