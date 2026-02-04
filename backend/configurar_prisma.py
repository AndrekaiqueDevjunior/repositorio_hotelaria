# Salve como: configurar_prisma.py
# Execute com: python configurar_prisma.py

import os
from pathlib import Path

def configurar_prisma():
    base_dir = Path.cwd()
    prisma_dir = base_dir / "prisma"
    
    # Criar diretório prisma
    prisma_dir.mkdir(exist_ok=True)
    
    # Criar schema.prisma
    schema_content = """// Schema Prisma para Hotel Real Cabo Frio

generator client {
  provider = "prisma-client-py"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// Modelo simples para teste
model Usuario {
  id        Int      @id @default(autoincrement())
  nome      String
  email     String   @unique
  senhaHash String   @map("senha_hash")
  perfil    String
  status    String   @default("ATIVO")
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  @@map("usuarios")
}

model Cliente {
  id           Int      @id @default(autoincrement())
  nomeCompleto String   @map("nome_completo")
  documento    String   @unique
  telefone     String?
  email        String?
  status       String   @default("ATIVO")
  createdAt    DateTime @default(now()) @map("created_at")
  updatedAt    DateTime @updatedAt @map("updated_at")

  @@map("clientes")
}

model Reserva {
  id               Int      @id @default(autoincrement())
  codigoReserva    String   @unique @map("codigo_reserva")
  clienteId        Int      @map("cliente_id")
  statusReserva    String   @default("PENDENTE") @map("status_reserva")
  checkinPrevisto  DateTime @map("checkin_previsto")
  checkoutPrevisto DateTime @map("checkout_previsto")
  valorDiaria      Decimal  @map("valor_diaria") @db.Decimal(10, 2)
  createdAt        DateTime @default(now()) @map("created_at")
  updatedAt        DateTime @updatedAt @map("updated_at")

  @@map("reservas")
}
"""
    
    # Salvar schema.prisma
    schema_path = prisma_dir / "schema.prisma"
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(schema_content)
    
    print("✅ Prisma configurado com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Execute: prisma generate")
    print("2. Execute: prisma db push")
    print("3. Teste a aplicação!")

def criar_dockerfile():
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Instalar Node.js para Prisma
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    nodejs \\
    npm \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar schema do Prisma e gerar cliente
COPY prisma ./prisma/
RUN npx prisma@5.7.1 generate

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["gunicorn", "app_simples:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
'''
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    print("✅ Dockerfile criado com sucesso!")

if __name__ == "__main__":
    configurar_prisma()
    criar_dockerfile()