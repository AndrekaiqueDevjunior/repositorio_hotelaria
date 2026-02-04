# Guia - Botão WhatsApp para Resgates

## 📱 Solução Simples - Sem Integração

Implementei um botão que abre o WhatsApp com a mensagem já formatada. **Não precisa de configuração**, funciona imediatamente!

---

## 🎯 Como Funciona

1. Cliente clica em "Resgatar via WhatsApp"
2. WhatsApp abre automaticamente com mensagem pronta
3. Cliente envia a mensagem para você: **+55 11 96802-9600**
4. Você recebe e combina a entrega

---

## 📦 Componentes Criados

### **1. WhatsAppButton.js**
Botão reutilizável que pode ser usado em qualquer lugar.

**Uso básico:**
```jsx
import WhatsAppButton from '@/components/WhatsAppButton'

<WhatsAppButton
  clienteNome="João Silva"
  premioNome="Voucher R$ 50"
  pontosUsados={500}
  codigoResgate="RES-000123"
  clienteEndereco="Rua Exemplo, 123 - Cabo Frio/RJ"
/>
```

### **2. PremioWhatsAppExample.js**
Exemplo completo de como integrar o botão em uma página de prêmios.

---

## 💬 Mensagem Enviada

Quando o cliente clicar no botão, o WhatsApp abrirá com esta mensagem:

```
Olá, me chamo João Silva, acumulei 500 pontos e resgatei o prêmio Voucher R$ 50.

Eu moro em Rua Exemplo, 123 - Cabo Frio/RJ.

O código do resgate é RES-000123.

Gostaria de saber como vai ser feita a entrega do item. Enviam via Correios?
```

---

## 🔧 Como Integrar

### **Opção 1: Usar o Exemplo Completo**

```jsx
// Em qualquer página de prêmios
import PremioWhatsAppExample from '@/components/PremioWhatsAppExample'

export default function PremiosPage() {
  const premio = {
    nome: "Voucher R$ 50",
    descricao: "Vale-compra de R$ 50,00",
    preco_em_pontos: 500
  }
  
  const cliente = {
    nome: "João Silva",
    endereco: "Rua Exemplo, 123 - Cabo Frio/RJ"
  }
  
  return (
    <div>
      <PremioWhatsAppExample premio={premio} cliente={cliente} />
    </div>
  )
}
```

### **Opção 2: Usar Apenas o Botão**

```jsx
// Adicionar em modal, card, etc
import WhatsAppButton from '@/components/WhatsAppButton'

<WhatsAppButton
  clienteNome={user.nome}
  premioNome={premio.nome}
  pontosUsados={premio.preco_em_pontos}
  codigoResgate={`RES-${resgate.id}`}
  clienteEndereco={user.endereco}
/>
```

---

## 🎨 Personalização

### **Mudar o Número WhatsApp**

Edite o arquivo `WhatsAppButton.js` linha 14:

```jsx
// Seu número atual
const numeroWhatsApp = '5511968029600'

// Para mudar, altere para:
const numeroWhatsApp = '5521987654321' // Exemplo
```

### **Customizar Mensagem**

Edite o arquivo `WhatsAppButton.js` linhas 17-23:

```jsx
const mensagem = `Olá, me chamo ${clienteNome}...`
```

### **Mudar Estilo do Botão**

```jsx
<WhatsAppButton
  className="w-full text-lg py-4" // Botão grande
  // ou
  className="btn-sm" // Botão pequeno
  // ou
  className="bg-blue-600 hover:bg-blue-700" // Cor diferente
/>
```

---

## 📱 Compatibilidade

### **Desktop**
- ✅ Abre WhatsApp Web
- ✅ Se não tiver WhatsApp Web, pede para instalar

### **Mobile**
- ✅ Abre app WhatsApp diretamente
- ✅ Funciona em iOS e Android

---

## 🚀 Vantagens

| Aspecto | Status |
|---------|--------|
| **Configuração** | ✅ Zero (funciona imediatamente) |
| **Custo** | ✅ Grátis (sem APIs pagas) |
| **Manutenção** | ✅ Nenhuma |
| **Complexidade** | ✅ Muito simples |
| **Funcionalidade** | ✅ Completa |

---

## 🔍 Exemplo Visual

```
┌─────────────────────────────────────┐
│  🎁 Voucher R$ 50,00                │
│  ⭐ 500 pontos                       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🎁 Resgatar Prêmio          │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 💬 Resgatar via WhatsApp        ││
│  │                                 ││
│  │ Clique para enviar mensagem     ││
│  │ automática com os detalhes      ││
│  │                                 ││
│  │ ┌─────────────────────────────┐ ││
│  │ │ 📱 Resgatar via WhatsApp    │ ││
│  │ └─────────────────────────────┘ ││
│  │                                 ││
│  │ 💬 Número: +55 11 96802-9600    ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

---

## ✅ Checklist

- [x] Componente WhatsAppButton criado
- [x] Exemplo de uso criado
- [x] Número configurado: +55 11 96802-9600
- [x] Mensagem formatada
- [x] Funciona sem configuração
- [ ] Integrar em página de prêmios (você escolhe onde)

---

## 📝 Próximos Passos

1. **Escolha onde adicionar o botão:**
   - Modal de confirmação de resgate
   - Página de detalhes do prêmio
   - Lista de prêmios disponíveis
   - Histórico de resgates

2. **Importe o componente:**
   ```jsx
   import WhatsAppButton from '@/components/WhatsAppButton'
   ```

3. **Adicione o botão:**
   ```jsx
   <WhatsAppButton
     clienteNome={cliente.nome}
     premioNome={premio.nome}
     pontosUsados={premio.pontos}
     codigoResgate={codigo}
     clienteEndereco={cliente.endereco}
   />
   ```

4. **Pronto!** Funciona imediatamente.

---

**Solução implementada!** ✅  
**Configuração necessária:** Nenhuma  
**Custo:** R$ 0,00  
**Complexidade:** Muito simples  

O botão está pronto para uso. Basta adicionar onde você quiser!
