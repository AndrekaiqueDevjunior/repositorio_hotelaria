"""
Script para popular o banco de dados com tarifas iniciais para teste.
"""
import asyncio
from datetime import date, timedelta
from app.core.database import get_db
from app.repositories.tarifa_suite_repo import TarifaSuiteRepository
from app.schemas.quarto_schema import TipoSuite

async def seed_tarifas():
    db = await get_db()
    tarifa_repo = TarifaSuiteRepository(db)
    
    # Data de início: hoje
    data_inicio = date.today()
    # Data de fim: 1 ano a partir de hoje
    data_fim = data_inicio + timedelta(days=365)
    
    # Tarifa para suíte STANDARD
    tarifa_standard = {
        'suite_tipo': TipoSuite.STANDARD,
        'temporada': 'Baixa Temporada',
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'preco_diaria': 200.00,  # R$ 200,00 por diária
        'ativo': True
    }
    
    try:
        # Verifica se já existe uma tarifa para o período
        tarifa_existente = await tarifa_repo.list_all(
            suite_tipo=TipoSuite.STANDARD,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ativo=True
        )
        
        if not tarifa_existente["tarifas"]:
            # Se não existir, cria uma nova tarifa
            await tarifa_repo.create(tarifa_standard)
            print("✅ Tarifa para suíte STANDARD criada com sucesso!")
        else:
            print("ℹ️ Já existe uma tarifa ativa para a suíte STANDARD no período informado.")
            
    except Exception as e:
        print(f"❌ Erro ao criar tarifa: {str(e)}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    print("Iniciando a criação de tarifas de teste...")
    asyncio.run(seed_tarifas())
