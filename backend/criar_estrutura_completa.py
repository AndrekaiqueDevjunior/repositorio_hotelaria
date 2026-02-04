import os

BASE = r"g:\app_hotel_cabo_frio\backend\app"

# Estrutura completa com arquivos obrigatórios
structure = {
    "": ["__init__.py"],
    "core": ["__init__.py"],
    "schemas": ["__init__.py"],
    "repositories": ["__init__.py"],
    "services": ["__init__.py"],
    "api": ["__init__.py"],
    os.path.join("api", "v1"): ["__init__.py"],
    "utils": ["__init__.py"],
    "middlewares": ["__init__.py"],
    "tasks": ["__init__.py"],
}

print("\n🏗️ Criando estrutura de pastas e arquivos...\n")

for folder, files in structure.items():
    dir_path = os.path.join(BASE, folder)

    # Criar pasta
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        print(f"[PASTA CRIADA] {dir_path}")
    else:
        print(f"[PASTA EXISTE] {dir_path}")

    # Criar arquivos
    for f in files:
        file_path = os.path.join(dir_path, f)
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.write("")  # arquivo vazio
            print(f"   [ARQUIVO CRIADO] {file_path}")
        else:
            print(f"   [ARQUIVO EXISTE] {file_path}")

print("\n✅ Finalizado! Todas as pastas e arquivos mínimos foram criados.\n")
