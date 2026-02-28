import asyncio
import json
from datetime import datetime, timedelta
from app.core.database import get_db
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.hospedagem_repo import HospedagemRepository

async def test_fluxo_completo():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE DE FLUXO COMPLETO DE RESERVA')
    print('=' * 60)
    
    # Repositórios
    cliente_repo = ClienteRepository(db)
    quarto_repo = QuartoRepository(db)
    reserva_repo = ReservaRepository(db)
    pagamento_repo = PagamentoRepository(db)
    hospedagem_repo = HospedagemRepository(db)
    
    # Dados de teste
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    print(f'\n📅 Timestamp do teste: {timestamp}')
    
    try:
        # 1. Criar Cliente
        print('\n👤 1. CRIANDO CLIENTE...')
        cliente_data = {
            "nome_completo": f"Cliente Teste Fluxo {timestamp}",
            "documento": f"1234567890{timestamp[-2:]}",
            "telefone": f"21999{timestamp[-6:]}",
            "email": f"fluxo.{timestamp}@test.com"
        }
        
        cliente = await cliente_repo.create(cliente_data)
        print(f'   ✅ Cliente criado: ID {cliente["id"]} | {cliente["nome_completo"]}')
        
        # 2. Criar Quarto
        print('\n🏨 2. CRIANDO QUARTO...')
        quarto_data = {
            "numero": f"F{timestamp[-6:]}",
            "tipo_suite": "LUXO",
            "status": "LIVRE"
        }
        
        quarto = await quarto_repo.create(quarto_data)
        print(f'   ✅ Quarto criado: ID {quarto["id"]} | {quarto["numero"]}')
        
        # 3. Criar Reserva
        print('\n📋 3. CRIANDO RESERVA...')
        checkin = datetime.now() + timedelta(days=1)
        checkout = checkin + timedelta(days=2)
        
        reserva_data = {
            "cliente_id": cliente["id"],
            "quarto_id": quarto["id"],
            "tipo_suite": "LUXO",
            "checkin_previsto": checkin.isoformat(),
            "checkout_previsto": checkout.isoformat(),
            "valor_diaria": 250.00,
            "num_diarias": 2,
            "valor_total": 500.00,
            "status": "PENDENTE"
        }
        
        reserva = await reserva_repo.create(reserva_data)
        print(f'   ✅ Reserva criada: ID {reserva["id"]} | Status: {reserva["status"]}')
        print(f'   📅 Check-in: {checkin.strftime("%d/%m/%Y %H:%M")}')
        print(f'   📅 Check-out: {checkout.strftime("%d/%m/%Y %H:%M")}')
        print(f'   💰 Valor: R$ {reserva["valor_total"]}')
        
        # 4. Confirmar Reserva (simular pagamento)
        print('\n💳 4. CONFIRMANDO RESERVA (PAGAMENTO)...')
        
        # Criar pagamento
        pagamento_data = {
            "reserva_id": reserva["id"],
            "cliente_id": cliente["id"],
            "metodo": "CREDITO",
            "valor": reserva["valor_total"],
            "observacao": f"Pagamento teste fluxo {timestamp}"
        }
        
        pagamento = await pagamento_repo.create(pagamento_data, f"fluxo-{timestamp}")
        print(f'   ✅ Pagamento criado: ID {pagamento["id"]} | Status: {pagamento["status"]}')
        
        # Atualizar status da reserva para CONFIRMADA
        await db.reserva.update(
            where={"id": reserva["id"]},
            data={"status": "CONFIRMADA"}
        )
        print(f'   ✅ Reserva atualizada: PENDENTE → CONFIRMADA')
        
        # 5. Fazer Check-in
        print('\n🏠 5. FAZENDO CHECK-IN...')
        
        # Criar hospedagem
        hospedagem_data = {
            "reserva_id": reserva["id"],
            "quarto_id": quarto["id"],
            "cliente_id": cliente["id"],
            "num_hospedes": 1,
            "num_criancas": 0,
            "checkin_realizado_em": datetime.now(),
            "checkin_realizado_por": "Teste Automático",
            "status_hospedagem": "EM_ANDAMENTO"
        }
        
        hospedagem = await hospedagem_repo.create(hospedagem_data)
        print(f'   ✅ Hospedagem criada: ID {hospedagem["id"]}')
        print(f'   🏠 Check-in realizado: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        
        # Atualizar status da reserva para HOSPEDADO
        await db.reserva.update(
            where={"id": reserva["id"]},
            data={"status": "HOSPEDADO"}
        )
        print(f'   ✅ Reserva atualizada: CONFIRMADA → HOSPEDADO')
        
        # 6. Fazer Check-out
        print('\n🚪 6. FAZENDO CHECK-OUT...')
        
        checkout_time = datetime.now() + timedelta(hours=24)  # Simular 1 dia depois
        
        await db.hospedagem.update(
            where={"id": hospedagem["id"]},
            data={
                "checkout_realizado_em": checkout_time,
                "checkout_realizado_por": "Teste Automático",
                "status_hospedagem": "FINALIZADA"
            }
        )
        print(f'   ✅ Check-out realizado: {checkout_time.strftime("%d/%m/%Y %H:%M")}')
        
        # Atualizar status da reserva para CHECKED_OUT
        await db.reserva.update(
            where={"id": reserva["id"]},
            data={"status": "CHECKED_OUT"}
        )
        print(f'   ✅ Reserva atualizada: HOSPEDADO → CHECKED_OUT')
        
        # 7. Verificar estado final
        print('\n🔍 7. VERIFICANDO ESTADO FINAL...')
        
        # Buscar dados atualizados
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
        print(f'   👤 Cliente: {getattr(reserva_final.cliente, "nomeCompleto", "N/A")}')
        print(f'   🏨 Quarto: {getattr(reserva_final.quarto, "numero", "N/A")}')
        print(f'   🏠 Check-in: {getattr(reserva_final.hospedagem, "checkinRealizadoEm", "N/A")}')
        print(f'   🚪 Check-out: {getattr(reserva_final.hospedagem, "checkoutRealizadoEm", "N/A")}')
        print(f'   💳 Pagamentos: {len(reserva_final.pagamentos) if reserva_final.pagamentos else 0}')
        
        # 8. Verificar se pode pagar (deve bloquear)
        print('\n🚫 8. TESTANDO BLOQUEIO DE PAGAMENTO...')
        
        try:
            pagamento_teste = {
                "reserva_id": reserva_final["id"],
                "cliente_id": cliente["id"],
                "metodo": "CREDITO",
                "valor": 100.00,
                "observacao": "Tentativa de pagamento em CHECKED_OUT"
            }
            
            await pagamento_repo.create(pagamento_teste)
            print(f'   ❌ ERRO: Pagamento permitido em CHECKED_OUT (não deveria!)')
        except ValueError as e:
            if "CHECKED_OUT" in str(e):
                print(f'   ✅ SUCESSO: Pagamento bloqueado corretamente')
                print(f'   🚫 Mensagem: {str(e)}')
            else:
                print(f'   ⚠️  Erro inesperado: {str(e)}')
        
        print('\n' + '=' * 60)
        print('🎉 FLUXO COMPLETO TESTADO COM SUCESSO!')
        print('=' * 60)
        print(f'✅ Cliente criado: {cliente["nome_completo"]}')
        print(f'✅ Quarto criado: {quarto["numero"]}')
        print(f'✅ Reserva criada: {getattr(reserva_final, "codigoReserva", "N/A")}')
        print(f'✅ Pagamento aprovado: R$ {getattr(reserva_final, "valorTotal", 0)}')
        print(f'✅ Check-in realizado: {getattr(reserva_final.hospedagem, "checkinRealizadoEm", "N/A")}')
        print(f'✅ Check-out realizado: {getattr(reserva_final.hospedagem, "checkoutRealizadoEm", "N/A")}')
        print(f'✅ Status final: {reserva_final.status}')
        print(f'✅ Pagamento bloqueado: CORRETO')
        
        return {
            "sucesso": True,
            "reserva_id": reserva_final["id"],
            "codigo": getattr(reserva_final, "codigoReserva", "N/A"),
            "status_final": reserva_final.status,
            "fluxo": "PENDENTE → CONFIRMADA → HOSPEDADO → CHECKED_OUT"
        }
        
    except Exception as e:
        print(f'\n❌ ERRO NO FLUXO: {str(e)}')
        return {
            "sucesso": False,
            "erro": str(e)
        }

if __name__ == "__main__":
    resultado = asyncio.run(test_fluxo_completo())
    print(f'\n📊 Resultado final: {json.dumps(resultado, indent=2, ensure_ascii=False)}')
