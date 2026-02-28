# Como Executar os Testes

## ⚠️ Problema Atual

O Prisma Client precisa ser gerado, mas há incompatibilidade de versões com Python 3.14.

## ✅ Solução Rápida

### Opção 1: Usar Python 3.11 ou 3.12

```powershell
# Se tiver Python 3.11 ou 3.12 instalado:
py -3.11 -m venv venv312
venv312\Scripts\activate
pip install -r requirements.txt
npx prisma@5.17.0 generate
python run_tests.py
```

### Opção 2: Executar Testes de API (sem Prisma gerado)

Os testes de API podem funcionar se o servidor estiver rodando:

```powershell
# Terminal 1: Iniciar servidor
cd backend
uvicorn app.main:app --reload

# Terminal 2: Executar testes de API
cd backend
python -m pytest tests/test_api_*.py -v
```

### Opção 3: Testar Manualmente

Use o script de teste manual:

```powershell
cd backend
python test_manual.py
```

## 📋 Estrutura de Testes Criada

✅ **Testes de API** (17 testes):
- `test_api_reservas.py` - 6 testes
- `test_api_clientes.py` - 5 testes  
- `test_api_quartos.py` - 6 testes

✅ **Testes de CRUD** (23 testes):
- `test_reservas_crud.py` - 9 testes
- `test_clientes_crud.py` - 6 testes
- `test_quartos_crud.py` - 8 testes

## 🎯 Próximos Passos

1. **Resolver Prisma**: Use Python 3.11/3.12 ou atualize as dependências
2. **Executar Testes**: `python run_tests.py`
3. **Ver Cobertura**: `python -m pytest tests/ --cov=app --cov-report=html`

## 📚 Documentação

- `TESTES.md` - Guia completo de testes
- `tests/README.md` - Documentação dos testes
- `SOLUCAO_PRISMA.md` - Soluções para problema do Prisma

