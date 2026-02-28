# Guia Completo de Testes Automatizados

## 📋 Visão Geral

O sistema possui dois tipos de testes automatizados:

1. **Testes de API (Integração HTTP)** - Testam os endpoints da API via HTTP
2. **Testes de Repositório (CRUD)** - Testam diretamente os repositórios e serviços

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Gerar Cliente Prisma (se necessário)

```bash
npx prisma generate
```

### 3. Executar Testes

```bash
# Todos os testes
python run_tests.py

# Ou usando pytest diretamente
python -m pytest tests/ -v
```

## 📁 Estrutura de Testes

```
backend/tests/
├── __init__.py
├── conftest.py              # Configuração global do pytest
├── README.md                # Documentação dos testes
├── test_api_reservas.py     # Testes HTTP de reservas
├── test_api_clientes.py     # Testes HTTP de clientes
├── test_api_quartos.py      # Testes HTTP de quartos
├── test_reservas_crud.py    # Testes de repositório de reservas
├── test_clientes_crud.py    # Testes de repositório de clientes
└── test_quartos_crud.py     # Testes de repositório de quartos
```

## 🧪 Tipos de Testes

### Testes de API (Integração)

Testam o fluxo completo da aplicação fazendo requisições HTTP reais:

```python
# Exemplo: test_api_reservas.py
@pytest.mark.asyncio
@pytest.mark.integration
async def test_criar_reserva(client, cliente_teste, quarto_teste):
    response = await client.post("/api/v1/reservas", json={...})
    assert response.status_code == 200
```

**Vantagens:**
- Testam o fluxo completo (request → controller → service → repository)
- Validam formato de resposta HTTP
- Testam validações de entrada

**Executar:**
```bash
python -m pytest tests/test_api_*.py -v
```

### Testes de Repositório (CRUD)

Testam diretamente os repositórios e serviços:

```python
# Exemplo: test_reservas_crud.py
@pytest.mark.asyncio
async def test_criar_reserva(reserva_service, cliente_teste, quarto_teste):
    reserva = await reserva_service.create(reserva_data)
    assert reserva["status"] == "PENDENTE"
```

**Vantagens:**
- Mais rápidos
- Não dependem da API estar rodando
- Testam lógica de negócio diretamente

**Executar:**
```bash
python -m pytest tests/test_*_crud.py -v
```

## 🎯 Cobertura de Testes

### ✅ Reservas
- [x] Criar reserva
- [x] Listar reservas
- [x] Obter reserva por ID
- [x] Check-in
- [x] Check-out
- [x] Cancelar reserva
- [x] Validações de status
- [x] Listar reservas por cliente

### ✅ Clientes
- [x] Criar cliente
- [x] Listar clientes
- [x] Obter cliente por ID
- [x] Obter cliente por documento
- [x] Atualizar cliente
- [x] Validação de documento duplicado

### ✅ Quartos
- [x] Criar quarto
- [x] Listar quartos
- [x] Obter quarto por número
- [x] Atualizar quarto
- [x] Atualizar status
- [x] Listar quartos disponíveis
- [x] Listar por status/tipo

## 🔧 Comandos Úteis

### Executar testes específicos

```bash
# Apenas testes de reservas
python -m pytest tests/test_*reservas*.py -v

# Apenas testes de clientes
python -m pytest tests/test_*clientes*.py -v

# Apenas testes de quartos
python -m pytest tests/test_*quartos*.py -v

# Teste específico
python -m pytest tests/test_api_reservas.py::test_checkin_reserva -v
```

### Com marcadores

```bash
# Apenas testes de integração
python -m pytest tests/ -m integration -v

# Apenas testes de CRUD
python -m pytest tests/ -m crud -v
```

### Com cobertura

```bash
pip install pytest-cov
python -m pytest tests/ --cov=app --cov-report=html
```

## 📝 Configuração

### pytest.ini

O arquivo `pytest.ini` contém:
- Modo assíncrono automático
- Marcadores personalizados
- Opções de saída

### Fixtures Disponíveis

- `client` - Cliente HTTP para testes de API
- `cliente_teste` - Cliente criado via API
- `quarto_teste` - Quarto criado via API
- `db` - Conexão com banco de dados
- `reserva_service` - Serviço de reservas
- `cliente_service` - Serviço de clientes
- `quarto_service` - Serviço de quartos

## ⚠️ Notas Importantes

1. **Banco de Dados**: Os testes criam dados temporários. Em ambiente de produção, use um banco de teste separado.

2. **Prisma**: O cliente Prisma deve ser gerado antes de executar os testes:
   ```bash
   npx prisma generate
   ```

3. **Variáveis de Ambiente**: Configure o `.env` com a `DATABASE_URL` correta.

4. **Limpeza**: Os testes de API não limpam dados automaticamente (não há endpoints DELETE). Use um banco de teste separado.

## 🐛 Troubleshooting

### Erro: "cannot import name 'Prisma'"
```bash
npx prisma generate
```

### Erro: "pytest não encontrado"
```bash
pip install pytest pytest-asyncio
```

### Erro: "httpx não encontrado"
```bash
pip install httpx
```

### Testes falhando por dados duplicados
- Use um banco de teste separado
- Ou limpe o banco antes de executar os testes

## 📊 Relatórios

### Gerar relatório HTML de cobertura

```bash
python -m pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Relatório JUnit (para CI/CD)

```bash
python -m pytest tests/ --junitxml=test-results.xml
```

## 🔄 CI/CD

Exemplo de configuração para GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: npx prisma generate
      - run: python -m pytest tests/ -v
```

## 📚 Recursos

- [Documentação do pytest](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [httpx](https://www.python-httpx.org/)

