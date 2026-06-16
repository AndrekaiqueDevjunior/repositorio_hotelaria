# Jornada Real - Skills para Spec Driven e Integração

Guia prático para remover mocks e integrar com o backend real.

> Para qualquer implementação nova, comece pelo contrato em `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md` e use esta página como playbook prático. O índice operacional das skills do projeto fica em `SKILLS.md`.

---

## 0. Skill: Spec Driven Development Jornada Real

### Objetivo
Implementar cada funcionalidade da Jornada Real a partir de contrato, testes e atualização explícita de status.

### Quando usar
Use antes de qualquer alteração ligada aos itens `JR-01` a `JR-11` da checklist.

### Fluxo

1. Abrir `JORNADA_REAL_FEATURES_CHECKLIST.md`.
2. Identificar o item (`JR-01` a `JR-11`).
3. Abrir `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md`.
4. Confirmar endpoints, payloads, validações, efeitos colaterais e testes mínimos.
5. Implementar backend primeiro quando houver regra de negócio.
6. Integrar frontend somente com contrato pronto ou mock explicitamente marcado.
7. Testar.
8. Atualizar checklist com `✅`, `🟡` ou `❌`.

### Mapa rápido

| ID | Checklist | Skill/Área |
|---|---|---|
| JR-01 | Cupom Amigo | Backend pontos/cupom + WhatsApp | ok
| JR-02 | Benefícios dos Níveis | Backend pontos | ok
| JR-03 | Barras de Progresso | Skill #1 + endpoint loyalty | ok
| JR-04 | Aviso Prêmio Próximo | Backend notificações + Twilio ✅ |
| JR-05 | Msg Pós Check-out | Backend checkout + Twilio ✅ |
| JR-06 | Som Check-out | Backend alertas ✅ + frontend dashboard |
| JR-07 | Invalidar Códigos | Backend ciclo de vida ✅ |
| JR-08 | Remover Suítes Reservadas | Backend disponibilidade + `/reservar` |
| JR-09 | Gerador de Cupons | Backend/admin cupons ✅ |
| JR-10 | Confirmação Check-in Admin | Backend check-in ✅ + Twilio ✅ + painel recepção ✅ |
| JR-11 | Autenticar Cadastro | Backend OTP ✅ + `/reservar` ✅ | funcionando 

### Regra de pronto
Só marque `✅` quando o contrato do spec estiver atendido e testado. Se existir implementação equivalente, mas faltar endpoint, metadata, dedupe, rate limit ou tela final, mantenha `🟡`.

---

## 1. Skill: Integrar Consulta de Pontos

### Objetivo
Fazer `/consultar-pontos` buscar dados reais do backend em vez de usar `currentPoints = 72` hardcoded.

### Arquivo
`/frontend/app/consultar-pontos/page.js`

### Implementação

#### 1.1 Importar hook de useEffect
```javascript
import { useEffect, useMemo, useState } from 'react'
```
✅ Já existe.

#### 1.2 Remover constantes hardcoded (linha 21-25)
**ANTES:**
```javascript
const currentPoints = 72
const nextLevelPoints = 90
const missingToLevel = nextLevelPoints - currentPoints
const levelProgress = Math.min((currentPoints / nextLevelPoints) * 100, 100)
const rewardProgress = 66
```

**DEPOIS:**
```javascript
// Deletar as 5 linhas acima

export default function ConsultarPontos() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [apiRewards, setApiRewards] = useState([])
  const [isLoadingRewards, setIsLoadingRewards] = useState(true)
  // NOVO:
  const [loyaltyData, setLoyaltyData] = useState(null)
  const [isLoadingLoyalty, setIsLoadingLoyalty] = useState(true)
  const [loyaltyError, setLoyaltyError] = useState(null)
  
  const cpf = searchParams.get('cpf')
  
  // NOVO: useEffect para buscar loyalty
  useEffect(() => {
    if (!cpf) return
    
    let isMounted = true
    
    const loadLoyalty = async () => {
      try {
        const response = await api.get(`/customers/${cpf}/loyalty`)
        if (isMounted) {
          setLoyaltyData(response.data)
          setLoyaltyError(null)
        }
      } catch (error) {
        if (isMounted) {
          setLoyaltyError(error.response?.data?.message || 'CPF não encontrado')
          setLoyaltyData(null)
        }
      } finally {
        if (isMounted) {
          setIsLoadingLoyalty(false)
        }
      }
    }
    
    loadLoyalty()
    
    return () => {
      isMounted = false
    }
  }, [cpf])
  
  // Calcular valores dinâmicos a partir dos dados
  const currentPoints = loyaltyData?.redeemable_points ?? 0
  const nextLevelPoints = 90 // TODO: buscar da API
  const missingToLevel = nextLevelPoints - currentPoints
  const levelProgress = Math.min((currentPoints / nextLevelPoints) * 100, 100)
  const rewardProgress = useMemo(() => {
    if (!loyaltyData?.redeemable_points) return 0
    // Lógica: quantos prêmios já resgatou vs. quantos pode fazer
    // Por enquanto, assume 2/3 = 66%
    return 66 // TODO: calcular de verdade
  }, [loyaltyData])
```

#### 1.3 Atualizar exibição de nome (linha 165-167)
**ANTES:**
```javascript
<p>Você está quase lá 👑</p>
<h1>
  Hóspede Real <Crown size={18} strokeWidth={1.6} />
</h1>
```

**DEPOIS:**
```javascript
<p>Você está quase lá 👑</p>
<h1>
  {loyaltyData?.customer_name || 'Hóspede Real'} <Crown size={18} strokeWidth={1.6} />
</h1>
```

#### 1.4 Exibir estado de carregamento/erro
**ADICIONAR após o logo** (linha ~162):
```javascript
{isLoadingLoyalty && (
  <div className="loading-indicator">
    <p>Carregando seus dados...</p>
  </div>
)}

{loyaltyError && (
  <div className="error-indicator">
    <p>❌ {loyaltyError}</p>
    <button onClick={() => router.push('/consultar')}>
      Voltar e tentar novamente
    </button>
  </div>
)}

{loyaltyData && !isLoadingLoyalty && (
  {/* Resto do conteúdo */}
)}
```

#### 1.5 Atualizar o URL de próximo nível (linha 101)
**ANTES:**
```javascript
const levelPageUrl = `/nivel_jornada_real?pontos=${currentPoints}&anterior=${currentPoints}${cpf ? `&cpf=${cpf}` : ''}`
```

**DEPOIS:**
```javascript
const levelPageUrl = useMemo(() => {
  if (!loyaltyData) return '/'
  return `/nivel_jornada_real?pontos=${loyaltyData.redeemable_points}&anterior=${loyaltyData.lifetime_points}${cpf ? `&cpf=${cpf}` : ''}`
}, [loyaltyData, cpf])
```

### Testes
```bash
# 1. Verificar se GET é chamado ao carregar página com ?cpf=
curl http://localhost:3000/consultar-pontos?cpf=11144477735

# 2. Confirmar que endpoint backend existe
curl http://localhost:8000/api/v1/customers/11144477735/loyalty
# Deveria retornar: { customer_name, redeemable_points, ... }
```

---

## 2. Skill: Integrar Resgate de Prêmios

### Objetivo
Fazer `resgate_dos_premios` chamar `POST /rewards/redeem` em vez de gerar código localmente.

### Arquivo
`/frontend/app/resgate_dos_premios/page.js`

### Implementação

#### 2.1 Remover geração local de código (linha 243-246)
**ANTES:**
```javascript
const handleRedeem = (prize) => {
  setRedeemedPrize({
    ...prize,
    code: `REAL -${Date.now().toString().slice(-6)}`,
  })
}
```

**DEPOIS:**
```javascript
const [isRedeeming, setIsRedeeming] = useState(false)
const [redeemError, setRedeemError] = useState(null)
const { user } = useAuth() // Deve ter customer_id do usuário

const handleRedeem = async (prize) => {
  if (!user?.id) {
    setRedeemError('Você precisa estar autenticado')
    return
  }
  
  setIsRedeeming(true)
  setRedeemError(null)
  
  try {
    const response = await api.post('/rewards/redeem', {
      reward_id: prize.id,
      customer_id: user.id,
    })
    
    setRedeemedPrize({
      ...prize,
      code: response.data.redemption_code,
      expiresAt: response.data.expires_at,
      status: response.data.status,
    })
  } catch (error) {
    const message = error.response?.data?.message || 'Erro ao resgatar prêmio'
    setRedeemError(message)
    
    // Tratamento de erros específicos
    if (error.response?.status === 402) {
      setRedeemError('Saldo insuficiente de pontos')
    } else if (error.response?.status === 409) {
      setRedeemError('Prêmio sem estoque disponível')
    }
  } finally {
    setIsRedeeming(false)
  }
}
```

#### 2.2 Atualizar modal de sucesso (linha 359-426)
**ANTES:**
```javascript
<p className="modal-message">
  Sua experiência <strong>{redeemedPrize.name}</strong> foi confirmada!
</p>

// ...

<div className="code-display">
  {redeemedPrize.code}
</div>

<p>
  Seu código é pessoal, intransferível e válido por 30 dias.
</p>
```

**DEPOIS:**
```javascript
<p className="modal-message">
  Sua experiência <strong>{redeemedPrize.name}</strong> foi confirmada!
</p>

// ...

<div className="code-display">
  {redeemedPrize.code}
</div>

<p>
  Seu código é pessoal, intransferível e válido até{' '}
  <strong>
    {new Date(redeemedPrize.expiresAt).toLocaleDateString('pt-BR')}
  </strong>
  .
</p>

{redeemedPrize.status === 'active' && (
  <small style={{ color: '#90EE90' }}>✓ Código ativo</small>
)}
```

#### 2.3 Exibir erro se houver (nova seção antes do modal)
**ADICIONAR:**
```javascript
{redeemError && (
  <div className="redeem-error-toast">
    <p>❌ {redeemError}</p>
    <button onClick={() => setRedeemError(null)}>Fechar</button>
  </div>
)}
```

#### 2.4 Desabilitar botão durante requisição
**Linha ~331 do handleRedeem:**
```javascript
<button 
  type="button" 
  className="confirm-button" 
  onClick={() => handleRedeem(prize)}
  disabled={isRedeeming}
>
  {isRedeeming ? 'Processando...' : 'Confirmar Resgate'}
</button>
```

### Testes
```bash
# 1. Verificar resposta do endpoint
curl -X POST http://localhost:8000/api/v1/rewards/redeem \
  -H "Content-Type: application/json" \
  -d '{
    "reward_id": "reward-001",
    "customer_id": "user-uuid"
  }'
# Deveria retornar: { redemption_code, expires_at, ... }

# 2. Testar erro de saldo insuficiente
# Cria customer com 0 pontos, tenta resgatar
curl -X POST http://localhost:8000/api/v1/rewards/redeem \
  -H "Content-Type: application/json" \
  -d '{
    "reward_id": "reward-001",
    "customer_id": "poor-customer"
  }'
# Deveria retornar 402 (Payment Required) ou 400
```

---

## 3. Skill: Integrar Consulta de CPF

### Objetivo
Validar que CPF existe no sistema antes de redirecionar para consulta.

### Arquivo
`/frontend/app/consultar/page.js`

### Implementação

#### 3.1 Validar CPF no backend (linha ~33-43)
**ANTES:**
```javascript
const handleSubmit = (event) => {
  event.preventDefault()
  
  const cpfLimpo = cpf.replace(/\D/g, '')
  if (cpfLimpo.length !== 11) {
    setError('Digite um CPF válido.')
    return
  }
  
  setError('')
  router.push(`/consultar-pontos?cpf=${cpfLimpo}`)
}
```

**DEPOIS:**
```javascript
const [isValidating, setIsValidating] = useState(false)

const handleSubmit = async (event) => {
  event.preventDefault()
  
  const cpfLimpo = cpf.replace(/\D/g, '')
  if (cpfLimpo.length !== 11) {
    setError('Digite um CPF válido.')
    return
  }
  
  setIsValidating(true)
  setError('')
  
  try {
    // Valida existência do customer
    await api.get(`/customers/${cpfLimpo}`)
    
    // Se OK, redireciona
    router.push(`/consultar-pontos?cpf=${cpfLimpo}`)
  } catch (error) {
    if (error.response?.status === 404) {
      setError('CPF não encontrado no sistema.')
    } else {
      setError('Erro ao validar CPF. Tente novamente.')
    }
  } finally {
    setIsValidating(false)
  }
}
```

#### 3.2 Desabilitar input durante validação
```javascript
<input
  id="cpf"
  type="text"
  // ... outros props
  disabled={isValidating}
/>

<button type="submit" className="submit-button" disabled={isValidating}>
  <span>{isValidating ? 'Validando...' : 'Ver minha jornada'}</span>
  {/* ... */}
</button>
```

### Testes
```bash
# CPF válido e existe
curl http://localhost:8000/api/v1/customers/11144477735

# CPF válido mas não existe
curl http://localhost:8000/api/v1/customers/00000000000
# Deveria retornar 404
```

---

## 4. Skill: Calcular Níveis Dinâmicos

### Objetivo
Buscar `loyalty_levels` do backend em vez de hardcodá-los.

### Arquivo
`/frontend/app/nivel_jornada_real/page.js`

### Implementação

#### 4.1 Remover hardcode de níveis
**ANTES:**
```javascript
const levels = [
  { name: 'Essência', level: 'Nível 1', range: '0 a 50 pontos', ... },
  { name: 'Experiência', level: 'Nível 2', range: '50 a 90 pontos', ... },
  { name: 'Real', level: 'Nível máximo', range: '90+ pontos', ... },
]
```

**DEPOIS:**
```javascript
const [levels, setLevels] = useState([])
const [isLoadingLevels, setIsLoadingLevels] = useState(true)

useEffect(() => {
  let isMounted = true
  
  const loadLevels = async () => {
    try {
      const response = await api.get('/loyalty-levels')
      if (isMounted) {
        setLevels(response.data)
      }
    } catch (error) {
      console.error('Erro ao carregar níveis:', error)
      // Fallback para dados locais
      setLevels([
        { name: 'Essência', min_points: 0, range: '0 a 50 pontos' },
        { name: 'Experiência', min_points: 50, range: '50 a 90 pontos' },
        { name: 'Real', min_points: 90, range: '90+ pontos' },
      ])
    } finally {
      if (isMounted) {
        setIsLoadingLevels(false)
      }
    }
  }
  
  loadLevels()
  
  return () => {
    isMounted = false
  }
}, [])
```

---

## 5. Skill: Tratar Erros de API

### Pattern Padrão para Toda Integração

```javascript
// Error boundary wrapper
const fetchWithErrorHandling = async (fn, fallbackMessage) => {
  try {
    return await fn()
  } catch (error) {
    const message = error.response?.data?.message || fallbackMessage
    
    // Log para debug
    console.error(`[API Error] ${error.config?.url}:`, error)
    
    // Toast de erro
    if (typeof window !== 'undefined') {
      toast.error(message)
    }
    
    // Re-throw para caller lidar se quiser
    throw error
  }
}

// Uso
const handleSomething = async () => {
  try {
    await fetchWithErrorHandling(
      () => api.get('/endpoint'),
      'Erro ao carregar dados'
    )
  } catch (error) {
    // Tratamento específico se necessário
  }
}
```

---

## 6. Checklist de Implementação

### Fase 1: Pontos
- [ ] Remover `const currentPoints = 72`
- [ ] Adicionar `useEffect` para `GET /customers/{cpf}/loyalty`
- [ ] Exibir nome real do cliente
- [ ] Calcular progresso dinamicamente
- [ ] Testar com CPF válido e inválido

### Fase 2: Resgate
- [ ] Remover geração local de código
- [ ] Implementar `POST /rewards/redeem`
- [ ] Tratar erros (saldo, estoque)
- [ ] Exibir data de expiração real
- [ ] Testar resgate com saldos diferentes

### Fase 3: Validação CPF
- [ ] Adicionar `GET /customers/{cpf}` antes de redirecionar
- [ ] Mostrar erro se CPF não existe
- [ ] Desabilitar botão durante validação

### Fase 4: Níveis
- [ ] Buscar `GET /loyalty-levels`
- [ ] Usar dados reais em vez de hardcode
- [ ] Manter fallback para erros

### Fase 5: Testes E2E
- [ ] Fluxo completo: CPF → Consulta → Resgate
- [ ] Teste com dados reais do banco
- [ ] Teste com erros de API
- [ ] Teste com conectividade perdida

---

## 7. Debugging Tips

### Verificar resposta da API
```javascript
// No console do navegador
const response = await api.get('/customers/11144477735/loyalty')
console.log(response.data)
```

### Ver requisições da API
```javascript
// Chrome DevTools → Network tab
// Filtrar por XHR/Fetch
// Verificar:
// - Method (GET/POST)
// - Status (200/400/404/402)
// - Response body
// - Headers (Authorization)
```

### Simular erro de API
```javascript
// No handlers do `handleRedeem`:
try {
  // ...
  throw new Error('TEST ERROR')
} catch (error) {
  // Seus handlers de erro rodam
}
```

---

## 8. Referências

- Spec central: `JORNADA_REAL_SPEC_DRIVEN_DEVELOPMENT.md`
- Índice de skills: `SKILLS.md`
- Schema Prisma: `/docs/jornada-real-backend-db.md`
- Mocks identificados: `JORNADA_REAL_MOCKS_SCHEMA.md`
- API Docs: `http://localhost:8000/docs` (Swagger se backend expor)
