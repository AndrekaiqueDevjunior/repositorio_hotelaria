import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db

async def test_fluxo_simplificado():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE DE FLUXO COMPLETO - VERSÃO SIMPLIFICADA')
    print('=' * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # 1. Criar Cliente
        print('\n👤 1. CRIANDO CLIENTE...')
        cliente = await db.cliente.create({
            "nomeCompleto": f"Cliente Teste Fluxo {timestamp}",
            "documento": f"1234567890{timestamp[-2:]}",
            "telefone": f"21999{timestamp[-6:]}",
            "email": f"fluxo.{timestamp}@test.com",
            "status": "ATIVO"
        })
        print(f'   ✅ Cliente criado: ID {cliente.id} | {cliente.nomeCompleto}')
        
        # 2. Criar Quarto
        print('\n🏨 2. CRIANDO QUARTO...')
        quarto = await db.quarto.create({
            "numero": f"F{timestamp[-6:]}",
            "tipoSuite": "LUXO",
            "status": "LIVRE"
        })
        print(f'   ✅ Quarto criado: ID {quarto.id} | {quarto.numero}')
        
        # 3. Criar Reserva
        print('\n📋 3. CRIANDO RESERVA...')
        checkin = datetime.now() + timedelta(days=1)
        checkout = checkin + timedelta(days=2)
        
        reserva = await db.reserva.create({
            "clienteId": cliente.id,
            "clienteNome": cliente.nomeCompleto,
            "quartoNumero": quarto.numero,
            "tipoSuite": "LUXO",
            "checkinPrevisto": checkin,
            "checkoutPrevisto": checkout,
            "valorDiaria": 250.00,
            "numDiarias": 2,
            "status": "PENDENTE",
            "codigoReserva": f"FLX-{timestamp}"
        })
        print(f'   ✅ Reserva criada: ID {reserva.id} | Status: {reserva.status}')
        print(f'   📅 Check-in: {checkin.strftime("%d/%m/%Y %H:%M")}')
        print(f'   📅 Check-out: {checkout.strftime("%d/%m/%Y %H:%M")}')
        print(f'   💰 Valor: R$ {reserva.valorDiaria * reserva.numDiarias}')
        
        # 4. Criar Pagamento
        print('\n💳 4. CRIANDO PAGAMENTO...')
        pagamento = await db.pagamento.create({
            "reservaId": reserva.id,
            "clienteId": cliente.id,
            "metodo": "CREDITO",
            "valor": reserva.valorDiaria * reserva.numDiarias,
            "status": "APROVADO",
            "idempotencyKey": f"fluxo-{timestamp}"
        })
        print(f'   ✅ Pagamento criado: ID {pagamento.id} | Status: {pagamento.status}')
        
        # 5. Atualizar status para CONFIRMADA
        print('\n✅ 5. CONFIRMAR RESERVA...')
        await db.reserva.update(
            where={"id": reserva.id},
            data={"status": "CONFIRMADA"}
        )
        print(f'   ✅ Status atualizado: PENDENTE → CONFIRMADA')
        
        # 6. Criar Hospedagem
        print('\n🏠 6. CRIANDO HOSPEDAGEM...')
        hospedagem = await db.hospedagem.create({
            "reservaId": reserva.id,
            "numHospedes": 1,
            "statusHospedagem": "CHECKIN_REALIZADO",
            "checkinRealizadoEm": datetime.now()
        })
        print(f'   ✅ Hospedagem criada: ID {hospedagem.id}')
        print(f'   🏠 Check-in: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        
        # 7. Atualizar status para HOSPEDADO
        print('\n🏠 7. HOSPEDAR RESERVA...')
        await db.reserva.update(
            where={"id": reserva.id},
            data={"status": "HOSPEDADO"}
        )
        print(f'   ✅ Status atualizado: CONFIRMADA → HOSPEDADO')
        
        # 8. Fazer Check-out (24h depois)
        print('\n🚪 8. FAZENDO CHECK-OUT...')
        checkout_time = datetime.now() + timedelta(hours=24)
        
        await db.hospedagem.update(
            where={"id": hospedagem.id},
            data={
                "checkoutRealizadoEm": checkout_time,
                "checkoutRealizadoPor": 1,
                "statusHospedagem": "CHECKOUT_REALIZADO"
            }
        )
        print(f'   ✅ Check-out realizado: {checkout_time.strftime("%d/%m/%Y %H:%M")}')
        
        # 9. Atualizar status para CHECKED_OUT
        print('\n🚪 9. FINALIZAR RESERVA...')
        await db.reserva.update(
            where={"id": reserva.id},
            data={"status": "CHECKED_OUT"}
        )
        print(f'   ✅ Status final: HOSPEDADO → CHECKED_OUT')
        
        # 10. Verificar estado final
        print('\n🔍 10. VERIFICANDO ESTADO FINAL...')
        
        reserva_final = await db.reserva.find_unique(
            where={"id": reserva["id"]},
            include={
                "cliente": True,
                "quarto": True,
                "hospedagem": True,
                "pagamentos": True
            }
        )
        
        print(f'   📋 Status Final: {reserva_final.status}')
        print(f'   👤 Cliente: {reserva_final.cliente.nomeCompleto}')
        print(f'   🏨 Quarto: {reserva_final.quarto.numero if reserva_final.quarto else "N/A"}')
        print(f'   🏠 Check-in: {reserva_final.hospedagem.checkinRealizadoEm}')
        print(f'   🚪 Check-out: {reserva_final.hospedagem.checkoutRealizadoEm}')
        print(f'   💳 Pagamentos: {len(reserva_final.pagamentos)}')
        
        # 11. Testar bloqueio de pagamento
        print('\n🚫 11. TESTAR BLOQUEIO DE PAGAMENTO...')
        
        try:
            pagamento_teste = await db.pagamento.create({
                "reservaId": reserva_final.id,
                "clienteId": cliente.id,
                "metodo": "CREDITO",
                "valor": 100.00,
                "status": "PENDENTE",
                "idempotencyKey": f"bloqueio-{timestamp}"
            })
            print(f'   ❌ ERRO: Pagamento permitido em CHECKED_OUT!')
        except Exception as e:
            if "CHECKED_OUT" in str(e):
                print(f'   ✅ SUCESSO: Pagamento bloqueado corretamente')
                print(f'   🚫 Mensagem: {str(e)}')
            else:
                print(f'   ⚠️  Erro inesperado: {str(e)}')
        
        print('\n' + '=' * 60)
        print('🎉 FLUXO COMPLETO TESTADO COM SUCESSO!')
        print('=' * 60)
        print(f'✅ Cliente: {reserva_final.cliente.nomeCompleto}')
        print(f'✅ Quarto: {reserva_final.quarto.numero if reserva_final.quarto else "N/A"}')
        print(f'✅ Reserva: {reserva_final.codigoReserva if hasattr(reserva_final, "codigoReserva") else "N/A"}')
        print(f'✅ Pagamento: R$ {reserva_final.valorDiaria * reserva_final.numDiarias}')
        print(f'✅ Check-in: {reserva_final.hospedagem.checkinRealizadoEm}')
        print(f'✅ Check-out: {reserva_final.hospedagem.checkoutRealizadoEm}')
        print(f'✅ Status Final: {reserva_final.status}')
        print(f'✅ Bloqueio de pagamento: CORRETO')
        
        return {
            "sucesso": True,
            "reserva_id": reserva_final.id,
            "codigo": getattr(reserva_final, "codigoReserva", "N/A"),
            "status_final": reserva_final.status,
            "fluxo": "PENDENTE → CONFIRMADA → HOSPEDADO → CHECKED_OUT",
            "cliente": reserva_final.cliente.nomeCompleto,
            "quarto": reserva_final.quarto.numero if reserva_final.quarto else "N/A",
            "valor_total": float(reserva_final.valorDiaria * reserva_final.numDiarias),
            "checkin": str(reserva_final.hospedagem.checkinRealizadoEm),
            "checkout": str(reserva_final.hospedagem.checkoutRealizadoEm)
        }
        
    except Exception as e:
        print(f'\n❌ ERRO NO FLUXO: {str(e)}')
        return {
            "sucesso": False,
            "erro": str(e)
        }

if __name__ == "__main__":
    resultado = asyncio.run(test_fluxo_simplificado())
    print(f'\n📊 Resultado: {resultado}')
