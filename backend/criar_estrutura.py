import os

BASE_DIR = r"g:\app_hotel_cabo_frio\backend\app"

# Estrutura de pastas e arquivos
structure = {
    "": ["__init__.py", "main.py"],
    "core": [
        "__init__.py",
        "config.py",
        "database.py",
        "security.py",
        "redis_client.py",
        "celery_app.py",
    ],
    "schemas": [
        "__init__.py",
        "auth_schema.py",
        "cliente_schema.py",
        "reserva_schema.py",
        "quarto_schema.py",
        "funcionario_schema.py",
        "pagamento_schema.py",
        "pontos_schema.py",
        "antifraude_schema.py",
        "dashboard_schema.py",
    ],
    "repositories": [
        "__init__.py",
        "cliente_repo.py",
        "reserva_repo.py",
        "quarto_repo.py",
        "funcionario_repo.py",
        "pagamento_repo.py",
        "pontos_repo.py",
        "antifraude_repo.py",
    ],
    "services": [
        "__init__.py",
        "cielo_service.py",
        "cliente_service.py",
        "reserva_service.py",
        "quarto_service.py",
        "funcionario_service.py",
        "pagamento_service.py",
        "pontos_service.py",
        "dashboard_service.py",
        "antifraude_service.py",
    ],
    "api": ["__init__.py"],
    os.path.join("api", "v1"): [
        "__init__.py",
        "auth_routes.py",
        "cliente_routes.py",
        "reserva_routes.py",
        "quarto_routes.py",
        "funcionario_routes.py",
        "pagamento_routes.py",
        "pontos_routes.py",
        "dashboard_routes.py",
        "webhook_routes.py",
    ],
    "utils": [
        "__init__.py",
        "hashing.py",
        "cache.py",
        "rate_limit.py",
    ],
    "middlewares": [
        "__init__.py",
        "security_headers.py",
        "rate_limit.py",
        "audit_logging.py",
    ],
    "tasks": [
        "__init__.py",
        "email_tasks.py",
        "antifraude_tasks.py",
        "relatorio_tasks.py",
        "limpeza_tasks.py",
    ],
}

print("\n=== Criando estrutura do projeto sem sobrescrever nada ===\n")

for folder, files in structure.items():
    dir_path = os.path.join(BASE_DIR, folder)

    # Criar pasta se não existir
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        print(f"[PASTA CRIADA] {dir_path}")
    else:
        print(f"[PASTA EXISTE] {dir_path}")

    # Criar arquivos
    for file_name in files:
        file_path = os.path.join(dir_path, file_name)

        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")  # arquivo vazio apenas para existir
            print(f"  [ARQUIVO CRIADO] {file_path}")
        else:
            print(f"  [ARQUIVO EXISTE] {file_path}")

print("\n=== Finalizado ===")
