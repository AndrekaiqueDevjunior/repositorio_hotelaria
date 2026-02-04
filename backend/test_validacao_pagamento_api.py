import asyncio
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.database import get_db
from app.services.pagamento_service import PagamentoService
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.schemas.pagamento_schema import PagamentoCreate

async def test_validacao_pagamento_api():
    db = get_db()
    await db.connect()
    
    print('🧪 TESTE DE VALIDAÇÃO DE PAGAMENTO VIA API')
    print('=' * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f'📅 Timestamp: {timestamp}')
    
    try:
        # 1. Criar dados de teste
        print('\n👤 1. CRIANDO CLIENTE...')
        cliente = await db.cliente.create({
            "nomeCompleto": f"Cliente Teste Validacao {timestamp}",
            "documento": f"987654321{timestamp[-2:]}",
            "telefone": f"21999{timestamp[-6:]}",
            "email": f"validacao.{timestamp}@test.com",
            "status": "ATIVO"
        })
        print(f'   ✅ Cliente criado: ID {cliente.id}')
        
        print('\n🏨 2. CRIANDO QUARTO...')
        quarto = await db.quarto.create({
            "numero": f"V{timestamp[-6:]}",
            "tipoSuite": "LUXO",
            "status": "LIVRE"
        })
        print(f'   ✅ Quarto criado: ID {quarto.id}')
        
        print('\n📋 3. CRIANDO RESERVA CHECKED_OUT...')
        checkin = datetime.now() - timedelta(days=5)
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
            "status": "CHECKED_OUT",  # Status que deve bloquear pagamento
            "codigoReserva": f"VAL-{timestamp}"
        })
        print(f'   ✅ Reserva criada: ID {reserva.id} | Status: {reserva.status}')
        
        # 4. Criar hospedagem para consistência
        print('\n🏠 4. CRIANDO HOSPEDAGEM...')
        hospedagem = await db.hospedagem.create({
            "reservaId": reserva.id,
            "numHospedes": 1,
            "statusHospedagem": "CHECKOUT_REALIZADO",
            "checkinRealizadoEm": checkin,
            "checkoutRealizadoEm": checkout
        })
        print(f'   ✅ Hospedagem criada: ID {hospedagem.id}')
        
        # 5. Testar validação via API (service)
        print('\n🚫 5. TESTANDO VALIDAÇÃO VIA API...')
        
        # Criar serviço
        pagamento_repo = PagamentoRepository(db)
        reserva_repo = ReservaRepository(db)
        pagamento_service = PagamentoService(pagamento_repo, reserva_repo)
        
        # Criar dados de pagamento
        pagamento_data = PagamentoCreate(
            reserva_id=reserva.id,
            cliente_id=cliente.id,
            metodo="CREDITO",
            valor=100.00,
            observacao="Teste de validação CHECKED_OUT"
        )
        
        print(f'   📋 Tentando criar pagamento para reserva CHECKED_OUT...')
        print(f'   📋 Reserva ID: {reserva.id}')
        print(f'   📋 Status: {reserva.status}')
        
        try:
            # Tentar criar pagamento via serviço
            resultado = await pagamento_service.create(pagamento_data)
            print(f'   ❌ ERRO: Pagamento criado indevidamente!')
            print(f'   📋 Resultado: {resultado}')
            return {
                "sucesso": False,
                "erro": "Validação não funcionou - pagamento criado indevidamente"
            }
            
        except ValueError as e:
            if "CHECKED_OUT" in str(e):
                print(f'   ✅ SUCESSO: Validação funcionou!')
                print(f'   🚫 Mensagem de erro: {str(e)}')
                
                # 6. Testar com status correto
                print('\n✅ 6. TESTANDO COM STATUS CORRETO...')
                
                # Atualizar reserva para CONFIRMADA
                await db.reserva.update(
                    where={"id": reserva.id},
                    data={"status": "CONFIRMADA"}
                )
                print(f'   📋 Status alterado para: CONFIRMADA')
                
                try:
                    resultado = await pagamento_service.create(pagamento_data)
                    print(f'   ✅ SUCESSO: Pagamento criado para status correto!')
                    print(f'   📋 Pagamento ID: {resultado["id"]}')
                    print(f'   📋 Status: {resultado["status"]}')
                    
                    return {
                        "sucesso": True,
                        "mensagem": "Validação funcionando corretamente",
                        "bloqueio_check_out": "CORRETO",
                        "criacao_confirmada": "CORRETO"
                    }
                    
                except Exception as e:
                    print(f'   ❌ ERRO: Falha ao criar pagamento para status correto: {str(e)}')
                    return {
                        "sucesso": False,
                        "erro": f"Falha ao criar pagamento para status correto: {str(e)}"
                    }
            else:
                print(f'   ⚠️  ERRO INESPERADO: {str(e)}')
                return {
                    "sucesso": False,
                    "erro": f"Erro inesperado na validação: {str(e)}"
                }
                
        except HTTPException as e:
            if "CHECKED_OUT" in str(e.detail):
                print(f'   ✅ SUCESSO: Validação funcionou!')
                print(f'   🚫 Mensagem de erro: {e.detail}')
                
                # 6. Testar com status correto
                print('\n✅ 6. TESTANDO COM STATUS CORRETO...')
                
                # Atualizar reserva para CONFIRMADA
                await db.reserva.update(
                    where={"id": reserva.id},
                    data={"status": "CONFIRMADA"}
                )
                print(f'   📋 Status alterado para: CONFIRMADA')
                
                try:
                    resultado = await pagamento_service.create(pagamento_data)
                    print(f'   ✅ SUCESSO: Pagamento criado para status correto!')
                    print(f'   📋 Pagamento ID: {resultado["id"]}')
                    print(f'   📋 Status: {resultado["status"]}')
                    
                    return {
                        "sucesso": True,
                        "mensagem": "Validação funcionando corretamente",
                        "bloqueio_check_out": "CORRETO",
                        "criacao_confirmada": "CORRETO"
                    }
                    
                except Exception as e:
                    print(f'   ❌ ERRO: Falha ao criar pagamento para status correto: {str(e)}')
                    return {
                        "sucesso": False,
                        "erro": f"Falha ao criar pagamento para status correto: {str(e)}"
                    }
            else:
                print(f'   ⚠️  ERRO INESPERADO: {e.detail}')
                return {
                    "sucesso": False,
                    "erro": f"Erro inesperado na validação: {e.detail}"
                }
                
        except Exception as e:
            print(f'   ❌ ERRO CRÍTICO: {str(e)}')
            print(f'   📋 Tipo do erro: {type(e).__name__}')
            if hasattr(e, '__cause__') and e.__cause__:
                print(f'   📋 Causa: {e.__cause__}')
            return {
                "sucesso": False,
                "erro": f"Erro crítico no teste: {str(e)}",
                "tipo": type(e).__name__
            }
    
    except Exception as e:
        print(f'\n❌ ERRO GERAL: {str(e)}')
        return {
            "sucesso": False,
            "erro": str(e)
        }

if __name__ == "__main__":
    resultado = asyncio.run(test_validacao_pagamento_api())
    print(f'\n📊 Resultado Final: {resultado}')
