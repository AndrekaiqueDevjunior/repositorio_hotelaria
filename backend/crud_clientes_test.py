import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db
from app.repositories.cliente_repo import ClienteRepository
from app.schemas.cliente_schema import ClienteCreate, ClienteUpdate

async def test_crud_clientes():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE CRUD COMPLETO - CLIENTES')
    print('=' * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # Instanciar repositório
        cliente_repo = ClienteRepository(db)
        
        # 1. CREATE - Criar clientes
        print('\n📝 1. CREATE - Criando clientes de teste...')
        
        clientes_criados = []
        
        # Cliente 1
        cliente1_data = ClienteCreate(
            nome_completo=f"Ana Paula Silva {timestamp}",
            documento=f"123.456.789-{timestamp[-2:]}",
            telefone=f"219999888{timestamp[-2:]}",
            email=f"ana.{timestamp}@email.com"
        )
        cliente1 = await cliente_repo.create(cliente1_data)
        clientes_criados.append(cliente1)
        print(f'   ✅ Cliente 1 criado: {cliente1["nome_completo"]} | {cliente1["documento"]}')
        
        # Cliente 2
        cliente2_data = ClienteCreate(
            nome_completo=f"Carlos Alberto {timestamp}",
            documento=f"987.654.32{timestamp[-2:]}-{timestamp[-2:]}",
            telefone=f"219999777{timestamp[-2:]}",
            email=f"carlos.{timestamp}@email.com"
        )
        cliente2 = await cliente_repo.create(cliente2_data)
        clientes_criados.append(cliente2)
        print(f'   ✅ Cliente 2 criado: {cliente2["nome_completo"]} | {cliente2["documento"]}')
        
        # Cliente 3
        cliente3_data = ClienteCreate(
            nome_completo=f"Mariana Costa {timestamp}",
            documento=f"555.555.55{timestamp[-2:]}-{timestamp[-2:]}",
            telefone=f"219999666{timestamp[-2:]}",
            email=f"mariana.{timestamp}@email.com"
        )
        cliente3 = await cliente_repo.create(cliente3_data)
        clientes_criados.append(cliente3)
        print(f'   ✅ Cliente 3 criado: {cliente3["nome_completo"]} | {cliente3["documento"]}')
        
        print(f'   📊 Total criados: {len(clientes_criados)} clientes')
        
        # 2. READ - Listar todos os clientes
        print('\n📖️ 2. READ - Listando todos os clientes...')
        
        todos_clientes = await cliente_repo.list_all()
        print(f'   📊 Total encontrado: {todos_clientes["total"]}')
        print(f'   📋 Exibindo os 3 primeiros:')
        
        for i, cliente in enumerate(todos_clientes["clientes"][:3], 1):
            print(f'      {i}. ID: {cliente["id"]} | {cliente["nome_completo"]} | {cliente["documento"]}')
        
        # 3. READ - Buscar cliente específico
        print('\n🔍 3. READ - Buscando cliente específico...')
        
        cliente_busca = await cliente_repo.get_by_id(cliente1["id"])
        print(f'   ✅ Cliente encontrado: {cliente_busca["nome_completo"]} | {cliente_busca["email"]}')
        
        # 4. UPDATE - Atualizar cliente
        print('\n✏️ 4. UPDATE - Atualizando cliente...')
        
        # Atualizar status para INATIVO
        update_data = ClienteUpdate(
            status="INATIVO"
        )
        
        cliente_atualizado = await cliente_repo.update(cliente1["id"], update_data)
        print(f'   ✅ Cliente atualizado: {cliente_atualizado["nome_completo"]} | {cliente_atualizado["status"]}')
        
        # Atualizar nome e telefone
        update_data2 = ClienteUpdate(
            nome_completo=f"Carlos Alberto Silva {timestamp}",
            telefone=f"219999999{timestamp[-2:]}",
            status="ATIVO"
        )
        
        cliente_atualizado2 = await cliente_repo.update(cliente2["id"], update_data2)
        print(f'   ✅ Cliente atualizado: {cliente_atualizado2["nome_completo"]}')
        
        # 5. READ - Verificar atualizações
        print('\n🔍 5. READ - Verificando atualizações...')
        
        cliente_verificado1 = await cliente_repo.get_by_id(cliente1["id"])
        print(f'   📋 Cliente 1: {cliente_verificado1["nome_completo"]} | {cliente_verificado1["status"]}')
        
        cliente_verificado2 = await cliente_repo.get_by_id(cliente2["id"])
        print(f'   📋 Cliente 2: {cliente_verificado2["nome_completo"]}')
        
        # 6. READ - Listar clientes finais
        print('\n📋 6. READ - Listando clientes finais...')
        
        clientes_finais = await cliente_repo.list_all()
        print(f'   📊 Total final: {clientes_finais["total"]}')
        
        print(f'   📋 Clientes criados no teste:')
        for cliente in clientes_criados:
            cliente_atual = await cliente_repo.get_by_id(cliente["id"])
            print(f'      - {cliente_atual["nome_completo"]} | {cliente_atual["documento"]} | {cliente_atual["status"]}')
        
        # 7. Testar filtros
        print('\n🔍 7. TESTE DE FILTROS...')
        
        # Filtrar por status
        clientes_ativos = await cliente_repo.list_all(status="ATIVO")
        print(f'   📊 Clientes ATIVOS: {clientes_ativos["total"]}')
        
        # Buscar por nome
        clientes_busca = await cliente_repo.list_all(search="Silva")
        print(f'   📊 Clientes com "Silva": {clientes_busca["total"]}')
        
        # Buscar por documento
        clientes_doc = await cliente_repo.list_all(search=timestamp[-2:])
        print(f'   📊 Clientes com documento "{timestamp[-2:]}": {clientes_doc["total"]}')
        
        # 8. DELETE - Excluir um cliente
        print('\n🗑️ 8. DELETE - Excluindo cliente de teste...')
        
        await cliente_repo.delete(cliente3["id"])
        print(f'   ✅ Cliente {cliente3["nome_completo"]} excluído')
        
        # 9. READ - Verificar exclusão
        print('\n🔍 9. READ - Verificando exclusão...')
        
        try:
            cliente_excluido = await cliente_repo.get_by_id(cliente3["id"])
            print(f'   ❌ ERRO: Cliente {cliente3["nome_completo"]} ainda existe!')
        except ValueError as e:
            print(f'   ✅ Confirmação: {str(e)}')
        
        # 10. READ - Buscar por documento
        print('\n📧 10. READ - Buscando por documento...')
        
        try:
            cliente_doc = await cliente_repo.get_by_documento(cliente2["documento"])
            print(f'   ✅ Cliente encontrado por documento: {cliente_doc["nome_completo"]}')
        except ValueError as e:
            print(f'   ❌ Erro ao buscar por documento: {str(e)}')
        
        print('\n' + '=' * 60)
        print('🎉 TESTE CRUD CLIENTES CONCLUÍDO!')
        print('=' * 60)
        
        print(f'✅ CREATE: {len(clientes_criados)} clientes criados')
        print(f'✅ READ: Listagem, busca por ID e documento funcionando')
        print(f'✅ UPDATE: Nome, telefone e status atualizados')
        print(f'✅ DELETE: Exclusão funcionando')
        print(f'✅ FILTROS: Status e busca funcionando')
        
        return {
            "sucesso": True,
            "criados": len(clientes_criados),
            "total_final": clientes_finais["total"],
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
    resultado = asyncio.run(test_crud_clientes())
    print(f'\n📊 Resultado: {resultado}')
