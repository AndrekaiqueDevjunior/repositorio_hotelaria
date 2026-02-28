# Testes de Integração API - Hotel Cabo Frio

## Visão Geral

Suite completa de testes de integração que executa **requests HTTP reais** contra a API REST rodando em Docker, validando todos os endpoints principais.

## Arquivos Criados

- **`.env.test`** - Configuração de ambiente para testes
- **`.env.test.example`** - Template de configuração
- **`tests/http_client.py`** - Cliente HTTP com autenticação e retry logic
- **`tests/test_integration_api.py`** - Suite completa de testes
- **`run_integration_tests.ps1`** - Script PowerShell para executar testes

## Endpoints Testados

### ✅ Autenticação
- `POST /api/v1/auth/login` - Login com credenciais válidas
- `POST /api/v1/auth/login` - Login com credenciais inválidas (401/403)

### ✅ Clientes
- `GET /api/v1/clientes` - Listar todos
- `POST /api/v1/clientes` - Criar novo
- `GET /api/v1/clientes/{id}` - Obter por ID

### ✅ Quartos
- `GET /api/v1/quartos` - Listar todos
- `POST /api/v1/quartos` - Criar novo

### ✅ Reservas
- `GET /api/v1/reservas` - Listar todas
- `POST /api/v1/reservas` - Criar nova

### ✅ Pagamentos
- `GET /api/v1/pagamentos` - Listar todos
- `POST /api/v1/pagamentos` - Criar novo

### ✅ Pontos
- `GET /api/v1/pontos` - Listar transações
- `GET /api/v1/pontos/saldo/{cliente_id}` - Obter saldo
- `POST /api/v1/pontos` - Criar transação

### ✅ Dashboard
- `GET /api/v1/dashboard/stats` - Estatísticas do sistema

## Como Executar

### Opção 1: Script PowerShell (Recomendado)

```powershell
# Certifique-se que containers estão rodando
docker-compose up -d

# Execute o script
.\run_integration_tests.ps1
```

### Opção 2: Via Docker Compose (Manual)

```powershell
# Executar testes dentro do container backend
docker-compose exec backend pytest tests/test_integration_api.py -v

# Com mais detalhes
docker-compose exec backend pytest tests/test_integration_api.py -v -s

# Apenas um teste específico
docker-compose exec backend pytest tests/test_integration_api.py::TestAuth::test_login_success -v
```

### Opção 3: Localmente (se tiver Python configurado)

```powershell
cd backend
pytest tests/test_integration_api.py -v
```

## Configuração

Edite `.env.test` se necessário:

```env
BASE_URL=http://localhost:8080
AUTH_EMAIL=admin@hotelreal.com.br
AUTH_PASSWORD=admin123
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

## Fluxo de Testes

Os testes seguem um **fluxo encadeado** para garantir dependências:

1. **Login** → Obtém token de autenticação
2. **Criar Cliente** → Captura `cliente_id`
3. **Criar Quarto** → Captura `quarto_id`
4. **Criar Reserva** → Usa `cliente_id` + `quarto_id` → Captura `reserva_id`
5. **Criar Pagamento** → Usa `reserva_id` → Captura `pagamento_id`
6. **Criar Pontos** → Usa `cliente_id` e `reserva_id`
7. **Validar GETs** → Verifica que recursos criados são recuperáveis
8. **Dashboard** → Valida estatísticas

## Critérios de Sucesso

Para cada endpoint:
- ✅ Status code **2XX** (200/201/204)
- ✅ Content-Type **application/json** (quando aplicável)
- ✅ Body contém campos esperados
- ✅ Recursos criados via POST são recuperáveis via GET
- ✅ Validações de negócio retornam 400/422 apropriadamente

## Tratamento de Erros

### Retry Automático
- Status **502/503/504** → Retry com backoff exponencial
- Timeout de conexão → Retry até MAX_RETRIES
- Outros erros → Falha imediata

### Validações
- **422 Unprocessable Entity** → Skip com mensagem (campos obrigatórios)
- **400 Bad Request** → Skip com mensagem (regra de negócio)
- **401/403 Unauthorized** → Esperado em testes de auth inválida

## Relatório

Após execução, é gerado:

### Console Output
```
[POST] /api/v1/auth/login -> 200 (150ms)
[GET] /api/v1/clientes -> 200 (45ms)
[POST] /api/v1/clientes -> 201 (120ms)
...
```

### Arquivo `test_report.md`
Tabela completa com:
- Método HTTP
- Endpoint
- Status code
- Resultado (PASS/FAIL)
- Tempo de resposta
- Erros (se houver)

## Recursos

### Cliente HTTP (`http_client.py`)
- ✅ Autenticação automática com Bearer token
- ✅ Retry logic para falhas transitórias
- ✅ Logging de requests/responses
- ✅ Redação de dados sensíveis (senha, token)
- ✅ Timeout configurável
- ✅ Context manager para cleanup

### Dados de Teste
- ✅ Únicos por execução (timestamp + random)
- ✅ Evita colisões entre execuções
- ✅ Formato: `Cliente Teste 20260108-112345`

## Troubleshooting

### Backend não responde
```powershell
# Verificar logs
docker-compose logs backend

# Reiniciar containers
docker-compose restart backend
```

### Erro de autenticação
```powershell
# Verificar credenciais em .env.test
# Verificar se admin existe no banco
docker-compose exec backend python check_admin_password.py
```

### Testes falhando
```powershell
# Executar com mais detalhes
docker-compose exec backend pytest tests/test_integration_api.py -v -s --tb=long

# Executar apenas um teste
docker-compose exec backend pytest tests/test_integration_api.py::TestClientes::test_get_clientes -v
```

## Próximos Passos

Para expandir os testes:

1. **Adicionar testes de UPDATE/DELETE**
   - PUT/PATCH para atualização
   - DELETE para remoção

2. **Testes de validação negativa**
   - Campos obrigatórios faltando
   - Formatos inválidos
   - Regras de negócio

3. **Testes de performance**
   - Carga com múltiplos requests
   - Tempo de resposta médio

4. **Testes de segurança**
   - CORS headers
   - SQL injection
   - XSS prevention

## Observações

- ✅ **Sem mocks**: Todos os testes fazem HTTP real
- ✅ **Containerizado**: Roda dentro do Docker (isolamento)
- ✅ **Idempotente**: Dados únicos evitam conflitos
- ✅ **Robusto**: Retry automático para falhas transitórias
- ✅ **Documentado**: Relatório completo em Markdown
