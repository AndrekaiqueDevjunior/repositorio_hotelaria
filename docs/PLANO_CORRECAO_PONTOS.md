# 🚀 PLANO DE CORREÇÃO - SISTEMA DE PONTOS RP

## 📋 **SUMÁRIO EXECUTIVO**

**STATUS ATUAL**: 🚨 **SISTEMA COM MÚLTIPLOS BUGS CRÍTICOS**
**PRIORIDADE**: 🔥 **URGENTE** - Impacto direto na fidelização de clientes
**ESTIMATIVA**: 3-4 dias para implementação completa

---

## 🎯 **OBJETIVOS DA CORREÇÃO**

1. **Implementar cálculo correto** baseado em tipo de suíte + diárias
2. **Adicionar acúmulo de diárias** para evitar perda de pontos
3. **Corrigir modelo de dados** com campos faltantes
4. **Manter automação no checkout** (já existe)
5. **Implementar catálogo de resgates**

---

## 🔧 **PLANO DE IMPLEMENTAÇÃO**

### **FASE 1 - CORREÇÃO DA LÓGICA DE CÁLCULO** (Dia 1)

#### **1.1 Criar Novo Serviço de Pontos RP**
```python
# backend/app/services/pontos_rp_service.py
class PontosRPService:
    """Serviço para cálculo de pontos baseado em regras RP"""
    
    REGRAS_PONTOS = {
        'LUXO': 3,      # 3 RP a cada 2 diárias
        'MASTER': 4,    # 4 RP a cada 2 diárias  
        'REAL': 5,      # 5 RP a cada 2 diárias
        # 'DUPLA': 4     # 4 RP a cada 2 diárias (se implementado)
    }
    
    @staticmethod
    def calcular_pontos_por_suite(tipo_suite: str, num_diarias: int, diarias_pendentes: int = 0) -> Dict[str, int]:
        """
        Calcular pontos baseado em tipo de suíte e diárias
        
        Args:
            tipo_suite: Tipo da suíte
            num_diarias: Diárias da reserva atual
            diarias_pendentes: Diárias acumuladas de reservas anteriores
            
        Returns:
            {
                'pontos_gerados': int,
                'diarias_restantes': int,
                'blocos_completos': int
            }
        """
        total_diarias = num_diarias + diarias_pendentes
        blocos_completos = total_diarias // 2
        diarias_restantes = total_diarias % 2
        
        pontos_por_bloco = PontosRPService.REGRAS_PONTOS.get(tipo_suite.upper(), 0)
        pontos_gerados = blocos_completos * pontos_por_bloco
        
        return {
            'pontos_gerados': pontos_gerados,
            'diarias_restantes': diarias_restantes,
            'blocos_completos': blocos_completos
        }
```

#### **1.2 Atualizar Modelo de Dados**
```python
# backend/app/models/pontos_rp.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from app.db.base import Base

class ClienteRP(Base):
    __tablename__ = "clientes_rp"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True)
    saldo_rp = Column(Integer, default=0, nullable=False)
    diarias_pendentes_para_pontos = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class HistoricoRP(Base):
    __tablename__ = "historico_rp"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    tipo_suite = Column(String(50), nullable=False)
    num_diarias = Column(Integer, nullable=False)
    diarias_usadas_acumuladas = Column(Integer, nullable=False)
    pontos_gerados = Column(Integer, nullable=False)
    data = Column(DateTime(timezone=True), server_default=func.now())

class PremioRP(Base):
    __tablename__ = "premios_rp"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    rp_necessario = Column(Integer, nullable=False)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ResgateRP(Base):
    __tablename__ = "resgates_rp"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    premio_id = Column(Integer, ForeignKey("premios_rp.id"), nullable=False)
    rp_utilizados = Column(Integer, nullable=False)
    status = Column(String(20), default="SOLICITADO")  # SOLICITADO, ENTREGUE, CANCELADO
    data_solicitacao = Column(DateTime(timezone=True), server_default=func.now())
    data_entrega = Column(DateTime(timezone=True), nullable=True)
    observacoes = Column(Text, nullable=True)
```

#### **1.3 Migration do Banco**
```sql
-- backend/migrations/003_implementar_sistema_rp.sql
-- Criar tabela de clientes RP
CREATE TABLE IF NOT EXISTS clientes_rp (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER UNIQUE REFERENCES clientes(id),
    saldo_rp INTEGER DEFAULT 0,
    diarias_pendentes_para_pontos INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Criar tabela de histórico RP
CREATE TABLE IF NOT EXISTS historico_rp (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    reserva_id INTEGER REFERENCES reservas(id),
    tipo_suite VARCHAR(50) NOT NULL,
    num_diarias INTEGER NOT NULL,
    diarias_usadas_acumuladas INTEGER NOT NULL,
    pontos_gerados INTEGER NOT NULL,
    data TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar tabela de prêmios RP
CREATE TABLE IF NOT EXISTS premios_rp (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    rp_necessario INTEGER NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar tabela de resgates RP
CREATE TABLE IF NOT EXISTS resgates_rp (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    premio_id INTEGER REFERENCES premios_rp(id),
    rp_utilizados INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'SOLICITADO',
    data_solicitacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_entrega TIMESTAMP WITH TIME ZONE,
    observacoes TEXT
);

-- Inserir prêmios do catálogo
INSERT INTO premios_rp (nome, descricao, rp_necessario) VALUES
('1 diária em Suíte Luxo', 'Diária gratuita em Suíte Luxo', 20),
('Luminária com carregador', 'Luminária LED com porta USB', 25),
('Cafeteira', 'Cafeteira elétrica', 35),
('iPhone 16', 'iPhone 16 128GB', 100);

-- Migrar dados existentes
INSERT INTO clientes_rp (cliente_id, saldo_rp)
SELECT DISTINCT cliente_id, COALESCE(saldo_atual, 0)
FROM usuarios_pontos
ON CONFLICT (cliente_id) DO UPDATE SET
    saldo_rp = EXCLUDED.saldo_rp;
```

### **FASE 2 - CORREÇÃO DO CHECKOUT** (Dia 2)

#### **2.1 Atualizar Método de Checkout**
```python
# backend/app/repositories/hospedagem_repo.py
async def _creditar_pontos_checkout(self, reserva) -> None:
    """
    Creditar pontos de fidelidade RP após checkout
    NOVA REGRA: Baseado em tipo de suíte + diárias completas
    """
    from app.services.pontos_rp_service import PontosRPService
    from app.repositories.pontos_rp_repo import PontosRPRepository
    
    # Buscar cliente RP
    pontos_repo = PontosRPRepository(self.db)
    cliente_rp = await pontos_repo.get_cliente_rp(reserva.clienteId)
    
    if not cliente_rp:
        # Criar registro se não existir
        cliente_rp = await pontos_repo.criar_cliente_rp(reserva.clienteId)
    
    # Calcular pontos usando nova regra
    resultado = PontosRPService.calcular_pontos_por_suite(
        tipo_suite=reserva.tipoSuite,
        num_diarias=reserva.numDiarias or 0,
        diarias_pendentes=cliente_rp.diarias_pendentes_para_pontos
    )
    
    if resultado['pontos_gerados'] <= 0:
        # Atualizar apenas diárias pendentes
        await pontos_repo.atualizar_diarias_pendentes(
            reserva.clienteId, 
            resultado['diarias_restantes']
        )
        print(f"[CHECKOUT] Sem pontos gerados. {resultado['diarias_restantes']} diárias pendentes acumuladas")
        return
    
    # Verificar idempotência
    transacao_existente = await self.db.historicorp.find_first(
        where={
            "reservaId": reserva.id,
            "clienteId": reserva.clienteId
        }
    )
    
    if transacao_existente:
        print(f"[CHECKOUT] Pontos RP já creditados para reserva {reserva.id}")
        return
    
    # Creditar pontos
    await pontos_repo.creditar_pontos_rp(
        cliente_id=reserva.clienteId,
        reserva_id=reserva.id,
        tipo_suite=reserva.tipoSuite,
        num_diarias=reserva.numDiarias or 0,
        pontos_gerados=resultado['pontos_gerados'],
        diarias_usadas=resultado['blocos_completos'] * 2,
        diarias_restantes=resultado['diarias_restantes']
    )
    
    print(f"✅ Creditado {resultado['pontos_gerados']} RP para cliente {reserva.clienteId}")
    print(f"   Diárias usadas: {resultado['blocos_completos'] * 2}")
    print(f"   Diárias pendentes: {resultado['diarias_restantes']}")
```

#### **2.2 Criar Repository RP**
```python
# backend/app/repositories/pontos_rp_repo.py
class PontosRPRepository:
    def __init__(self, db):
        self.db = db
    
    async def get_cliente_rp(self, cliente_id: int):
        """Buscar registro RP do cliente"""
        return await self.db.clienterp.find_unique(
            where={"cliente_id": cliente_id},
            include={"historico": True, "resgates": True}
        )
    
    async def criar_cliente_rp(self, cliente_id: int):
        """Criar registro RP para cliente"""
        return await self.db.clienterp.create(
            data={
                "cliente_id": cliente_id,
                "saldo_rp": 0,
                "diarias_pendentes_para_pontos": 0
            }
        )
    
    async def creditar_pontos_rp(
        self,
        cliente_id: int,
        reserva_id: int,
        tipo_suite: str,
        num_diarias: int,
        pontos_gerados: int,
        diarias_usadas: int,
        diarias_restantes: int
    ):
        """Creditar pontos RP e atualizar saldos"""
        
        # Atualizar saldo do cliente
        await self.db.clienterp.update(
            where={"cliente_id": cliente_id},
            data={
                "saldo_rp": {"increment": pontos_gerados},
                "diarias_pendentes_para_pontos": diarias_restantes
            }
        )
        
        # Criar histórico
        await self.db.historicorp.create(
            data={
                "cliente_id": cliente_id,
                "reserva_id": reserva_id,
                "tipo_suite": tipo_suite,
                "num_diarias": num_diarias,
                "diarias_usadas_acumuladas": diarias_usadas,
                "pontos_gerados": pontos_gerados
            }
        )
        
        return {"success": True, "pontos_gerados": pontos_gerados}
    
    async def resgatar_premio(self, cliente_id: int, premio_id: int):
        """Processar resgate de prêmio"""
        cliente = await self.get_cliente_rp(cliente_id)
        premio = await self.db.premiorp.find_unique(where={"id": premio_id})
        
        if not cliente or not premio:
            raise ValueError("Cliente ou prêmio não encontrado")
        
        if cliente.saldo_rp < premio.rp_necessario:
            raise ValueError("Saldo insuficiente")
        
        # Debitar pontos
        await self.db.clienterp.update(
            where={"cliente_id": cliente_id},
            data={"saldo_rp": {"decrement": premio.rp_necessario}}
        )
        
        # Criar resgate
        resgate = await self.db.resgaterp.create(
            data={
                "cliente_id": cliente_id,
                "premio_id": premio_id,
                "rp_utilizados": premio.rp_necessario,
                "status": "SOLICITADO"
            }
        )
        
        return {"success": True, "resgate": resgate}
```

### **FASE 3 - API E FRONTEND** (Dia 3)

#### **3.1 Criar Rotas RP**
```python
# backend/app/api/v1/pontos_rp_routes.py
@router.get("/saldo-rp/{cliente_id}")
async def get_saldo_rp(cliente_id: int):
    """Obter saldo RP do cliente"""
    pontos_repo = PontosRPRepository(get_db())
    cliente = await pontos_repo.get_cliente_rp(cliente_id)
    
    if not cliente:
        return {"saldo_rp": 0, "diarias_pendentes": 0}
    
    return {
        "saldo_rp": cliente.saldo_rp,
        "diarias_pendentes": cliente.diarias_pendentes_para_pontos
    }

@router.get("/historico-rp/{cliente_id}")
async def get_historico_rp(cliente_id: int, limit: int = 20):
    """Obter histórico RP do cliente"""
    pontos_repo = PontosRPRepository(get_db())
    historico = await pontos_repo.get_historico_rp(cliente_id, limit)
    
    return {"historico": historico}

@router.get("/premios-rp")
async def get_premios_rp():
    """Listar prêmios disponíveis para resgate"""
    pontos_repo = PontosRPRepository(get_db())
    premios = await pontos_repo.get_premios_disponiveis()
    
    return {"premios": premios}

@router.post("/resgatar-rp")
async def resgatar_premio_rp(request: ResgateRPRequest):
    """Resgatar prêmio com pontos RP"""
    pontos_repo = PontosRPRepository(get_db())
    
    try:
        resultado = await pontos_repo.resgatar_premio(
            request.cliente_id,
            request.premio_id
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### **3.2 Atualizar Frontend**
```javascript
// frontend/app/(dashboard)/pontos/page.js
// Nova aba de resgates
const [premios, setPremios] = useState([])
const [resgates, setResgates] = useState([])

const loadPremios = async () => {
  try {
    const res = await api.get('/premios-rp')
    setPremios(res.data.premios)
  } catch (error) {
    console.error('Erro ao carregar prêmios:', error)
  }
}

const resgatarPremio = async (premioId) => {
  try {
    setLoading(true)
    const res = await api.post('/resgatar-rp', {
      cliente_id: clienteId,
      premio_id: premioId
    })
    
    if (res.data.success) {
      toast.success('🎉 Prêmio resgatado com sucesso!')
      loadSaldo()
      loadResgates()
    }
  } catch (error) {
    toast.error('❌ ' + (error.response?.data?.detail || 'Erro ao resgatar'))
  } finally {
    setLoading(false)
  }
}
```

### **FASE 4 - TESTES E VALIDAÇÃO** (Dia 4)

#### **4.1 Testes Automáticos**
```python
# backend/test_pontos_rp.py
async def test_calculo_pontos():
    """Testar cálculo de pontos por tipo de suíte"""
    
    # Teste 1: Suíte Luxo - 3 diárias
    resultado = PontosRPService.calcular_pontos_por_suite('LUXO', 3)
    assert resultado['pontos_gerados'] == 3  # 2 diárias = 3 RP
    assert resultado['diarias_restantes'] == 1  # 1 diária pendente
    
    # Teste 2: Suíte Real - 4 diárias
    resultado = PontosRPService.calcular_pontos_por_suite('REAL', 4)
    assert resultado['pontos_gerados'] == 10  # 4 diárias = 2 blocos * 5 RP
    assert resultado['diarias_restantes'] == 0
    
    # Teste 3: Acumulação de diárias
    resultado = PontosRPService.calcular_pontos_por_suite('MASTER', 2, 1)
    assert resultado['pontos_gerados'] == 8  # 3 diárias = 1 bloco * 4 RP
    assert resultado['diarias_restantes'] == 1

async def test_checkout_automatico():
    """Testar geração automática de pontos no checkout"""
    
    # Criar reserva de teste
    reserva = await criar_reserva_teste(
        tipo_suite='LUXO',
        num_diarias=3,
        cliente_id=1
    )
    
    # Simular checkout
    hospedagem_repo = HospedagemRepository(db)
    await hospedagem_repo.realizar_checkout(reserva.id, funcionario_id=1)
    
    # Verificar pontos creditados
    cliente_rp = await pontos_repo.get_cliente_rp(1)
    assert cliente_rp.saldo_rp == 3  # 2 diárias = 3 RP
    assert cliente_rp.diarias_pendentes_para_pontos == 1  # 1 diária pendente
```

#### **4.2 Testes Manuais**
1. **Cenário 1**: Cliente faz 1 diária em Suíte Luxo
   - Expected: 0 pontos, 1 diária pendente
   
2. **Cenário 2**: Cliente faz 3 diárias em Suíte Real
   - Expected: 5 pontos, 1 diária pendente
   
3. **Cenário 3**: Cliente com 1 diária pendente + 1 diária nova
   - Expected: 3 pontos (Suíte Luxo), 0 diárias pendentes

---

## 📊 **MÉTRICAS DE SUCESSO**

### **KPIs de Implementação:**
- ✅ **100%** dos checkouts gerando pontos automaticamente
- ✅ **0%** de perda de diárias no sistema
- ✅ **100%** dos cálculos seguindo regras RP
- ✅ **< 100ms** tempo de resposta da API

### **KPIs de Negócio:**
- 🎯 **+40%** taxa de fidelização em 3 meses
- 🎯 **+25%** diárias médias por cliente
- 🎯 **95%** satisfação com programa de pontos
- 🎯 **ROI positivo** em 6 meses

---

## 🚨 **RISCOS E MITIGAÇÃO**

### **Risco 1: Migração de Dados**
- **Problema**: Perda de pontos existentes
- **Mitigação**: Backup completo + migração incremental
- **Plano B**: Manter sistema antigo paralelo por 30 dias

### **Risco 2: Performance**
- **Problema**: Lentidão no cálculo de pontos
- **Mitigação**: Cache de saldos + cálculo assíncrono
- **Plano B**: Processamento em fila para checkouts em lote

### **Risco 3: Complexidade**
- **Problema**: Regras muito complexas
- **Mitigação**: Documentação completa + testes automatizados
- **Plano B**: Simplificar regras se necessário

---

## 📅 **CRONOGRAMA**

| Dia | Tarefa | Status |
|-----|--------|---------|
| **Dia 1** | Implementar lógica de cálculo + migração | ⏳ |
| **Dia 2** | Corrigir checkout + repositories | ⏳ |
| **Dia 3** | API + frontend | ⏳ |
| **Dia 4** | Testes + validação | ⏳ |
| **Dia 5** | Deploy + monitoramento | ⏳ |

---

## 🎯 **PRÓXIMOS PASSOS**

1. **Aprovação do plano** - Aguardar feedback do stakeholder
2. **Setup do ambiente** - Preparar branch de desenvolvimento
3. **Implementação Fase 1** - Começar pela lógica de cálculo
4. **Testes contínuos** - Validar cada fase antes de prosseguir
5. **Documentação** - Manter docs atualizadas
6. **Treinamento** - Capacitar equipe sobre novas regras

---

**STATUS**: 📋 **PLANO PRONTO PARA APROVAÇÃO E EXECUÇÃO**
