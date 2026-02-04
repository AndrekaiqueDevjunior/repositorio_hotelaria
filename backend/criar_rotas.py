# Copie este código e salve como: criar_rotas.py
# Execute com: python criar_rotas.py

from pathlib import Path

def criar_rotas():
    base_dir = Path.cwd()
    
    # Criar arquivo main.py simplificado
    main_content = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": f"Bem-vindo ao {settings.APP_NAME}",
        "version": "1.0.0",
        "status": "online",
        "database": "Prisma Accelerate Connected"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
"""
    
    # Salvar main.py
    with open(base_dir / "app" / "main.py", 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    print("✅ main.py atualizado com sucesso!")
    print("\n🚀 Execute: uvicorn app.main:app --reload")

if __name__ == "__main__":
    criar_rotas()