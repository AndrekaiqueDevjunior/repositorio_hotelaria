import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db
from app.services.pagamento_service import PagamentoService
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.hospedagem_repo import HospedagemRepository
from app.repositories.pontos_repo import PontosRepository
from app.schemas.pagamento_schema import PagamentoCreate

async def test_pontos_checkout_real():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE REAL - SISTEMA DE PONTOS NO CHECKOUT')
    print('=' * 70)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # 1. Criar cliente de teste
        print('\n👤 1. CRIANDO CLIENTE DE TESTE...')
        cliente_repo = ClienteRepository(db)
        
        cliente_data = {
            "nome_completo": f"Cliente Pontos Real {timestamp}",
            "documento": f"9999999999{timestamp[-2:]}",
            "telefone": f"21999{timestamp[-6:]}",
            "email": f"pontos.real.{timestamp}@test.com"
        }
        
        cliente = await cliente_repo.create(cliente_data)
        print(f'   ✅ Cliente criado: {cliente["nome_completo"]} (ID: {cliente["id"]})')
        
        # 2. Verificar saldo inicial do cliente
        print('\n💰 2. VERIFICANDO SALDO INICIAL...')
        pontos_repo = PontosRepository(db)
        
        try:
            saldo_inicial = await pontos_repo.get_saldo(cliente["id"])
            if not saldo_inicial["success"]:
                # Criar registro inicial
                from app.schemas.pontos_schema import AjustarPontosRequest
                ajuste = AjustarPontosRequest(
                    cliente_id=cliente["id"],
                    pontos=0,
                    motivo="Registro inicial"
                )
                await pontos_repo.ajustar_pontos(ajuste)
                saldo_inicial = await pontos_repo.get_saldo(cliente["id"])
            
            saldo_inicial_valor = saldo_inicial["saldo"]
            print(f'   💰 Saldo inicial: {saldo_inicial_valor} pontos')
        except Exception as e:
            print(f'   ❌ Erro ao verificar saldo inicial: {e}')
            saldo_inicial_valor = 0
        
        # 3. Criar quarto disponível
        print('\n🏨 3. CRIANDO QUARTO...')
        quarto_repo = QuartoRepository(db)
        
        quarto_data = {
            "numero": f"P{timestamp[-6:]}",
            "tipo_suite": "LUXO",
            "status": "LIVRE"
        }
        
        quarto = await quarto_repo.create(quarto_data)
        print(f'   ✅ Quarto criado: {quarto["numero"]} (ID: {quarto["id"]})')
        
        # 4. Criar reserva
        print('\n📋 4. CRIANDO RESERVA...')
        checkin = datetime.now() - timedelta(days=1)
        checkout = checkin + timedelta(days=3)  # 3 diárias
        
        reserva_data = {
            "cliente_id": cliente["id"],
            "quarto_id": quarto["id"],
            "tipo_suite": quarto["tipo_suite"],
            "checkin_previsto": checkin,
            "checkout_previsto": checkout,
            "valor_diaria": 150.00,  # R$ 150 por diária
            "num_diarias": 3,
            "status": "PENDENTE",
            "codigo_reserva": f"PNT-{timestamp}"
        }
        
        reserva_repo = ReservaRepository(db)
        reserva = await reserva_repo.create(reserva_data)
        
        valor_total = reserva["valor_diaria"] * reserva["num_diarias"]
        pontos_esperados = int(valor_total / 10)  # R$ 450 = 45 pontos
        
        print(f'   ✅ Reserva criada: {reserva["codigo_reserva"]}')
        print(f'   💰 Valor total: R$ {valor_total}')
        print(f'   🎯 Pontos esperados: {pontos_esperados} (1 ponto/R$10)')
        
        # 5. Processar pagamento
        print('\n💳 5. PROCESSANDO PAGAMENTO...')
        pagamento_repo = PontosRepository(db)
        pagamento_service = PagamentoService(pagamento_repo, reserva_repo)
        
        pagamento_data = PagamentoCreate(
            reserva_id=reserva["id"],
            cliente_id=cliente["id"],
            metodo="CREDITO",
            valor=valor_total,
            observacao="Teste real sistema de pontos"
        )
        
        pagamento = await pagamento_service.create(pagamento_data)
        print(f'   ✅ Pagamento criado: ID {pagamento["id"]} | Status: {pagamento["status"]}')
        
        # 6. Confirmar reserva
        print('\n✅ 6. CONFIRMAR RESERVA...')
        await reserva_repo.update(reserva["id"], {"status": "CONFIRMADA"})
        print(f'   ✅ Status: PENDENTE → CONFIRMADA')
        
        # 7. Realizar check-in
        print('\n🏠 7. REALIZANDO CHECK-IN...')
        hospedagem_repo = HospedagemRepository(db)
        
        hospedagem_data = {
            "reserva_id": reserva["id"],
            "num_hospedes": 2,
            "status_hospedagem": "CHECKIN_REALIZADO",
            "checkin_realizado_em": datetime.now(),
            "checkin_realizado_por": 1
        }
        
        hospedagem = await hospedagem_repo.create(hospedagem_data)
        await reserva_repo.update(reserva["id"], {"status": "HOSPEDADO"})
        print(f'   ✅ Check-in realizado: {hospedagem["checkin_realizado_em"]}')
        print(f'   ✅ Status: CONFIRMADA → HOSPEDADO')
        
        # 8. Verificar pontos ANTES do checkout
        print('\n💰 8. VERIFICANDO PONTOS ANTES DO CHECKOUT...')
        try:
            pontos_antes_checkout = await pontos_repo.get_saldo(cliente["id"])
            saldo_antes_checkout = pontos_antes_checkout["saldo"]
            print(f'   💰 Saldo antes do checkout: {saldo_antes_checkout} pontos')
            
            if saldo_antes_checkout > saldo_inicial_valor:
                pontos_ganhos_antes = saldo_antes_checkout - saldo_inicial_valor
                print(f'   ⚠️  ATENÇÃO: Já ganhou {pontos_ganhos_antes} pontos antes do checkout!')
            else:
                print(f'   ✅ Nenhum ponto ganho ainda (esperado)')
        except Exception as e:
            print(f'   ❌ Erro ao verificar pontos antes: {e}')
            saldo_antes_checkout = saldo_inicial_valor
        
        # 9. REALIZAR CHECKOUT (TESTE CRÍTICO)
        print('\n🚪 9. REALIZANDO CHECKOUT (TESTE DE PONTOS)...')
        
        # Usar o método checkout do ReservaRepository (que deve creditar pontos)
        resultado_checkout = await reserva_repo.checkout(reserva["id"])
        
        print(f'   ✅ Checkout realizado')
        print(f'   📋 Status final: {resultado_checkout["status"]}')
        
        # 10. VERIFICAR PONTOS APÓS CHECKOUT
        print('\n💰 10. VERIFICANDO PONTOS APÓS CHECKOUT...')
        try:
            pontos_apos_checkout = await pontos_repo.get_saldo(cliente["id"])
            saldo_apos_checkout = pontos_apos_checkout["saldo"]
            print(f'   💰 Saldo após checkout: {saldo_apos_checkout} pontos')
            
            # Calcular pontos ganhos no checkout
            pontos_ganhos_checkout = saldo_apos_checkout - saldo_antes_checkout
            print(f'   🎯 Pontos ganhos no checkout: {pontos_ganhos_checkout}')
            
            # Verificar se bate com o esperado
            if pontos_ganhos_checkout == pontos_esperados:
                print(f'   ✅ PERFEITO! Pontos ganhos = esperados ({pontos_esperados})')
                status_pontos = "CORRETO"
            elif pontos_ganhos_checkout > 0:
                print(f'   ⚠️  Pontos ganhos, mas valor diferente:')
                print(f'      Esperado: {pontos_esperados}')
                print(f'      Ganho: {pontos_ganhos_checkout}')
                status_pontos = "DIFERENTE"
            else:
                print(f'   ❌ ERRO: Nenhum ponto ganho no checkout!')
                status_pontos = "ERRO"
                
        except Exception as e:
            print(f'   ❌ Erro ao verificar pontos após checkout: {e}')
            pontos_ganhos_checkout = 0
            status_pontos = "ERRO_VERIFICACAO"
        
        # 11. VERIFICAR TRANSAÇÕES DE PONTOS
        print('\n📊 11. VERIFICANDO TRANSAÇÕES DE PONTOS...')
        try:
            transacoes = await db.transacaopontos.find_many(
                where={"clienteId": cliente["id"]},
                order={"createdAt": "desc"},
                take=5
            )
            
            print(f'   📊 Total de transações: {len(transacoes)}')
            
            for i, transacao in enumerate(transacoes[:3], 1):
                print(f'   {i}. ID: {transacao.id}')
                print(f'      Tipo: {transacao.tipo}')
                print(f'      Pontos: {transacao.pontos}')
                print(f'      Origem: {transacao.origem}')
                print(f'      Motivo: {transacao.motivo}')
                print(f'      Data: {transacao.createdAt}')
                print()
                
        except Exception as e:
            print(f'   ❌ Erro ao verificar transações: {e}')
        
        # 12. VERIFICAR STATUS FINAL DA RESERVA
        print('\n📋 12. VERIFICANDO STATUS FINAL...')
        reserva_final = await db.reserva.find_unique(
            where={"id": reserva["id"]},
            include={"cliente": True, "hospedagem": True}
        )
        
        print(f'   📋 Código: {reserva_final.codigoReserva}')
        print(f'   👤 Cliente: {reserva_final.cliente.nomeCompleto}')
        print(f'   🏨 Quarto: {reserva_final.quartoNumero}')
        print(f'   📋 Status: {reserva_final.status}')
        print(f'   🏠 Check-in: {reserva_final.hospedagem.checkinRealizadoEm}')
        print(f'   🚪 Check-out: {reserva_final.hospedagem.checkoutRealizadoEm}')
        
        # 13. RESUMO FINAL
        print('\n' + '=' * 70)
        print('🎉 TESTE REAL CONCLUÍDO!')
        print('=' * 70)
        
        print(f'✅ Cliente: {cliente["nome_completo"]}')
        print(f'✅ Reserva: {reserva["codigo_reserva"]}')
        print(f'✅ Valor: R$ {valor_total}')
        print(f'✅ Diárias: {reserva["num_diarias"]}')
        print(f'✅ Pontos esperados: {pontos_esperados}')
        print(f'✅ Pontos ganhos: {pontos_ganhos_checkout}')
        print(f'✅ Status pontos: {status_pontos}')
        print(f'✅ Saldo final: {saldo_apos_checkout}')
        
        # Verificação final
        sucesso_total = (
            status_pontos == "CORRETO" and
            reserva_final["status"] == "CHECKED_OUT" and
            pontos_ganhos_checkout > 0
        )
        
        return {
            "sucesso": sucesso_total,
            "cliente": cliente["nome_completo"],
            "reserva": reserva["codigo_reserva"],
            "valor_total": valor_total,
            "pontos_esperados": pontos_esperados,
            "pontos_ganhos": pontos_ganhos_checkout,
            "status_pontos": status_pontos,
            "saldo_final": saldo_apos_checkout,
            "fluxo": "PENDENTE → CONFIRMADA → HOSPEDADO → CHECKED_OUT",
            "mensagem": "Sistema de pontos funcionando perfeitamente" if sucesso_total else "Problema detectado"
        }
        
    except Exception as e:
        print(f'\n❌ ERRO NO TESTE: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return {
            "sucesso": False,
            "erro": str(e),
            "mensagem": "Erro crítico no teste"
        }

if __name__ == "__main__":
    resultado = asyncio.run(test_pontos_checkout_real())
    print(f'\n📊 RESULTADO FINAL: {resultado}')
