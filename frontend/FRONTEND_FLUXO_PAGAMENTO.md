# Frontend: Fluxo de Pagamento com Comprovante

## 🎨 Componentes Criados/Atualizados

### 1. **StatusBadge.js** ✅ NOVO
Componente para exibir badges de status das reservas com cores e ícones.

**Localização**: `frontend/components/StatusBadge.js`

**Uso**:
```jsx
import StatusBadge from '@/components/StatusBadge'

<StatusBadge status="CHECKIN_LIBERADO" />
<StatusBadge status="EM_ANALISE" />
<StatusBadge status="PAGA_REJEITADA" />
```

**Estados suportados**:
- 🟡 `PENDENTE_PAGAMENTO` - Amarelo
- 📤 `AGUARDANDO_COMPROVANTE` - Laranja
- 🔍 `EM_ANALISE` - Azul
- ✅ `PAGA_APROVADA` - Verde
- ❌ `PAGA_REJEITADA` - Vermelho
- 🟢 `CHECKIN_LIBERADO` - Roxo
- 🏨 `CHECKIN_REALIZADO` - Índigo
- ✔️ `CHECKOUT_REALIZADO` - Cinza

---

### 2. **ModalEscolhaPagamento.js** ✅ NOVO
Modal para o cliente escolher a forma de pagamento.

**Localização**: `frontend/components/ModalEscolhaPagamento.js`

**Opções**:
1. **PIX** 📱 - Em desenvolvimento
2. **Cartão Online** 💳 - Em desenvolvimento  
3. **Pagamento no Balcão** 🏪 - ✅ Funcional

**Uso**:
```jsx
import ModalEscolhaPagamento from '@/components/ModalEscolhaPagamento'

const [showModalPagamento, setShowModalPagamento] = useState(false)

<ModalEscolhaPagamento
  reserva={reserva}
  onClose={() => setShowModalPagamento(false)}
  onSuccess={() => {
    // Atualizar lista de reservas
    carregarReservas()
  }}
/>
```

**Fluxo**:
1. Cliente escolhe "Pagamento no Balcão"
2. Modal abre automaticamente `UploadComprovanteModal`
3. Cliente faz upload do comprovante
4. Sistema muda status para `EM_ANALISE`

---

### 3. **UploadComprovanteModal.js** ✅ ATUALIZADO
Modal de upload de comprovante (já existia, foi atualizado).

**Mudanças**:
- ✅ Agora usa endpoint correto: `POST /reservas/{id}/comprovante`
- ✅ Envia `metodo_pagamento` em vez de `tipo_comprovante`
- ✅ Mensagens de sucesso atualizadas

**Endpoint usado**:
```javascript
POST /api/v1/reservas/${reserva.id}/comprovante

Body:
{
  "arquivo_base64": "...",
  "nome_arquivo": "comprovante.jpg",
  "metodo_pagamento": "PIX|DINHEIRO|DEBITO|CREDITO",
  "observacao": "Pago no débito"
}
```

---

## 🔄 Fluxo Completo (Frontend)

### Passo 1: Criar Reserva
```jsx
// Página: /reservar
const criarReserva = async () => {
  const response = await api.post('/reservas', dados)
  // Status inicial: PENDENTE_PAGAMENTO
}
```

### Passo 2: Escolher Pagamento
```jsx
// Após criar reserva, abrir modal
<ModalEscolhaPagamento
  reserva={novaReserva}
  onClose={...}
  onSuccess={...}
/>
```

### Passo 3: Upload de Comprovante (se escolher "Balcão")
```jsx
// Modal abre automaticamente
<UploadComprovanteModal
  reserva={reserva}
  pagamento={{ valor: reserva.valor_total }}
  onClose={...}
  onSuccess={...}
/>
```

### Passo 4: Exibir Status
```jsx
// Na lista de reservas
<StatusBadge status={reserva.status_reserva} />

// Exemplo de resultado:
// 🔍 Em Análise
```

### Passo 5: Admin Aprova (Página /comprovantes)
```jsx
// Já existe: frontend/app/(dashboard)/comprovantes/page.js
// Admin clica em "Aprovar"
// Backend muda status para: CHECKIN_LIBERADO
```

### Passo 6: Check-in Liberado
```jsx
// Botão de check-in só aparece se:
{reserva.status_reserva === 'CHECKIN_LIBERADO' && (
  <button onClick={fazerCheckin}>
    Fazer Check-in
  </button>
)}
```

---

## 📋 Exemplo de Implementação Completa

### Na Página de Reservas (`/reservas/page.js`):

```jsx
'use client'
import { useState } from 'react'
import StatusBadge from '@/components/StatusBadge'
import ModalEscolhaPagamento from '@/components/ModalEscolhaPagamento'

export default function ReservasPage() {
  const [reservas, setReservas] = useState([])
  const [reservaSelecionada, setReservaSelecionada] = useState(null)
  const [showModalPagamento, setShowModalPagamento] = useState(false)

  const handlePagar = (reserva) => {
    setReservaSelecionada(reserva)
    setShowModalPagamento(true)
  }

  const handleCheckin = async (reserva) => {
    // Validar status
    if (reserva.status_reserva !== 'CHECKIN_LIBERADO') {
      toast.error('Check-in não liberado. Aguarde aprovação do pagamento.')
      return
    }

    // Fazer check-in
    await api.post(`/checkin/${reserva.id}/realizar`, dados)
  }

  return (
    <div>
      {reservas.map(reserva => (
        <div key={reserva.id} className="card">
          <h3>Reserva #{reserva.codigo_reserva}</h3>
          
          {/* Badge de Status */}
          <StatusBadge status={reserva.status_reserva} />

          {/* Botões Condicionais */}
          {reserva.status_reserva === 'PENDENTE_PAGAMENTO' && (
            <button onClick={() => handlePagar(reserva)}>
              💰 Pagar Agora
            </button>
          )}

          {reserva.status_reserva === 'AGUARDANDO_COMPROVANTE' && (
            <button onClick={() => handlePagar(reserva)}>
              📤 Enviar Comprovante
            </button>
          )}

          {reserva.status_reserva === 'EM_ANALISE' && (
            <div className="alert alert-info">
              🔍 Comprovante em análise pelo administrador
            </div>
          )}

          {reserva.status_reserva === 'PAGA_REJEITADA' && (
            <div className="alert alert-danger">
              ❌ Comprovante rejeitado. Envie um novo.
              <button onClick={() => handlePagar(reserva)}>
                Reenviar Comprovante
              </button>
            </div>
          )}

          {reserva.status_reserva === 'CHECKIN_LIBERADO' && (
            <button onClick={() => handleCheckin(reserva)} className="btn-success">
              ✅ Fazer Check-in
            </button>
          )}

          {reserva.status_reserva === 'CHECKIN_REALIZADO' && (
            <div className="alert alert-success">
              🏨 Check-in realizado
            </div>
          )}
        </div>
      ))}

      {/* Modal de Pagamento */}
      {showModalPagamento && reservaSelecionada && (
        <ModalEscolhaPagamento
          reserva={reservaSelecionada}
          onClose={() => {
            setShowModalPagamento(false)
            setReservaSelecionada(null)
          }}
          onSuccess={() => {
            setShowModalPagamento(false)
            setReservaSelecionada(null)
            // Recarregar reservas
            carregarReservas()
          }}
        />
      )}
    </div>
  )
}
```

---

## 🎯 Páginas que Precisam Ser Atualizadas

### 1. **`/reservas/page.js`** (Lista de Reservas)
- ✅ Adicionar `<StatusBadge />`
- ✅ Adicionar botão "Pagar Agora" para status `PENDENTE_PAGAMENTO`
- ✅ Tornar botão de check-in condicional a `CHECKIN_LIBERADO`

### 2. **`/reservas/[id]/page.js`** (Detalhes da Reserva)
- ✅ Adicionar `<StatusBadge />`
- ✅ Adicionar histórico de mudanças de status
- ✅ Mostrar informações do comprovante se existir

### 3. **`/comprovantes/page.js`** (Admin - Já existe)
- ✅ Já funcional
- ⚠️ Melhorar visualização de imagens (zoom, fullscreen)

### 4. **`/reservar/page.js`** (Criar Nova Reserva)
- ✅ Após criar, abrir `ModalEscolhaPagamento` automaticamente

---

## 🔧 Configuração da API

Certifique-se de que o arquivo `lib/api.js` está configurado corretamente:

```javascript
// lib/api.js
import axios from 'axios'

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

---

## 📱 UX/UI Recomendações

### Cores dos Status (Tailwind)
```css
PENDENTE_PAGAMENTO:      bg-yellow-100 text-yellow-800
AGUARDANDO_COMPROVANTE:  bg-orange-100 text-orange-800
EM_ANALISE:              bg-blue-100 text-blue-800
PAGA_APROVADA:           bg-green-100 text-green-800
PAGA_REJEITADA:          bg-red-100 text-red-800
CHECKIN_LIBERADO:        bg-purple-100 text-purple-800
CHECKIN_REALIZADO:       bg-indigo-100 text-indigo-800
```

### Ícones
- ⏳ Aguardando
- 📤 Upload
- 🔍 Análise
- ✅ Aprovado
- ❌ Rejeitado
- 🟢 Liberado
- 🏨 Check-in
- ✔️ Finalizado

---

## 🚀 Próximos Passos

1. **Integração PIX** - Implementar fluxo de pagamento PIX
2. **Integração Cielo** - Implementar pagamento com cartão online
3. **Notificações em Tempo Real** - WebSocket para atualizar status
4. **Histórico de Status** - Timeline de mudanças de status
5. **Relatórios** - Dashboard de pagamentos e comprovantes

---

## ✅ Checklist de Implementação

- [x] Componente `StatusBadge`
- [x] Componente `ModalEscolhaPagamento`
- [x] Atualizar `UploadComprovanteModal`
- [ ] Atualizar página `/reservas`
- [ ] Atualizar página `/reservas/[id]`
- [ ] Melhorar página `/comprovantes` (zoom de imagens)
- [ ] Adicionar notificações em tempo real
- [ ] Testes E2E com Playwright

---

**Data**: 26/01/2026  
**Status**: Componentes Criados ✅  
**Próximo**: Integrar nas páginas existentes
