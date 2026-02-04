#!/usr/bin/env python3
"""
Script para testar criação de reserva do zero e identificar gaps de status
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o backend ao path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import get_db
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.schemas.reserva_schema import ReservaCreate
from app.utils.datetime_utils import now_utc

async def test_fluxo_completo():
    """Testar fluxo completo de criação de reserva"""
    print("🔍 INICIANDO TESTE DE FLUXO COMPLETO DE RESERVA")
    print("=" * 60)
    
    db = next(get_db())
    cliente_repo = ClienteRepository(db)
    quarto_repo = QuartoRepository(db)
    reserva_repo = ReservaRepository(db)
    
    # 1. Verificar clientes existentes
    print("\n📋 1. VERIFICANDO CLIENTES")
    clientes = await db.cliente.find_many()
    print(f"   Clientes encontrados: {len(clientes)}")
    
    if not clientes:
        print("   ❌ Nenhum cliente encontrado. Criando cliente de teste...")
        # Criar cliente de teste
        cliente_teste = await db.cliente.create({
            "nomeCompleto": "CLIENTE TESTE FLUXO",
            "email": "teste@fluxo.com",
            "telefone": "21999999999",
            "documento": "12345678901",
            "dataNascimento": datetime(1990, 1, 1),
            "nacionalidade": "Brasil"
        })
        print(f"   ✅ Cliente criado: ID {cliente_teste.id} - {cliente_teste.nomeCompleto}")
        cliente_id = cliente_teste.id
    else:
        cliente = clientes[0]
        print(f"   ✅ Usando cliente: ID {cliente.id} - {cliente.nomeCompleto}")
        cliente_id = cliente.id
    
    # 2. Verificar quartos disponíveis
    print("\n🏨 2. VERIFICANDO QUARTOS")
    quartos = await db.quarto.find_many()
    print(f"   Quartos encontrados: {len(quartos)}")
    
    quarto_disponivel = None
    for q in quartos:
        print(f"   - Quarto {q.numero}: {q.tipoSuite} - Status: {q.status}")
        if q.status == "LIVRE" and not quarto_disponivel:
            quarto_disponivel = q
    
    if not quarto_disponivel:
        print("   ❌ Nenhum quarto disponível encontrado")
        return
    
    print(f"   ✅ Usando quarto: {quarto_disponivel.numero} - {quarto_disponivel.tipoSuite}")
    
    # 3. Criar reserva
    print("\n📅 3. CRIANDO RESERVA")
    
    # Datas para amanhã e depois de amanhã
    amanha = now_utc() + timedelta(days=1)
    depois_de_amanha = now_utc() + timedelta(days=3)
    
    dados_reserva = ReservaCreate(
        cliente_id=cliente_id,
        quarto_numero=quarto_disponivel.numero,
        tipo_suite=quarto_disponivel.tipoSuite,
        checkin_previsto=amanha,
        checkout_previsto=depois_de_amanha,
        num_diarias=2
    )
    
    print(f"   Dados da reserva:")
    print(f"   - Cliente ID: {dados_reserva.cliente_id}")
    print(f"   - Quarto: {dados_reserva.quarto_numero}")
    print(f"   - Check-in: {dados_reserva.checkin_previsto.strftime('%d/%m/%Y')}")
    print(f"   - Check-out: {dados_reserva.checkout_previsto.strftime('%d/%m/%Y')}")
    print(f"   - Diárias: {dados_reserva.num_diarias}")
    
    try:
        # Obter quarto para pegar o ID
        quarto_obj = await db.quarto.find_unique(where={"numero": dados_reserva.quarto_numero})
        if not quarto_obj:
            print(f"   ❌ Quarto {dados_reserva.quarto_numero} não encontrado")
            return
        
        # Obter cliente para pegar o nome
        cliente_obj = await db.cliente.find_unique(where={"id": dados_reserva.cliente_id})
        if not cliente_obj:
            print(f"   ❌ Cliente {dados_reserva.cliente_id} não encontrado")
            return
        
        # Criar reserva diretamente com Prisma para teste
        from app.utils.datetime_utils import now_utc
        import secrets
        
        tentativa = 0
        nova_reserva = None
        while tentativa < 5:
            tentativa += 1
            codigo_reserva = f"RCF-{now_utc().strftime('%Y%m')}-{secrets.token_hex(3).upper()}"
            
            try:
                nova_reserva = await db.reserva.create(
                    data={
                        "codigoReserva": codigo_reserva,
                        "clienteId": dados_reserva.cliente_id,
                        "quartoId": quarto_obj.id,
                        "quartoNumero": dados_reserva.quarto_numero,
                        "tipoSuite": dados_reserva.tipo_suite,
                        "clienteNome": cliente_obj.nomeCompleto,
                        "checkinPrevisto": dados_reserva.checkin_previsto,
                        "checkoutPrevisto": dados_reserva.checkout_previsto,
                        "valorDiaria": 100.0,  # Valor fixo para teste
                        "numDiarias": dados_reserva.num_diarias,
                        "statusReserva": "PENDENTE"
                    }
                )
                break
            except Exception as e:
                print(f"   Tentativa {tentativa} falhou: {e}")
                nova_reserva = None
        
        if not nova_reserva:
            print("   ❌ Não foi possível gerar um código de reserva único")
            return
        
        reserva_criada = reserva_repo._serialize_reserva(nova_reserva)
        print(f"   ✅ Reserva criada com sucesso!")
        print(f"   - ID: {reserva_criada['id']}")
        print(f"   - Código: {reserva_criada['codigo_reserva']}")
        print(f"   - Status: {reserva_criada['status']}")
        
        # 4. Verificar se hospedagem foi criada
        print("\n🛏️ 4. VERIFICANDO HOSPEDAGEM")
        hospedagem = await db.hospedagem.find_unique(where={"reservaId": reserva_criada['id']})
        
        if hospedagem:
            print(f"   ✅ Hospedagem encontrada:")
            print(f"   - ID: {hospedagem.id}")
            print(f"   - Status: {hospedagem.statusHospedagem}")
            print(f"   - Criada em: {hospedagem.createdAt}")
        else:
            print(f"   ❌ Hospedagem NÃO encontrada (GAP IDENTIFICADO!)")
        
        # 5. Verificar pagamentos
        print("\n💳 5. VERIFICANDO PAGAMENTOS")
        pagamentos = await db.pagamento.find_many(where={"reservaId": reserva_criada['id']})
        print(f"   Pagamentos encontrados: {len(pagamentos)}")
        
        if pagamentos:
            for p in pagamentos:
                print(f"   - Pagamento {p.id}: R$ {p.valor} - Status: {p.statusPagamento}")
        else:
            print(f"   ❌ Nenhum pagamento encontrado (esperado para nova reserva)")
        
        # 6. Resumo dos status atuais
        print("\n📊 6. RESUMO DOS STATUS ATUAIS")
        print(f"   Reserva: {reserva_criada['status']}")
        if hospedagem:
            print(f"   Hospedagem: {hospedagem.statusHospedagem}")
        else:
            print(f"   Hospedagem: NÃO CRIADA")
        print(f"   Pagamentos: {len(pagamentos)}")
        
        # 7. Análise de gaps
        print("\n🔍 7. ANÁLISE DE GAPS IDENTIFICADOS")
        gaps = []
        
        # Gap 1: Hospedagem não criada automaticamente
        if not hospedagem:
            gaps.append("❌ Gap #1: Hospedagem não é criada automaticamente na criação da reserva")
        
        # Gap 2: Status inicial inconsistente
        if reserva_criada['status'] not in ['PENDENTE', 'PENDENTE_PAGAMENTO']:
            gaps.append(f"❌ Gap #2: Status inicial inesperado: {reserva_criada['status']}")
        
        # Gap 3: Verificar compatibilidade de enums
        from app.schemas.status_enums import StatusReserva
        try:
            status_enum = StatusReserva(reserva_criada['status'])
            print(f"   ✅ Status '{reserva_criada['status']}' é válido no enum StatusReserva")
        except ValueError:
            gaps.append(f"❌ Gap #3: Status '{reserva_criada['status']}' NÃO é válido no enum StatusReserva")
        
        if gaps:
            print("\n   GAPS ENCONTRADOS:")
            for gap in gaps:
                print(f"   {gap}")
        else:
            print("\n   ✅ Nenhum gap encontrado na criação da reserva")
        
        # 8. Próximos passos do fluxo
        print("\n🔄 8. PRÓXIMOS PASSOS DO FLUXO")
        print("   Para continuar o teste:")
        print(f"   1. Criar pagamento para reserva {reserva_criada['codigo_reserva']}")
        print("   2. Fazer upload de comprovante (se pagamento balcão)")
        print("   3. Validar comprovante")
        print("   4. Verificar transição para status CONFIRMADA")
        print("   5. Criar hospedagem (se não existir)")
        print("   6. Fazer check-in")
        print("   7. Verificar transição para HOSPEDADO")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar reserva: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fluxo_completo())
