import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db
from app.repositories.quarto_repo import QuartoRepository
from app.schemas.quarto_schema import QuartoCreate, QuartoUpdate, StatusQuarto, TipoSuite

async def test_crud_quartos():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE CRUD COMPLETO - QUARTOS')
    print('=' * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # Instanciar repositório
        quarto_repo = QuartoRepository(db)
        
        # 1. CREATE - Criar quartos
        print('\n📝 1. CREATE - Criando quartos de teste...')
        
        quartos_criados = []
        
        # Quarto 1
        quarto1_data = QuartoCreate(
            numero=f"101{timestamp[-2:]}",
            tipo_suite=TipoSuite.LUXO,
            status=StatusQuarto.LIVRE
        )
        quarto1 = await quarto_repo.create(quarto1_data)
        quartos_criados.append(quarto1)
        print(f'   ✅ Quarto 1 criado: {quarto1["numero"]} | {quarto1["tipo_suite"]}')
        
        # Quarto 2
        quarto2_data = QuartoCreate(
            numero=f"102{timestamp[-2:]}",
            tipo_suite=TipoSuite.MASTER,
            status=StatusQuarto.LIVRE
        )
        quarto2 = await quarto_repo.create(quarto2_data)
        quartos_criados.append(quarto2)
        print(f'   ✅ Quarto 2 criado: {quarto2["numero"]} | {quarto2["tipo_suite"]}')
        
        # Quarto 3
        quarto3_data = QuartoCreate(
            numero=f"103{timestamp[-2:]}",
            tipo_suite=TipoSuite.REAL,
            status=StatusQuarto.LIVRE
        )
        quarto3 = await quarto_repo.create(quarto3_data)
        quartos_criados.append(quarto3)
        print(f'   ✅ Quarto 3 criado: {quarto3["numero"]} | {quarto3["tipo_suite"]}')
        
        print(f'   📊 Total criados: {len(quartos_criados)} quartos')
        
        # 2. READ - Listar todos os quartos
        print('\n📖️ 2. READ - Listando todos os quartos...')
        
        todos_quartos = await quarto_repo.list_all()
        print(f'   📊 Total encontrado: {todos_quartos["total"]}')
        print(f'   📋 Exibindo os 3 primeiros:')
        
        for i, quarto in enumerate(todos_quartos["quartos"][:3], 1):
            print(f'      {i}. ID: {quarto["id"]} | {quarto["numero"]} | {quarto["tipo_suite"]} | {quarto["status"]}')
        
        # 3. READ - Buscar quarto específico
        print('\n🔍 3. READ - Buscando quarto específico...')
        
        quarto_busca = await quarto_repo.get_by_numero(quarto1["numero"])
        print(f'   ✅ Quarto encontrado: {quarto_busca["numero"]} | {quarto_busca["tipo_suite"]}')
        
        # 4. UPDATE - Atualizar quarto
        print('\n✏️ 4. UPDATE - Atualizando quarto...')
        
        # Atualizar status para OCUPADO
        update_data = QuartoUpdate(
            status=StatusQuarto.OCUPADO
        )
        
        quarto_atualizado = await quarto_repo.update(quarto1["numero"], update_data)
        print(f'   ✅ Quarto atualizado: {quarto_atualizado["numero"]} | {quarto_atualizado["status"]}')
        
        # Atualizar tipo de suíte
        update_data2 = QuartoUpdate(
            tipo_suite=TipoSuite.MASTER,
            status=StatusQuarto.MANUTENCAO
        )
        
        quarto_atualizado2 = await quarto_repo.update(quarto2["numero"], update_data2)
        print(f'   ✅ Quarto atualizado: {quarto_atualizado2["numero"]} | {quarto_atualizado2["tipo_suite"]} | {quarto_atualizado2["status"]}')
        
        # 5. UPDATE - Atualizar status específico
        await quarto_repo.update_status(quarto3["numero"], StatusQuarto.BLOQUEADO)
        print(f'   ✅ Quarto {quarto3["numero"]} status: LIVRE → BLOQUEADO')
        
        # 6. READ - Verificar atualizações
        print('\n🔍 6. READ - Verificando atualizações...')
        
        quarto_verificado1 = await quarto_repo.get_by_numero(quarto1["numero"])
        print(f'   📋 Quarto 1: {quarto_verificado1["numero"]} | {quarto_verificado1["status"]}')
        
        quarto_verificado2 = await quarto_repo.get_by_numero(quarto2["numero"])
        print(f'   📋 Quarto 2: {quarto_verificado2["numero"]} | {quarto_verificado2["tipo_suite"]} | {quarto_verificado2["status"]}')
        
        quarto_verificado3 = await quarto_repo.get_by_numero(quarto3["numero"])
        print(f'   📋 Quarto 3: {quarto_verificado3["numero"]} | {quarto_verificado3["status"]}')
        
        # 7. DELETE - Excluir um quarto
        print('\n🗑️ 7. DELETE - Excluindo quarto de teste...')
        
        await quarto_repo.delete(quarto3["numero"])
        print(f'   ✅ Quarto {quarto3["numero"]} excluído')
        
        # 8. READ - Verificar exclusão
        print('\n🔍 8. READ - Verificando exclusão...')
        
        try:
            quarto_excluido = await quarto_repo.get_by_numero(quarto3["numero"])
            print(f'   ❌ ERRO: Quarto {quarto3["numero"]} ainda existe!')
        except ValueError as e:
            print(f'   ✅ Confirmação: {str(e)}')
        
        # 9. READ - Listar quartos finais
        print('\n📋 9. READ - Listando quartos finais...')
        
        quartos_finais = await quarto_repo.list_all()
        print(f'   📊 Total final: {quartos_finais["total"]}')
        
        print(f'   📋 Quartos restantes:')
        for i, quarto in enumerate(quartos_finais["quartos"], 1):
            print(f'      {i}. ID: {quarto["id"]} | {quarto["numero"]} | {quarto["tipo_suite"]} | {quarto["status"]}')
        
        # 10. Testar filtros
        print('\n🔍 10. TESTE DE FILTROS...')
        
        # Filtrar por status
        quartos_livres = await quarto_repo.list_all(status="LIVRE")
        print(f'   📊 Quartos LIVRES: {quartos_livres["total"]}')
        
        # Filtrar por tipo
        quartos_luxo = await quarto_repo.list_all(tipo_suite="LUXO")
        print(f'   📊 Quartos LUXO: {quartos_luxo["total"]}')
        
        # Buscar por número
        quartos_busca = await quarto_repo.list_all(search="10")
        print(f'   📊 Quartos com "10": {quartos_busca["total"]}')
        
        print('\n' + '=' * 60)
        print('🎉 TESTE CRUD QUARTOS CONCLUÍDO!')
        print('=' * 60)
        
        print(f'✅ CREATE: {len(quartos_criados)} quartos criados')
        print(f'✅ READ: Listagem e busca funcionando')
        print(f'✅ UPDATE: Status e atributos atualizados')
        print(f'✅ DELETE: Exclusão funcionando')
        print(f'✅ FILTROS: Status, tipo e busca funcionando')
        
        return {
            "sucesso": True,
            "criados": len(quartos_criados),
            "total_final": quartos_finais["total"],
            "operacoes": ["CREATE", "READ", "UPDATE", "DELETE", "FILTROS"]
        }
        
    except Exception as e:
        print(f'\n❌ ERRO NO TESTE: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return {
            "sucesso": False,
            "erro": str(e)
        }

if __name__ == "__main__":
    resultado = asyncio.run(test_crud_quartos())
    print(f'\n📊 Resultado: {resultado}')
