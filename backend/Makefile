# Makefile para facilitar execução de testes
.PHONY: test test-api test-crud test-reservas install setup

# Instalar dependências
install:
	pip install -r requirements.txt

# Configurar ambiente de testes
setup:
	pip install -r requirements.txt
	npx prisma generate || echo "Prisma já configurado"

# Executar todos os testes
test:
	python run_tests.py

# Executar apenas testes de API
test-api:
	python -m pytest tests/test_api_*.py -v

# Executar apenas testes de CRUD
test-crud:
	python -m pytest tests/test_*_crud.py -v

# Executar apenas testes de reservas
test-reservas:
	python -m pytest tests/test_*reservas*.py -v

# Executar testes com cobertura
test-coverage:
	python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Limpar cache do pytest
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

