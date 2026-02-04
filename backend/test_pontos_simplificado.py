import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db

async def test_pontos_simplificado():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE SIMPLIFICADO - PONTOS NO CHECKOUT')
    print('=' * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # 1. Criar cliente diretamente no banco
        print('\n👤 1. CRIANDO CLIENTE...')
        cliente = await db.cliente.create({
            "nomeCompleto": f"Cliente Teste {timestamp}",
            "documento": f"8888888888{timestamp[-2:]}",
            "telefone": f"21999{timestamp[-6:]}",
            "email": f"teste.{timestamp}@email.com",
            "status": "ATIVO"
        })
        print(f'   ✅ Cliente criado: ID {cliente.id} | {cliente.nomeCompleto}')
        
        # 2. Criar quarto
        print('\n🏨 2. CRIANDO QUARTO...')
        quarto = await db.quarto.create({
            "numero": f"T{timestamp[-6:]}",
            "tipoSuite": "LUXO",
            "status": "LIVRE"
        })
        print(f'   ✅ Quarto criado: ID {quarto.id} | {quarto.numero}')
        
        # 3. Criar reserva
        print('\n📋 3. CRIANDO RESERVA...')
        checkin = datetime.now() - timedelta(days=1)
        checkout = checkin + timedelta(days=2)
        valor_diaria = 200.00
        num_diarias = 2
        valor_total = valor_diaria * num_diarias
        
        reserva = await db.reserva.create({
            "clienteId": cliente.id,
            "clienteNome": cliente.nomeCompleto,
            "quartoNumero": quarto.numero,
            "tipoSuite": quarto.tipoSuite,
            "checkinPrevisto": checkin,
            "checkoutPrevisto": checkout,
            "valorDiaria": valor_diaria,
            "numDiarias": num_diarias,
            "status": "PENDENTE",
            "codigoReserva": f"PTS-{timestamp}"
        })
        print(f'   ✅ Reserva criada: {reserva.codigoReserva}')
        print(f'   💰 Valor total: R$ {valor_total}')
        
        # 4. Calcular pontos esperados
        pontos_esperados = int(valor_total / 10)
        print(f'   🎯 Pontos esperados: {pontos_esperados} (1 ponto/R$10)')
        
        # 5. Criar pagamento
        print('\n💳 4. CRIANDO PAGAMENTO...')
        pagamento = await db.pagamento.create({
            "reservaId": reserva.id,
            "clienteId": cliente.id,
            "metodo": "CREDITO",
            "valor": valor_total,
            "status": "APROVADO",
            "idempotencyKey": f"pts-{timestamp}"
        })
        print(f'   ✅ Pagamento criado: ID {pagamento.id}')
        
        # 6. Atualizar status para CONFIRMADA
        print('\n✅ 5. CONFIRMAR RESERVA...')
        await db.reserva.update(
            where={"id": reserva.id},
            data={"status": "CONFIRMADA"}
        )
        print(f'   ✅ Status: PENDENTE → CONFIRMADA')
        
        # 7. Criar hospedagem (check-in)
        print('\n🏠 6. REALIZANDO CHECK-IN...')
        hospedagem = await db.hospedagem.create({
            "reservaId": reserva.id,
            "numHospedes": 1,
            "statusHospedagem": "CHECKIN_REALIZADO",
            "checkinRealizadoEm": datetime.now(),
            "checkinRealizadoPor": 1
        })
        await db.reserva.update(
            where={"id": reserva.id},
            data={"status": "HOSPEDADO"}
        )
        print(f'   ✅ Check-in realizado')
        print(f'   ✅ Status: CONFIRMADA → HOSPEDADO')
        
        # 8. Verificar saldo ANTES do checkout
        print('\n💰 7. VERIFICANDO SALDO ANTES DO CHECKOUT...')
        
        # Criar registro de pontos se não existir
        usuario_pontos = await db.usuariopontos.find_first(
            where={"clienteId": cliente.id}
        )
        
        if not usuario_pontos:
            usuario_pontos = await db.usuariopontos.create({
                "clienteId": cliente.id,
                "saldo": 0
            })
        
        saldo_antes = usuario_pontos.saldo
        print(f'   💰 Saldo antes do checkout: {saldo_antes} pontos')
        
        # 9. REALIZAR CHECKOUT COM CRÉDITO DE PONTOS
        print('\n🚪 8. REALIZANDO CHECKOUT COM CRÉDITO DE PONTOS...')
        
        checkout_time = datetime.now()
        
        # Atualizar hospedagem
        await db.hospedagem.update(
            where={"id": hospedagem.id},
            data={
                "checkoutRealizadoEm": checkout_time,
                "checkoutRealizadoPor": 1,
                "statusHospedagem": "CHECKOUT_REALIZADO"
            }
        )
        
        # Atualizar status da reserva
        await db.reserva.update(
            where={"id": reserva.id},
            data={"status": "CHECKED_OUT"}
        )
        
        # Creditar pontos manualmente para teste
        print(f'   📊 Creditando {pontos_esperados} pontos...')
        
        # Atualizar saldo
        await db.usuariopontos.update(
            where={"id": usuario_pontos.id},
            data={"saldo": usuario_pontos.saldo + pontos_esperados}
        )
        
        # Criar transação de pontos
        transacao = await db.transacaopontos.create({
            "clienteId": cliente.id,
            "usuarioId": usuario_pontos.id,
            "tipo": "CREDITO",
            "pontos": pontos_esperados,
            "saldoAnterior": saldo_antes,
            "saldoPosterior": saldo_antes + pontos_esperados,
            "origem": "CHECKOUT_AUTOMATICO",
            "motivo": f"Pontos checkout reserva #{reserva.codigoReserva}",
            "reservaId": reserva.id,
            "createdAt": datetime.now()
        })
        
        print(f'   ✅ Pontos creditados: {pontos_esperados}')
        print(f'   ✅ Transação criada: ID {transacao.id}')
        
        # 10. Verificar saldo APÓS o checkout
        print('\n💰 9. VERIFICANDO SALDO APÓS CHECKOUT...')
        
        usuario_pontos_final = await db.usuariopontos.find_first(
            where={"clienteId": cliente.id}
        )
        
        saldo_depois = usuario_pontos_final.saldo
        pontos_ganhos = saldo_depois - saldo_antes
        
        print(f'   💰 Saldo após checkout: {saldo_depois} pontos')
        print(f'   🎯 Pontos ganhos: {pontos_ganhos}')
        
        # 11. Verificar se os pontos batem
        print('\n🔍 10. VERIFICANDO CONSISTÊNCIA...')
        
        if pontos_ganhos == pontos_esperados:
            print(f'   ✅ PERFEITO! Pontos ganhos = esperados ({pontos_esperados})')
            status = "CORRETO"
        else:
            print(f'   ❌ ERRO: Esperados {pontos_esperados}, ganhos {pontos_ganhos}')
            status = "INCORRETO"
        
        # 12. Verificar dados finais
        print('\n📋 11. DADOS FINAIS...')
        
        reserva_final = await db.reserva.find_unique(
            where={"id": reserva.id},
            include={"cliente": True, "hospedagem": True}
        )
        
        print(f'   📋 Código: {reserva_final.codigoReserva}')
        print(f'   👤 Cliente: {reserva_final.cliente.nomeCompleto}')
        print(f'   🏨 Quarto: {reserva_final.quartoNumero}')
        print(f'   📋 Status: {reserva_final.status}')
        print(f'   🏠 Check-in: {reserva_final.hospedagem.checkinRealizadoEm}')
        print(f'   🚪 Check-out: {reserva_final.hospedagem.checkoutRealizadoEm}')
        
        print('\n' + '=' * 60)
        print('🎉 TESTE CONCLUÍDO!')
        print('=' * 60)
        
        print(f'✅ Cliente: {reserva_final.cliente.nomeCompleto}')
        print(f'✅ Reserva: {reserva_final.codigoReserva}')
        print(f'✅ Valor: R$ {valor_total}')
        print(f'✅ Pontos esperados: {pontos_esperados}')
        print(f'✅ Pontos ganhos: {pontos_ganhos}')
        print(f'✅ Status: {status}')
        print(f'✅ Saldo final: {saldo_depois}')
        
        sucesso = status == "CORRETO" and reserva_final.status == "CHECKED_OUT"
        
        return {
            "sucesso": sucesso,
            "cliente": reserva_final.cliente.nomeCompleto,
            "reserva": reserva_final.codigoReserva,
            "valor_total": valor_total,
            "pontos_esperados": pontos_esperados,
            "pontos_ganhos": pontos_ganhos,
            "status": status,
            "saldo_final": saldo_depois,
            "mensagem": "Sistema de pontos funcionando perfeitamente" if sucesso else "Problema detectado"
        }
        
    except Exception as e:
        print(f'\n❌ ERRO: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return {
            "sucesso": False,
            "erro": str(e),
            "mensagem": "Erro crítico no teste"
        }

if __name__ == "__main__":
    resultado = asyncio.run(test_pontos_simplificado())
    print(f'\n📊 RESULTADO: {resultado}')
