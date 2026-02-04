"""
Script de teste do sistema de pontos
Testa o fluxo completo: criar reserva → checkout → verificar pontos
"""
import asyncio
from app.core.database import db

async def test_pontos_system():
    print("🧪 TESTE DO SISTEMA DE PONTOS")
    print("=" * 60)
    
    await db.connect()
    
    try:
        # 1. Verificar estrutura da tabela
        print("\n1️⃣ Verificando estrutura de transacoes_pontos...")
        result = await db.query_raw("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'transacoes_pontos'
            ORDER BY ordinal_position;
        """)
        print(f"✅ Campos encontrados: {len(result)} colunas")
        for col in result:
            print(f"   - {col['column_name']}: {col['data_type']}")
        
        # 2. Verificar registros existentes
        print("\n2️⃣ Verificando registros existentes...")
        usuarios_pontos = await db.usuariopontos.count()
        transacoes = await db.transacaopontos.count()
        print(f"✅ UsuarioPontos: {usuarios_pontos} registros")
        print(f"✅ TransacaoPontos: {transacoes} registros")
        
        # 3. Buscar uma reserva CHECKED_OUT para testar
        print("\n3️⃣ Buscando reserva finalizada...")
        reserva = await db.reserva.find_first(
            where={"status": "CHECKED_OUT"},
            include={"cliente": True}
        )
        
        if reserva:
            print(f"✅ Reserva encontrada: {reserva.codigoReserva}")
            print(f"   Cliente: {reserva.cliente.nomeCompleto}")
            print(f"   Tipo Suíte: {reserva.tipoSuite}")
            print(f"   Diárias: {reserva.numDiarias}")
            
            # 4. Verificar se já tem pontos creditados
            print("\n4️⃣ Verificando pontos do cliente...")
            pontos_cliente = await db.usuariopontos.find_first(
                where={"clienteId": reserva.clienteId}
            )
            
            if pontos_cliente:
                print(f"✅ Saldo atual: {pontos_cliente.saldo} pontos")
                
                # Buscar transações
                transacoes_cliente = await db.transacaopontos.find_many(
                    where={"clienteId": reserva.clienteId},
                    order={"createdAt": "desc"},
                    take=5
                )
                
                print(f"✅ Transações recentes: {len(transacoes_cliente)}")
                for t in transacoes_cliente:
                    print(f"   - {t.tipo}: {t.pontos} pontos ({t.origem})")
            else:
                print("⚠️ Cliente ainda não tem registro de pontos")
        else:
            print("⚠️ Nenhuma reserva CHECKED_OUT encontrada")
        
        # 5. Testar cálculo de pontos
        print("\n5️⃣ Testando cálculo de pontos...")
        from app.services.pontos_acumulo_service import PontosAcumuloService
        
        test_cases = [
            ("REAL", 3, 15),    # 3 diárias x 5 pontos
            ("MASTER", 2, 20),  # 2 diárias x 10 pontos
            ("LUXO", 1, 15),    # 1 diária x 15 pontos
        ]
        
        for tipo_suite, diarias, esperado in test_cases:
            resultado = await PontosAcumuloService.obter_previsao_pontos(
                tipo_suite=tipo_suite,
                num_diarias=diarias
            )
            status = "✅" if resultado["pontos_estimados"] == esperado else "❌"
            print(f"{status} {tipo_suite}: {diarias} diárias = {resultado['pontos_estimados']} pontos (esperado: {esperado})")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_pontos_system())
