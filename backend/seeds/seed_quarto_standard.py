"""
Script para adicionar um quarto de teste do tipo STANDARD.
"""
import asyncio
from app.core.database import get_db, get_db_connected
from app.repositories.quarto_repo import QuartoRepository
from app.schemas.quarto_schema import StatusQuarto, TipoSuite

async def seed_quarto_standard():
    db = await get_db_connected()
    quarto_repo = QuartoRepository(db)
    
    # Verificar se já existe um quarto STANDARD
    existing = await quarto_repo.list_all(
        tipo_suite=TipoSuite.STANDARD,
        status=StatusQuarto.LIVRE,
        limit=1
    )
    
    if existing["total"] > 0:
        print(f"✅ Já existe um quarto STANDARD disponível: {existing['quartos'][0]['numero']}")
        return
    
    # Criar um quarto STANDARD
    novo_quarto = {
        "numero": "STD-001",
        "tipo_suite": TipoSuite.STANDARD,
        "status": StatusQuarto.LIVRE,
        "descricao": "Quarto Standard para testes"
    }
    
    try:
        quarto = await quarto_repo.create(novo_quarto)
        print(f"✅ Quarto STANDARD criado com sucesso: {quarto['numero']}")
    except Exception as e:
        print(f"❌ Erro ao criar quarto STANDARD: {str(e)}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    print("Iniciando a criação do quarto STANDARD...")
    asyncio.run(seed_quarto_standard())
