from app.core.database import get_db
import asyncio

async def buscar_clientes_com_pontos():
    db = get_db()
    await db.connect()
    
    # Buscar todos os clientes com seus saldos RP
    result = await db.query_raw('SELECT c.id, c.nomeCompleto, c.documento, cr.cliente_id, cr.saldo_rp, cr.diarias_pendentes FROM clientes c LEFT JOIN clientes_rp cr ON c.id = cr.cliente_id ORDER BY cr.saldo_rp DESC')
    
    print('🔍 CLIENTES COM PONTOS RP:')
    print('=' * 60)
    
    clientes_com_pontos = []
    
    for row in result:
        if row['saldo_rp'] and row['saldo_rp'] > 0:
            clientes_com_pontos.append(row)
            print('✅ ID: ' + str(row['id']) + ' | ' + row['nomeCompleto'])
            print('   📧 CPF: ' + row['documento'])
            print('   💎 Saldo: ' + str(row['saldo_rp']) + ' RP')
            print('   📅 Diárias pendentes: ' + str(row['diarias_pendentes']))
            print()
    
    if not clientes_com_pontos:
        print('❌ Nenhum cliente com pontos encontrado')
        print()
        print('📊 TODOS OS CLIENTES E SEUS SALDOS:')
        print('=' * 40)
        
        for row in result:
            saldo = row['saldo_rp'] if row['saldo_rp'] else 0
            diarias = row['diarias_pendentes'] if row['diarias_pendentes'] else 0
            status = '💎' if saldo > 0 or diarias > 0 else '⭕'
            print(status + ' ID: ' + str(row['id']) + ' | ' + row['nomeCompleto'][:30] + '...')
            print('     Saldo: ' + str(saldo) + ' RP | Diárias: ' + str(diarias))
    
    # Verificar se há algum histórico
    print()
    print('📈 VERIFICANDO HISTÓRICO...')
    
    historico = await db.query_raw('SELECT COUNT(*) as total FROM historico_rp')
    total_historico = historico[0]['total']
    print('📈 Total de registros no histórico: ' + str(total_historico))
    
    if total_historico > 0:
        print('💡 Há histórico de pontos no sistema!')
        
        # Mostrar alguns detalhes
        detalhes = await db.query_raw('SELECT * FROM historico_rp LIMIT 3')
        print('📈 Últimas movimentações:')
        for h in detalhes:
            print('  Cliente ID: ' + str(h['cliente_id']) + ' | Pontos: ' + str(h['pontos_gerados']))
    else:
        print('💡 Nenhum histórico encontrado - pontos ainda não foram gerados')
        print()
        print('🚀 PARA GERAR PONTOS:')
        print('   1. Crie uma reserva')
        print('   2. Confirme o pagamento')
        print('   3. Faça o checkout')
        print('   4. Os pontos serão calculados automaticamente!')
    
    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(buscar_clientes_com_pontos())
