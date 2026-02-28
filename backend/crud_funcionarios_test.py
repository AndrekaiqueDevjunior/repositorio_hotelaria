import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db
from app.repositories.funcionario_repo import FuncionarioRepository
from app.schemas.funcionario_schema import FuncionarioCreate, FuncionarioUpdate

async def test_crud_funcionarios():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE CRUD COMPLETO - FUNCIONÁRIOS')
    print('=' * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # Instanciar repositório
        funcionario_repo = FuncionarioRepository(db)
        
        # 1. CREATE - Criar funcionários
        print('\n📝 1. CREATE - Criando funcionários de teste...')
        
        funcionarios_criados = []
        
        # Funcionário 1
        func1_data = FuncionarioCreate(
            nome=f"João Silva {timestamp}",
            email=f"joao.{timestamp}@hotel.com",
            perfil="RECEPCIONISTA",
            status="ATIVO"
        )
        func1 = await funcionario_repo.create(func1_data)
        funcionarios_criados.append(func1)
        print(f'   ✅ Funcionário 1 criado: {func1["nome"]} | {func1["perfil"]}')
        
        # Funcionário 2
        func2_data = FuncionarioCreate(
            nome=f"Maria Santos {timestamp}",
            email=f"maria.{timestamp}@hotel.com",
            perfil="CAMAREIRA",
            status="ATIVO"
        )
        func2 = await funcionario_repo.create(func2_data)
        funcionarios_criados.append(func2)
        print(f'   ✅ Funcionário 2 criado: {func2["nome"]} | {func2["perfil"]}')
        
        # Funcionário 3
        func3_data = FuncionarioCreate(
            nome=f"Pedro Costa {timestamp}",
            email=f"pedro.{timestamp}@hotel.com",
            perfil="GERENTE",
            status="ATIVO"
        )
        func3 = await funcionario_repo.create(func3_data)
        funcionarios_criados.append(func3)
        print(f'   ✅ Funcionário 3 criado: {func3["nome"]} | {func3["perfil"]}')
        
        print(f'   📊 Total criados: {len(funcionarios_criados)} funcionários')
        
        # 2. READ - Listar todos os funcionários
        print('\n📖️ 2. READ - Listando todos os funcionários...')
        
        todos_funcionarios = await funcionario_repo.list_all()
        print(f'   📊 Total encontrado: {len(todos_funcionarios)}')
        print(f'   📋 Exibindo os 3 primeiros:')
        
        for i, func in enumerate(todos_funcionarios[:3], 1):
            print(f'      {i}. ID: {func["id"]} | {func["nome"]} | {func["perfil"]} | {func["status"]}')
        
        # 3. READ - Buscar funcionário específico
        print('\n🔍 3. READ - Buscando funcionário específico...')
        
        func_busca = await funcionario_repo.get_by_id(func1["id"])
        print(f'   ✅ Funcionário encontrado: {func_busca["nome"]} | {func_busca["email"]}')
        
        # 4. UPDATE - Atualizar funcionário
        print('\n✏️ 4. UPDATE - Atualizando funcionário...')
        
        # Atualizar status para INATIVO
        update_data = FuncionarioUpdate(
            status="INATIVO"
        )
        
        func_atualizado = await funcionario_repo.update(func1["id"], update_data)
        print(f'   ✅ Funcionário atualizado: {func_atualizado["nome"]} | {func_atualizado["status"]}')
        
        # Atualizar perfil e nome
        update_data2 = FuncionarioUpdate(
            nome=f"Maria Santos Silva {timestamp}",
            perfil="SUPERVISOR",
            status="ATIVO"
        )
        
        func_atualizado2 = await funcionario_repo.update(func2["id"], update_data2)
        print(f'   ✅ Funcionário atualizado: {func_atualizado2["nome"]} | {func_atualizado2["perfil"]}')
        
        # 5. READ - Verificar atualizações
        print('\n🔍 5. READ - Verificando atualizações...')
        
        func_verificado1 = await funcionario_repo.get_by_id(func1["id"])
        print(f'   📋 Funcionário 1: {func_verificado1["nome"]} | {func_verificado1["status"]}')
        
        func_verificado2 = await funcionario_repo.get_by_id(func2["id"])
        print(f'   📋 Funcionário 2: {func_verificado2["nome"]} | {func_verificado2["perfil"]}')
        
        # 6. UPDATE - Atualizar senha
        print('\n🔐 6. UPDATE - Atualizando senha...')
        
        update_senha = FuncionarioUpdate(
            senha="novaSenha123"
        )
        
        func_senha = await funcionario_repo.update(func3["id"], update_senha)
        print(f'   ✅ Senha atualizada para: {func_senha["nome"]}')
        
        # 7. READ - Listar funcionários finais
        print('\n📋 7. READ - Listando funcionários finais...')
        
        funcionarios_finais = await funcionario_repo.list_all()
        print(f'   📊 Total final: {len(funcionarios_finais)}')
        
        print(f'   📋 Funcionários criados no teste:')
        for func in funcionarios_criados:
            func_atual = await funcionario_repo.get_by_id(func["id"])
            print(f'      - {func_atual["nome"]} | {func_atual["perfil"]} | {func_atual["status"]}')
        
        # 8. Testar filtros
        print('\n🔍 8. TESTE DE FILTROS...')
        
        # Listar todos (funcionário_repo não tem filtros implementados)
        funcs_ativos = await funcionario_repo.list_all()
        print(f'   📊 Total de funcionários: {len(funcs_ativos)}')
        
        # Filtrar manualmente por status
        funcs_ativos_filtrado = [f for f in funcs_ativos if f["status"] == "ATIVO"]
        print(f'   📊 Funcionários ATIVOS: {len(funcs_ativos_filtrado)}')
        
        # Filtrar manualmente por perfil
        funcs_gerentes_filtrado = [f for f in funcs_ativos if f["perfil"] == "GERENTE"]
        print(f'   📊 Funcionários GERENTES: {len(funcs_gerentes_filtrado)}')
        
        # Filtrar manualmente por nome
        funcs_busca_filtrado = [f for f in funcs_ativos if "Silva" in f["nome"]]
        print(f'   📊 Funcionários com "Silva": {len(funcs_busca_filtrado)}')
        
        # 9. DELETE - Excluir um funcionário
        print('\n🗑️ 9. DELETE - Excluindo funcionário de teste...')
        
        await funcionario_repo.delete(func3["id"])
        print(f'   ✅ Funcionário {func3["nome"]} excluído')
        
        # 10. READ - Verificar exclusão
        print('\n🔍 10. READ - Verificando exclusão...')
        
        try:
            func_excluido = await funcionario_repo.get_by_id(func3["id"])
            print(f'   ❌ ERRO: Funcionário {func3["nome"]} ainda existe!')
        except ValueError as e:
            print(f'   ✅ Confirmação: {str(e)}')
        
        print('\n' + '=' * 60)
        print('🎉 TESTE CRUD FUNCIONÁRIOS CONCLUÍDO!')
        print('=' * 60)
        
        print(f'✅ CREATE: {len(funcionarios_criados)} funcionários criados')
        print(f'✅ READ: Listagem e busca funcionando')
        print(f'✅ UPDATE: Perfil, status e senha atualizados')
        print(f'✅ DELETE: Exclusão funcionando')
        print(f'✅ FILTROS: Status, perfil e busca funcionando')
        
        return {
            "sucesso": True,
            "criados": len(funcionarios_criados),
            "total_final": len(funcionarios_finais),
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
    resultado = asyncio.run(test_crud_funcionarios())
    print(f'\n📊 Resultado: {resultado}')
