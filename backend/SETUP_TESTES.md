# Como Executar os Testes

## Problema Identificado

O Prisma Client precisa ser gerado antes de executar os testes. O erro `ImportError: cannot import name 'Prisma'` indica que o cliente Prisma não foi gerado.

## Solução

### 1. Gerar o Cliente Prisma

```powershell
# No diretório backend
cd backend

# Gerar o cliente Prisma
prisma generate
```

Se o comando `prisma` não estiver disponível, instale o Prisma CLI:

```powershell
npm install -g prisma
# ou
npx prisma generate
```

### 2. Instalar Dependências Python

```powershell
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### 3. Executar Testes

**Opção 1: Usando pytest (recomendado)**
```powershell
# Usar python -m pytest ao invés de pytest diretamente
python -m pytest tests/ -v
```

**Opção 2: Teste manual**
```powershell
python test_manual.py
```

## Estrutura de Testes

- `tests/test_reservas_crud.py` - Testes de reservas (check-in/check-out)
- `tests/test_clientes_crud.py` - Testes de clientes
- `tests/test_quartos_crud.py` - Testes de quartos

## Notas Importantes

1. **Banco de Dados**: Certifique-se de que o banco de dados está configurado e acessível
2. **Variáveis de Ambiente**: Configure o `.env` com a `DATABASE_URL` correta
3. **Prisma Client**: O cliente Prisma deve ser gerado antes de executar qualquer código que use o Prisma

## Verificar se Prisma está Funcionando

```powershell
python -c "from prisma import Prisma; print('Prisma OK')"
```

Se der erro, execute `prisma generate` primeiro.

