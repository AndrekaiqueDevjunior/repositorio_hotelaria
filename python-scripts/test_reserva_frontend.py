import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import json

# Adiciona o diretório backend ao path para importar os modelos
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Dados de teste
BASE_URL = "http://localhost:8000/api/v1"

# Dados do cliente de teste (deve existir no banco de dados)
CLIENTE_TESTE = {
    "id": 1,  # Substitua pelo ID de um cliente existente
    "nome": "Cliente Teste",
    "email": "cliente@teste.com"
}

# Tipos de suítes disponíveis
TIPOS_SUITE = [
    "LUXO", "LUXO 2º", "LUXO 3º", "LUXO 4º EC", 
    "DUPLA", "MASTER", "REAL", "STANDARD", "SUITE"
]

# Dados do cartão de teste (sandbox Cielo)
CARTAO_TESTE = {
    "numero": "4532117080573700",  # Cartão de teste Cielo Sandbox
    "validade": "12/2025",
    "cvv": "123",
    "nome": "CLIENTE TESTE"
}

async def get_quartos_disponiveis():
    """Busca quartos disponíveis para reserva"""
    url = f"{BASE_URL}/quartos/disponiveis"
    
    # Parâmetros de exemplo (ajuste conforme necessário)
    params = {
        "checkin": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "checkout": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "tipo_suite": random.choice(TIPOS_SUITE)  # Escolhe um tipo de suíte aleatório
    }
    
    print(f"\n🔍 Buscando quartos disponíveis...")
    print(f"📅 Período: {params['checkin']} até {params['checkout']}")
    print(f"🏨 Tipo de suíte: {params['tipo_suite']}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ {len(data.get('data', []))} quartos disponíveis encontrados")
                    return data.get('data', [])
                else:
                    error = await response.text()
                    print(f"❌ Erro ao buscar quartos: {error}")
                    return []
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
        return []

async def criar_reserva():
    """Cria uma nova reserva"""
    # 1. Buscar quartos disponíveis
    quartos = await get_quartos_disponiveis()
    
    if not quartos:
        print("❌ Nenhum quarto disponível para os critérios informados")
        return
    
    # Seleciona o primeiro quarto disponível
    quarto = quartos[0]
    print(f"\n🎯 Selecionando quarto: {quarto.get('numero')} - {quarto.get('tipo_suite')}")
    
    # 2. Dados da reserva
    checkin = datetime.now() + timedelta(days=1)
    checkout = checkin + timedelta(days=2)  # 2 noites
    
    reserva_data = {
        "cliente_id": CLIENTE_TESTE["id"],
        "quarto_id": quarto["id"],
        "quarto_numero": quarto["numero"],
        "tipo_suite": quarto["tipo_suite"],
        "checkin_previsto": checkin.isoformat(),
        "checkout_previsto": checkout.isoformat(),
        "valor_diaria": quarto["valor_diaria"],
        "num_diarias": 2,
        "adultos": 2,
        "criancas": 0,
        "observacoes": "Reserva de teste automático"
    }
    
    print("\n📝 Criando reserva...")
    print(json.dumps(reserva_data, indent=2, default=str))
    
    try:
        async with aiohttp.ClientSession() as session:
            # 3. Criar reserva
            url = f"{BASE_URL}/reservas"
            async with session.post(url, json=reserva_data) as response:
                if response.status == 201:
                    reserva = await response.json()
                    print(f"\n✅ Reserva criada com sucesso!")
                    print(f"📌 Código: {reserva.get('codigo_reserva')}")
                    print(f"🏨 Quarto: {reserva.get('quarto_numero')}")
                    print(f"📅 Período: {reserva.get('checkin_previsto')} a {reserva.get('checkout_previsto')}")
                    print(f"💰 Valor total: R$ {reserva.get('valor_total', 0):.2f}")
                    
                    # 4. Processar pagamento
                    await processar_pagamento(reserva["id"], reserva_data["valor_diaria"] * 2)  # 2 noites
                    
                    return reserva
                else:
                    error = await response.text()
                    print(f"❌ Erro ao criar reserva: {error}")
                    return None
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
        return None

async def processar_pagamento(reserva_id: int, valor: float):
    """Processa o pagamento da reserva"""
    print(f"\n💳 Processando pagamento para reserva {reserva_id}...")
    
    pagamento_data = {
        "reserva_id": reserva_id,
        "valor": valor,
        "metodo": "credit_card",
        "cartao_numero": CARTAO_TESTE["numero"],
        "cartao_validade": CARTAO_TESTE["validade"],
        "cartao_cvv": CARTAO_TESTE["cvv"],
        "cartao_nome": CARTAO_TESTE["nome"],
        "parcelas": 1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BASE_URL}/pagamentos"
            async with session.post(url, json=pagamento_data) as response:
                if response.status == 201:
                    pagamento = await response.json()
                    print(f"\n✅ Pagamento processado com sucesso!")
                    print(f"🔢 ID do pagamento: {pagamento.get('id')}")
                    print(f"📊 Status: {pagamento.get('status')}")
                    print(f"💳 Bandeira: {pagamento.get('cartao_bandeira', 'N/A')}")
                    print(f"🔍 Código de autorização: {pagamento.get('authorization_code', 'N/A')}")
                    
                    # Verificar status da reserva após o pagamento
                    await verificar_reserva(reserva_id)
                    
                    return pagamento
                else:
                    error = await response.text()
                    print(f"❌ Erro ao processar pagamento: {error}")
                    return None
    except Exception as e:
        print(f"❌ Erro na requisição de pagamento: {str(e)}")
        return None

async def verificar_reserva(reserva_id: int):
    """Verifica o status de uma reserva"""
    print(f"\n🔍 Verificando status da reserva {reserva_id}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BASE_URL}/reservas/{reserva_id}"
            async with session.get(url) as response:
                if response.status == 200:
                    reserva = await response.json()
                    print(f"\n📋 Status da reserva {reserva_id}:")
                    print(f"📌 Código: {reserva.get('codigo_reserva')}")
                    print(f"🏨 Quarto: {reserva.get('quarto_numero')}")
                    print(f"📅 Check-in: {reserva.get('checkin_previsto')}")
                    print(f"📅 Check-out: {reserva.get('checkout_previsto')}")
                    print(f"📊 Status: {reserva.get('status')}")
                    print(f"💰 Valor total: R$ {reserva.get('valor_total', 0):.2f}")
                    
                    # Verificar se há pagamentos associados
                    if reserva.get('pagamentos'):
                        print("\n💳 Pagamentos:")
                        for p in reserva['pagamentos']:
                            print(f"  - ID: {p.get('id')} | Status: {p.get('status')} | Valor: R$ {p.get('valor', 0):.2f}")
                    
                    return reserva
                else:
                    error = await response.text()
                    print(f"❌ Erro ao verificar reserva: {error}")
                    return None
    except Exception as e:
        print(f"❌ Erro ao verificar reserva: {str(e)}")
        return None

async def main():
    print("""
    🏨 SIMULADOR DE RESERVA - HOTEL CABO FRIO
    =======================================
    Este script simula o fluxo de criação de uma reserva
    através de requisições HTTP para a API do backend.
    """)
    
    # 1. Criar reserva
    reserva = await criar_reserva()
    
    if reserva:
        print("\n✅ Fluxo de reserva concluído com sucesso!")
    else:
        print("\n❌ Ocorreu um erro durante o fluxo de reserva.")

if __name__ == "__main__":
    asyncio.run(main())
