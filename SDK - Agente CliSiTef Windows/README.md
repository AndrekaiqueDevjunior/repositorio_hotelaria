# TEF Agente Service - Integração CliSiTef

Este serviço fornece uma API REST para integração com o CliSiTef (Sistema de Transferência Eletrônica de Fundos) da Software Express.

## Pré-requisitos

- Node.js 16+
- SDK CliSiTef instalado
- Windows (o CliSiTef é específico para Windows)

## Instalação

1. Instalar dependências:
```bash
npm install
```

2. Configurar variáveis de ambiente (opcional):
```bash
# Porta do serviço (padrão: 9999)
set TEF_PORT=9999

# Caminho para o executável agenteCliSiTef.exe
set CLISITEF_PATH=C:\caminho\para\agenteCliSiTef.exe
```

## Executar

```bash
npm start
```

Para desenvolvimento:
```bash
npm run dev
```

## API Endpoints

### POST /pagamento
Inicia um pagamento TEF.

**Request Body:**
```json
{
  "valor": 15000,        // Valor em centavos (R$ 150,00)
  "reserva_id": 123,     // ID da reserva
  "tipo": "venda"        // Tipo de transação
}
```

**Response:**
```json
{
  "success": true,
  "aprovado": true,
  "autorizacao": "AUT123456",
  "nsu": "NSU789012",
  "mensagem": "Pagamento TEF aprovado - R$ 150.00"
}
```

### GET /consulta/:nsu
Consulta o status de um pagamento.

**Response:**
```json
{
  "success": true,
  "status": "APROVADO",
  "autorizacao": "AUT123456",
  "mensagem": "Pagamento aprovado"
}
```

### POST /cancelamento/:nsu
Cancela um pagamento.

**Response:**
```json
{
  "success": true,
  "mensagem": "Cancelamento realizado com sucesso"
}
```

### GET /health
Health check do serviço.

## Integração com o Sistema Hoteleiro

No sistema hoteleiro (backend), configure a variável de ambiente:

```bash
TEF_AGENTE_URL=http://localhost:9999
```

## Implementação Real do CliSiTef

Atualmente, o serviço simula as transações. Para implementar a integração real:

1. Estudar a documentação do CliSiTef
2. Implementar as chamadas para `agenteCliSiTef.exe` com os parâmetros corretos
3. Tratar os códigos de retorno e mensagens de erro
4. Implementar o fluxo completo de venda, consulta e cancelamento

## Arquivos de Configuração

- `agenteclisitef.ini`: Configurações do agente
- `CliSiTef.ini`: Configurações do CliSiTef
- `Cheque.txt`: Configurações de consulta de cheques (renomear para `.ini` se necessário)

## Logs

Os logs são salvos em `logs/` e também exibidos no console.

## Suporte

Para dúvidas sobre o CliSiTef, consulte a documentação da Software Express.