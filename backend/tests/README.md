# Testes Automatizados - Hotel Real Cabo Frio

Este diretório contém todos os testes automatizados do sistema.

## Estrutura de Testes

### Testes de Integração (API HTTP)
- `test_api_reservas.py` - Testes HTTP para endpoints de reservas
- `test_api_clientes.py` - Testes HTTP para endpoints de clientes
- `test_api_quartos.py` - Testes HTTP para endpoints de quartos

### Testes de Repositório (Banco de Dados)
- `test_reservas_crud.py` - Testes diretos do repositório de reservas
- `test_clientes_crud.py` - Testes diretos do repositório de clientes
- `test_quartos_crud.py` - Testes diretos do repositório de quartos

## Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Gerar cliente Prisma (se necessário)
npx prisma generate
```

## Executar Testes

### Todos os testes:
```bash
python run_tests.py
# ou
python -m pytest tests/ -v
```

### Testes específicos:
```bash
# Apenas testes de API
python -m pytest tests/test_api_*.py -v

# Apenas testes de repositório
python -m pytest tests/test_*_crud.py -v

# Apenas testes de reservas
python -m pytest tests/test_*reservas*.py -v
```

### Com marcadores:
```bash
# Apenas testes de integração
python -m pytest tests/ -m integration -v

# Apenas testes de CRUD
python -m pytest tests/ -m crud -v
```

## Tipos de Testes

### Testes de Integração (API)
- Fazem requisições HTTP reais à API
- Testam o fluxo completo: request → controller → service → repository → response
- Usam `httpx.AsyncClient` para fazer requisições assíncronas
- Marcados com `@pytest.mark.integration`

### Testes de Repositório
- Testam diretamente os repositórios e serviços
- Mais rápidos que testes de integração
- Não dependem da API estar rodando
- Marcados com `@pytest.mark.crud`

## Cobertura de Testes

### Reservas
- ✅ Criar reserva
- ✅ Listar reservas
- ✅ Obter reserva por ID
- ✅ Check-in
- ✅ Check-out
- ✅ Cancelar reserva
- ✅ Validações de status

### Clientes
- ✅ Criar cliente
- ✅ Listar clientes
- ✅ Obter cliente por ID
- ✅ Obter cliente por documento
- ✅ Atualizar cliente
- ✅ Validação de documento duplicado

### Quartos
- ✅ Criar quarto
- ✅ Listar quartos
- ✅ Obter quarto por número
- ✅ Atualizar quarto
- ✅ Atualizar status
- ✅ Listar quartos disponíveis
- ✅ Listar por status/tipo

## Configuração

O arquivo `pytest.ini` contém a configuração do pytest:
- Modo assíncrono automático
- Marcadores personalizados
- Opções de saída

## Fixtures

- `client` - Cliente HTTP para testes de API
- `cliente_teste` - Cliente de teste criado via API
- `quarto_teste` - Quarto de teste criado via API
- `db` - Conexão com banco de dados

## Notas

- Os testes criam dados temporários que são limpos automaticamente
- Certifique-se de que o banco de dados está configurado
- Os testes de API não requerem o servidor estar rodando (usam TestClient)
- Para testes em ambiente de produção, configure variáveis de ambiente apropriadas
