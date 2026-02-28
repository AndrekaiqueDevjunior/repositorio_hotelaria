"""
ROTA DE TESTES CIELO PRODUÇÃO
Pagamento de R$ 1,00 para validar integração
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.core.database import get_db, get_db_connected
from app.services.cielo_service import CieloAPI
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.schemas.cliente_schema import ClienteCreate
from app.schemas.reserva_schema import ReservaCreate

router = APIRouter(prefix="/cielo-test", tags=["cielo-test"])


class TestPaymentRequest(BaseModel):
    """Dados para teste de pagamento Cielo"""
    # Dados do Cliente
    nome_completo: str = "CLIENTE TESTE PRODUCAO"
    email: str = "teste@hotelreal.com.br"
    cpf: str = "12345678901"
    telefone: str = "11999999999"
    
    # Dados do Cartão
    cartao_numero: str = "4242424242424242"  # Cartão de teste
    cartao_validade: str = "12/2025"
    cartao_cvv: str = "123"
    cartao_nome: str = "CLIENTE TESTE PRODUCAO"


@router.get("/status")
async def status_cielo_producao():
    """Verificar status das credenciais Cielo em produção"""
    try:
        cielo_api = CieloAPI()
        
        return {
            "success": True,
            "mode": cielo_api.mode,
            "merchant_id": cielo_api.merchant_id[:8] + "****" if cielo_api.merchant_id else None,
            "api_url": cielo_api.base_url,
            "timeout": f"{cielo_api.timeout}s",
            "credentials_ok": bool(cielo_api.merchant_id and cielo_api.merchant_key),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/pagamento-1-real")
async def teste_pagamento_1_real(request: TestPaymentRequest):
    """
    Teste de pagamento de R$ 1,00 na Cielo Produção
    Cria reserva teste + pagamento real
    """
    # Inicializar APIs e repositórios
    db = await get_db_connected()
    if not db.is_connected():
        await db.connect()
    cielo_api = CieloAPI()
    pagamento_repo = PagamentoRepository(db)
    reserva_repo = ReservaRepository(db)
    cliente_repo = ClienteRepository(db)
    
    try:
        # 1. Criar ou obter cliente de teste
        clientes_existentes = await cliente_repo.list_all(search=request.email)
        cliente_teste = None
        if clientes_existentes["clientes"]:
            cliente_teste = clientes_existentes["clientes"][0]
            
            # Limpar reservas pendentes existentes para este cliente
            reservas_pendentes = await db.reserva.find_many(
                where={
                    "clienteId": cliente_teste["id"],  # Usar clienteId em vez de cliente_id
                    "statusReserva": {  # Usar statusReserva em vez de status_reserva
                        "in": ["PENDENTE", "CONFIRMADA"]
                    }
                }
            )
            
            # Cancelar reservas pendentes
            for reserva in reservas_pendentes:
                await db.reserva.update(
                    where={"id": reserva.id},
                    data={"statusReserva": "CANCELADA"}  # Usar statusReserva em vez de status_reserva
                )
        
        # Criar novo cliente se não existir
        if not cliente_teste:
            cliente_create = ClienteCreate(
                nome_completo=request.nome_completo,
                documento=request.cpf,
                email=request.email,
                telefone=request.telefone
            )
            cliente_teste = await cliente_repo.create(cliente_create)
        
        # 2. Criar reserva teste
        codigo_reserva = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        # Usar o quarto REAL 501 que está disponível
        dados_reserva = ReservaCreate(
            cliente_id=cliente_teste["id"],
            quarto_numero="501",  # Usando o quarto REAL existente
            tipo_suite="REAL",
            checkin_previsto=datetime.now(),
            checkout_previsto=datetime.now(),
            valor_diaria=1.00,
            num_diarias=1,
        )

        reserva_teste = await reserva_repo.create(dados_reserva)
        
        # 3. Criar pagamento de R$ 1,00
        idempotency_key = f"test-{reserva_teste['id']}-{uuid.uuid4().hex[:8]}"
        
        dados_pagamento = {
            "reserva_id": reserva_teste["id"],
            "valor": 1.00,
            "metodo": "credit_card",
            "parcelas": 1,
            "cartao_numero": request.cartao_numero,
            "cartao_validade": request.cartao_validade,
            "cartao_cvv": request.cartao_cvv,
            "cartao_nome": request.cartao_nome
        }
        
        # 4. Processar pagamento na Cielo
        print(f"[CIELO TEST] Iniciando pagamento de R$ 1,00...")
        print(f"[CIELO TEST] Reserva: {codigo_reserva}")
        print(f"[CIELO TEST] Cliente: {cliente_teste.get('nome_completo', cliente_teste.get('nomeCompleto', 'Cliente sem nome'))}")
        print(f"[CIELO TEST] Ambiente: {cielo_api.mode}")
        
        try:
            # Chamar a API da Cielo
            resultado_cielo = await cielo_api.criar_pagamento_cartao(
                valor=1.00,
                cartao_numero=request.cartao_numero,
                cartao_validade=request.cartao_validade,
                cartao_cvv=request.cartao_cvv,
                cartao_nome=request.cartao_nome,
                parcelas=1
            )
            
            # Verificar se o pagamento foi bem-sucedido
            if not resultado_cielo.get('success', True):
                # Se success for False, tratar como erro
                error_msg = resultado_cielo.get('error', 'Erro desconhecido na Cielo')
                print(f"[CIELO TEST] Erro na API Cielo: {error_msg}")
                await db.disconnect()
                return {
                    "success": False,
                    "error": f"Erro na API Cielo: {error_msg}",
                    "cielo_response": resultado_cielo,
                    "test_data": {
                        "reserva_codigo": codigo_reserva,
                        "valor_teste": "R$ 1,00",
                        "ambiente": cielo_api.mode,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
            # Verificar se o pagamento foi bem-sucedido
            if resultado_cielo.get('status') in ['AUTHORIZED', 'CAPTURED']:
                # Pagamento aprovado
                print(f"[CIELO TEST] Pagamento aprovado: {resultado_cielo}")
                
                # Salvar pagamento no banco com dados Cielo
                pagamento_criado = await pagamento_repo.create(
                    pagamento=dados_pagamento,
                    idempotency_key=idempotency_key
                )
                
                # Atualizar com dados da Cielo
                await pagamento_repo.update_status(
                    pagamento_id=pagamento_criado["id"],
                    status="APROVADO",
                    cielo_payment_id=resultado_cielo.get('payment_id'),
                    url_pagamento=resultado_cielo.get('url')
                )
                
                # Confirmar reserva automaticamente
                await reserva_repo.update_status(reserva_teste["id"], "CONFIRMADA")
                
                await db.disconnect()
                
                # Retorno sucesso
                return {
                    "success": True,
                    "message": "✅ Pagamento de R$ 1,00 aprovado com sucesso!",
                    "test_data": {
                        "reserva_codigo": codigo_reserva,
                        "reserva_id": reserva_teste["id"],
                        "cliente_id": cliente_teste["id"],
                        "pagamento_id": pagamento_criado["id"],
                        "valor_teste": "R$ 1,00",
                        "ambiente": cielo_api.mode,
                        "timestamp": datetime.now().isoformat()
                    },
                    "cielo_response": {
                        "payment_id": resultado_cielo.get('payment_id'),
                        "status": resultado_cielo.get('status'),
                        "authorization_code": resultado_cielo.get('authorization_code'),
                        "return_code": resultado_cielo.get('return_code'),
                        "return_message": resultado_cielo.get('return_message')
                    }
                }
            else:
                # Pagamento falhou na Cielo
                error_msg = resultado_cielo.get('return_message', resultado_cielo.get('error', 'Erro desconhecido na Cielo'))
                print(f"[CIELO TEST] Falha no pagamento: {error_msg}")
                
                # Se houver uma reserva, cancelá-la
                if reserva_teste and 'id' in reserva_teste:
                    try:
                        await reserva_repo.update_status(reserva_teste["id"], "CANCELADA")
                    except Exception as e:
                        print(f"[CIELO TEST] Erro ao cancelar reserva: {str(e)}")
                
                await db.disconnect()
                return {
                    "success": False,
                    "error": f"Pagamento recusado pela Cielo: {error_msg}",
                    "cielo_response": resultado_cielo,
                    "test_data": {
                        "reserva_codigo": codigo_reserva,
                        "valor_teste": "R$ 1,00",
                        "ambiente": cielo_api.mode,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            print(f"[CIELO TEST] Erro ao processar pagamento: {str(e)}")
            await db.disconnect()
            return {
                "success": False,
                "error": f"Erro ao processar pagamento: {str(e)}",
                "test_data": {
                    "reserva_codigo": codigo_reserva,
                    "valor_teste": "R$ 1,00",
                    "ambiente": cielo_api.mode,
                    "timestamp": datetime.now().isoformat()
                },
                "debug_info": {
                    "merchant_id_configured": bool(cielo_api.merchant_id),
                    "api_url": cielo_api.base_url,
                    "mode": cielo_api.mode
                }
            }
        
        # 5. Salvar pagamento no banco com dados Cielo
        pagamento_criado = await pagamento_repo.create(
            pagamento=dados_pagamento,
            idempotency_key=idempotency_key
        )
        
        # 6. Atualizar com dados da Cielo
        await pagamento_repo.update_status(
            pagamento_id=pagamento_criado["id"],
            status="APROVADO",
            cielo_payment_id=resultado_cielo["data"].get("PaymentId"),
            url_pagamento=resultado_cielo["data"].get("Url")
        )
        
        # 7. Confirmar reserva automaticamente
        await reserva_repo.update_status(reserva_teste["id"], "CONFIRMADA")
        
        await db.disconnect()
        
        # Retorno sucesso
        return {
            "success": True,
            "message": "✅ Pagamento de R$ 1,00 aprovado com sucesso!",
            "test_data": {
                "reserva_codigo": codigo_reserva,
                "reserva_id": reserva_teste["id"],
                "cliente_id": cliente_teste["id"],
                "pagamento_id": pagamento_criado["id"],
                "valor_teste": "R$ 1,00",
                "ambiente": cielo_api.mode,
                "timestamp": datetime.now().isoformat()
            },
            "cielo_response": {
                "payment_id": resultado_cielo["data"].get("PaymentId"),
                "status": resultado_cielo["data"].get("Status"),
                "authorization_code": resultado_cielo["data"].get("AuthorizationCode"),
                "return_code": resultado_cielo["data"].get("ReturnCode"),
                "return_message": resultado_cielo["data"].get("ReturnMessage")
            },
            "next_steps": [
                "1. Verifique o pagamento no dashboard Cielo",
                "2. Confirme se o valor de R$ 1,00 foi debitado",
                "3. Teste o estorno se necessário",
                "4. Valide se a reserva foi confirmada"
            ]
        }
        
    except Exception as e:
        # Erro no processamento
        try:
            await db.disconnect()
        except:
            pass
            
        return {
            "success": False,
            "error": f"Erro no teste: {str(e)}",
            "test_data": {
                "valor_teste": "R$ 1,00",
                "ambiente": "production",
                "timestamp": datetime.now().isoformat()
            },
            "debug_info": {
                "merchant_id_configured": bool(cielo_api.merchant_id),
                "api_url": cielo_api.base_url,
                "mode": cielo_api.mode
            }
        }


@router.post("/estorno-teste")
async def teste_estorno_1_real(payment_id: str):
    """
    Teste de estorno do pagamento de R$ 1,00
    """
    try:
        db = get_db()
        await db.connect()
        
        cielo_api = CieloAPI()
        pagamento_repo = PagamentoRepository(db)
        
        # Buscar pagamento pelo ID da Cielo
        pagamento = await pagamento_repo.get_by_payment_id(payment_id)
        if not pagamento:
            await db.disconnect()
            raise HTTPException(status_code=404, detail="Pagamento não encontrado")
        
        # Processar estorno na Cielo
        resultado_estorno = await cielo_api.estornar_pagamento_cartao(
            payment_id=payment_id,
            valor=1.00,
            motivo="Teste de estorno R$ 1,00"
        )
        
        if resultado_estorno.get("success"):
            # Atualizar status no banco
            await pagamento_repo.update_status(
                pagamento_id=pagamento["id"],
                status="ESTORNADO"
            )
            
            await db.disconnect()
            
            return {
                "success": True,
                "message": "✅ Estorno de R$ 1,00 processado com sucesso!",
                "estorno_data": {
                    "payment_id": payment_id,
                    "valor": "R$ 1,00",
                    "motivo": "Teste de estorno",
                    "timestamp": datetime.now().isoformat()
                },
                "cielo_response": resultado_estorno
            }
        else:
            await db.disconnect()
            return {
                "success": False,
                "error": "Estorno falhou",
                "cielo_response": resultado_estorno
            }
            
    except Exception as e:
        try:
            await db.disconnect()
        except:
            pass
        return {
            "success": False,
            "error": f"Erro no estorno: {str(e)}"
        }


@router.get("/limpar-testes")
async def limpar_dados_teste():
    """
    Limpar todos os dados de teste (reservas, pagamentos, cliente teste)
    """
    try:
        db = get_db()
        await db.connect()
        
        # Buscar e deletar dados de teste
        cliente_teste = await db.cliente.find_first(
            where={"email": "teste@hotelreal.com.br"},
            include={
                "reservas": True,
                "pagamentos": True
            }
        )
        
        if cliente_teste:
            # Deletar pagamentos teste
            for pagamento in cliente_teste.pagamentos or []:
                await db.pagamento.delete(where={"id": pagamento.id})
            
            # Deletar reservas teste
            for reserva in cliente_teste.reservas or []:
                await db.reserva.delete(where={"id": reserva.id})
            
            # Deletar cliente teste
            await db.cliente.delete(where={"id": cliente_teste.id})
            
            await db.disconnect()
            
            return {
                "success": True,
                "message": "✅ Dados de teste limpos com sucesso!",
                "removed_data": {
                    "cliente": getattr(cliente_teste, 'nome_completo', getattr(cliente_teste, 'nomeCompleto', 'Cliente sem nome')),
                    "reservas_removidas": len(getattr(cliente_teste, 'reservas', []) or []),
                    "pagamentos_removidos": len(getattr(cliente_teste, 'pagamentos', []) or [])
                }
            }
        else:
            await db.disconnect()
            return {
                "success": True,
                "message": "Nenhum dado de teste encontrado para limpar"
            }
            
    except Exception as e:
        try:
            await db.disconnect()
        except:
            pass
        return {
            "success": False,
            "error": f"Erro ao limpar dados: {str(e)}"
        }
