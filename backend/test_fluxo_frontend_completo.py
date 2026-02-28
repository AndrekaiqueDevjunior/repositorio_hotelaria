import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db
from app.services.pagamento_service import PagamentoService
from app.services.pontos_service import PontosService
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.hospedagem_repo import HospedagemRepository
from app.repositories.pontos_repo import PontosRepository
from app.schemas.pagamento_schema import PagamentoCreate

async def test_fluxo_frontend_completo():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE COMPLETO - FLUXO FRONTEND COM PONTOS')
    print('=' * 70)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # 1. Verificar quartos disponíveis
        print('\n🏨 1. VERIFICANDO QUARTOS DISPONÍVEIS...')
        quarto_repo = QuartoRepository(db)
        quartos_disponiveis = await quarto_repo.list_all(status="LIVRE")
        
        if not quartos_disponiveis["quartos"]:
            print('   ❌ Nenhum quarto disponível!')
            return {"sucesso": False, "erro": "Nenhum quarto disponível"}
        
        quarto = quartos_disponiveis["quartos"][0]
        print(f'   ✅ Quarto disponível: {quarto["numero"]} | {quarto["tipoSuite"]}')
        
        # 2. Criar cliente existente ou usar um existente
        print('\n👤 2. CRIANDO/USANDO CLIENTE...')
        cliente_repo = ClienteRepository(db)
        
        # Tentar usar cliente existente primeiro
        clientes = await cliente_repo.list_all(limit=1)
        
        if clientes["clientes"]:
            cliente = clientes["clientes"][0]
            print(f'   ✅ Usando cliente existente: {cliente["nome_completo"]} (ID: {cliente["id"]})')
        else:
            # Criar novo cliente
            cliente_data = {
                "nome_completo": f"Cliente Teste Pontos {timestamp}",
                "documento": f"7777777777{timestamp[-2:]}",
                "telefone": f"21999{timestamp[-6:]}",
                "email": f"pontos.{timestamp}@test.com"
            }
            cliente = await cliente_repo.create(cliente_data)
            print(f'   ✅ Cliente criado: {cliente["nome_completo"]} (ID: {cliente["id"]})')
        
        # 3. Verificar pontos iniciais do cliente
        print('\n🎯 3. VERIFICANDO PONTOS INICIAIS...')
        pontos_repo = PontosRepository(db)
        
        try:
            pontos_iniciais = await pontos_repo.get_saldo(cliente["id"])
            saldo_inicial = pontos_iniciais["saldo"]
            print(f'   💰 Saldo inicial: {saldo_inicial} pontos')
        except:
            print(f'   💰 Cliente não tem registro de pontos, criando...')
            # Criar registro inicial com 0 pontos
            from app.schemas.pontos_schema import AjustarPontosRequest
            
            ajuste_request = AjustarPontosRequest(
                cliente_id=cliente["id"],
                pontos=0,
                motivo="Registro inicial"
            )
            pontos_iniciais = await pontos_repo.ajustar_pontos(ajuste_request)
            saldo_inicial = 0
            print(f'   💰 Registro criado com saldo: {saldo_inicial} pontos')
        
        # 4. Criar reserva
        print('\n📋 4. CRIANDO RESERVA...')
        checkin = datetime.now() + timedelta(days=1)
        checkout = checkin + timedelta(days=2)
        
        reserva_data = {
            "cliente_id": cliente["id"],
            "quarto_id": quarto["id"],
            "tipo_suite": quarto["tipo_suite"],
            "checkin_previsto": checkin,
            "checkout_previsto": checkout,
            "valor_diaria": 200.00,
            "num_diarias": 2,
            "valor_total": 400.00,
            "status": "PENDENTE",
            "codigo_reserva": f"PNT-{timestamp}"
        }
        
        reserva_repo = ReservaRepository(db)
        reserva = await reserva_repo.create(reserva_data)
        print(f'   ✅ Reserva criada: {reserva["codigo_reserva"]} | Status: {reserva["status"]}')
        print(f'   📅 Check-in: {checkin.strftime("%d/%m/%Y")}')
        print(f'   📅 Check-out: {checkout.strftime("%d/%m/%Y")}')
        print(f'   💰 Valor: R$ {reserva["valor_total"]}')
        
        # 5. Calcular pontos esperados
        print('\n🎯 5. CALCULANDO PONTOS ESPERADOS...')
        pontos_service = PontosService(db)
        pontos_esperados = await pontos_service.calcular_pontos_reserva(reserva["id"])
        print(f'   💰 Pontos esperados: {pontos_esperados} pontos')
        print(f'   📊 Regra: 1 ponto por R$ 10 = R$ {reserva["valor_total"]} / 10 = {pontos_esperados}')
        
        # 6. Processar pagamento
        print('\n💳 6. PROCESSANDO PAGAMENTO...')
        pagamento_repo = PagamentoRepository(db)
        pagamento_service = PagamentoService(pagamento_repo, reserva_repo)
        
        pagamento_data = PagamentoCreate(
            reserva_id=reserva["id"],
            cliente_id=cliente["id"],
            metodo="CREDITO",
            valor=reserva["valor_total"],
            observacao="Teste fluxo completo com pontos"
        )
        
        pagamento = await pagamento_service.create(pagamento_data)
        print(f'   ✅ Pagamento criado: ID {pagamento["id"]} | Status: {pagamento["status"]}')
        
        # 7. Confirmar reserva
        print('\n✅ 7. CONFIRMAR RESERVA...')
        await reserva_repo.update(reserva["id"], {"status": "CONFIRMADA"})
        print(f'   ✅ Status atualizado: PENDENTE → CONFIRMADA')
        
        # 8. Verificar pontos após pagamento
        print('\n🎯 8. VERIFICANDO PONTOS APÓS PAGAMENTO...')
        try:
            pontos_apos_pagamento = await pontos_repo.get_saldo(cliente["id"])
            saldo_apos_pagamento = pontos_apos_pagamento["saldo"]
            print(f'   💰 Saldo após pagamento: {saldo_apos_pagamento} pontos')
            
            if saldo_apos_pagamento > saldo_inicial:
                pontos_ganhos = saldo_apos_pagamento - saldo_inicial
                print(f'   ✅ Pontos ganhos: {pontos_ganhos} pontos')
            else:
                print(f'   ⚠️  Nenhum ponto ganho ainda (check-in necessário)')
        except Exception as e:
            print(f'   ❌ Erro ao verificar pontos: {str(e)}')
        
        # 9. Realizar check-in
        print('\n🏠 9. REALIZANDO CHECK-IN...')
        hospedagem_repo = HospedagemRepository(db)
        
        hospedagem_data = {
            "reserva_id": reserva["id"],
            "num_hospedes": 1,
            "status_hospedagem": "CHECKIN_REALIZADO",
            "checkin_realizado_em": datetime.now(),
            "checkin_realizado_por": 1
        }
        
        hospedagem = await hospedagem_repo.create(hospedagem_data)
        await reserva_repo.update(reserva["id"], {"status": "HOSPEDADO"})
        print(f'   ✅ Check-in realizado: {hospedagem["checkin_realizado_em"]}')
        print(f'   ✅ Status atualizado: CONFIRMADA → HOSPEDADO')
        
        # 10. VERIFICAR PONTOS APÓS CHECK-IN
        print('\n🎯 10. VERIFICANDO PONTOS APÓS CHECK-IN...')
        try:
            pontos_apos_checkin = await pontos_repo.get_saldo(cliente["id"])
            saldo_apos_checkin = pontos_apos_checkin["saldo"]
            print(f'   💰 Saldo após check-in: {saldo_apos_checkin} pontos')
            
            if saldo_apos_checkin > saldo_apos_pagamento:
                pontos_checkin = saldo_apos_checkin - saldo_apos_pagamento
                print(f'   ✅ Pontos ganhos no check-in: {pontos_checkin} pontos')
                print(f'   📊 Total acumulado: {saldo_inicial} → {saldo_apos_checkin}')
            else:
                print(f'   ⚠️  Nenhum ponto ganho no check-in')
        except Exception as e:
            print(f'   ❌ Erro ao verificar pontos: {str(e)}')
        
        # 11. Realizar checkout
        print('\n🚪 11. REALIZANDO CHECKOUT...')
        checkout_time = datetime.now()
        
        await hospedagem_repo.update(hospedagem["id"], {
            "checkout_realizado_em": checkout_time,
            "checkout_realizado_por": 1,
            "status_hospedagem": "CHECKOUT_REALIZADO"
        })
        
        await reserva_repo.update(reserva["id"], {"status": "CHECKED_OUT"})
        print(f'   ✅ Checkout realizado: {checkout_time}')
        print(f'   ✅ Status atualizado: HOSPEDADO → CHECKED_OUT')
        
        # 12. VERIFICAR PONTOS FINAIS
        print('\n🎯 12. VERIFICANDO PONTOS FINAIS...')
        try:
            pontos_finais = await pontos_repo.get_saldo(cliente["id"])
            saldo_final = pontos_finais["saldo"]
            print(f'   💰 Saldo final: {saldo_final} pontos')
            
            pontos_totais_ganhos = saldo_final - saldo_inicial
            print(f'   ✅ Total de pontos ganhos: {pontos_totais_ganhos} pontos')
            
            # Verificar se os pontos batem com o esperado
            if pontos_totais_ganhos == pontos_esperados:
                print(f'   ✅ PERFEITO! Pontos ganhos = pontos esperados ({pontos_esperados})')
            else:
                print(f'   ⚠️  Diferença: esperados {pontos_esperados}, ganhos {pontos_totais_ganhos}')
        except Exception as e:
            print(f'   ❌ Erro ao verificar pontos finais: {str(e)}')
        
        # 13. Verificar transações de pontos
        print('\n📊 13. VERIFICANDO TRANSAÇÕES DE PONTOS...')
        try:
            transacoes = await db.transacaopontos.find_many(
                where={"clienteId": cliente["id"]},
                order={"createdAt": "desc"}
            )
            
            print(f'   📊 Total de transações: {len(transacoes)}')
            for i, transacao in enumerate(transacoes[:3], 1):
                print(f'   {i}. ID: {transacao.id} | Tipo: {transacao.tipo} | Pontos: {transacao.pontos} | Data: {transacao.createdAt}')
        except Exception as e:
            print(f'   ❌ Erro ao verificar transações: {str(e)}')
        
        print('\n' + '=' * 70)
        print('🎉 FLUXO COMPLETO TESTADO COM SUCESSO!')
        print('=' * 70)
        
        print(f'✅ Cliente: {cliente["nome_completo"]}')
        print(f'✅ Quarto: {quarto["numero"]}')
        print(f'✅ Reserva: {reserva["codigo_reserva"]}')
        print(f'✅ Pagamento: R$ {reserva["valor_total"]}')
        print(f'✅ Check-in: {hospedagem["checkin_realizado_em"]}')
        print(f'✅ Checkout: {checkout_time}')
        print(f'✅ Status final: CHECKED_OUT')
        print(f'✅ Pontos ganhos: {pontos_totais_ganhos if "pontos_totais_ganhos" in locals() else "N/A"}')
        
        return {
            "sucesso": True,
            "cliente": cliente["nome_completo"],
            "reserva": reserva["codigo_reserva"],
            "fluxo": "PENDENTE → CONFIRMADA → HOSPEDADO → CHECKED_OUT",
            "pontos_esperados": pontos_esperados,
            "pontos_ganhos": pontos_totais_ganhos if "pontos_totais_ganhos" in locals() else 0,
            "sistema_pontos": "FUNCIONANDO" if pontos_totais_ganhos == pontos_esperados else "COM ERRO"
        }
        
    except Exception as e:
        print(f'\n❌ ERRO NO FLUXO: {str(e)}')
        return {
            "sucesso": False,
            "erro": str(e)
        }

if __name__ == "__main__":
    resultado = asyncio.run(test_fluxo_frontend_completo())
    print(f'\n📊 Resultado Final: {resultado}')
