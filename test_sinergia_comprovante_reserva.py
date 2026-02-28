#!/usr/bin/env python3
"""
TESTE COMPLETO: SINERGIA COMPROVANTES ↔ RESERVAS
Verifica se aprovação de comprovante altera status da reserva
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar backend ao path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import get_db
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.comprovante_repo import ComprovanteRepository
from app.schemas.reserva_schema import ReservaCreate
from app.schemas.pagamento_schema import PagamentoCreate
from app.schemas.comprovante_schema import ComprovanteUpload, TipoComprovante
import base64

async def testar_sinergia_comprovante_reserva():
    """Teste completo da sinergia entre comprovantes e reservas"""
    
    print("🧪 TESTE DE SINERGIA: COMPROVANTES ↔ RESERVAS")
    print("=" * 60)
    
    db = get_db()
    await db.connect()
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    try:
        # 1. Criar cliente
        print("\n👤 1. CRIANDO CLIENTE...")
        cliente_repo = ClienteRepository(db)
        cliente = await cliente_repo.create({
            "nome_completo": f"Teste Sinergia {timestamp}",
            "documento": f"1234567890{timestamp[-2:]}",
            "telefone": f"2199999999{timestamp[-4:]}",
            "email": f"teste.sinergia.{timestamp}@test.com"
        })
        print(f"   ✅ Cliente criado: ID {cliente['id']}")
        
        # 2. Verificar quartos disponíveis
        print("\n🏠 2. BUSCANDO QUARTO DISPONÍVEL...")
        quarto_repo = QuartoRepository(db)
        quartos = await quarto_repo.list_available()
        if not quartos:
            print("   ❌ Nenhum quarto disponível")
            return
        
        quarto = quartos[0]
        print(f"   ✅ Quarto encontrado: {quarto['numero']} (ID: {quarto['id']})")
        
        # 3. Criar reserva
        print("\n📋 3. CRIANDO RESERVA...")
        reserva_repo = ReservaRepository(db)
        checkin_date = datetime.now().date()
        checkout_date = checkin_date + timedelta(days=2)
        
        reserva_data = ReservaCreate(
            cliente_id=cliente['id'],
            quarto_id=quarto['id'],
            checkin_previsto=checkin_date,
            checkout_previsto=checkout_date,
            valor_diaria=100.0,
            num_diarias_previstas=2,
            valor_previsto=200.0,
            origem="BALCAO"
        )
        
        reserva = await reserva_repo.create(reserva_data.dict())
        print(f"   ✅ Reserva criada: ID {reserva['id']} | Código: {reserva['codigo_reserva']}")
        print(f"   📊 Status inicial da reserva: {reserva['status_reserva']}")
        
        # 4. Criar pagamento
        print("\n💰 4. CRIANDO PAGAMENTO...")
        pagamento_repo = PagamentoRepository(db)
        pagamento_data = PagamentoCreate(
            reserva_id=reserva['id'],
            valor=200.0,
            metodo_pagamento="DINHEIRO",
            status="PENDENTE"
        )
        
        pagamento = await pagamento_repo.create(pagamento_data.dict())
        print(f"   ✅ Pagamento criado: ID {pagamento['id']} | Status: {pagamento['status']}")
        
        # 5. Atualizar status da reserva para AGUARDANDO_COMPROVANTE
        print("\n📤 5. ATUALIZANDO RESERVA PARA AGUARDANDO_COMPROVANTE...")
        await reserva_repo.update(reserva['id'], {
            "status_reserva": "AGUARDANDO_COMPROVANTE"
        })
        
        reserva_atualizada = await reserva_repo.get_by_id(reserva['id'])
        print(f"   ✅ Status atualizado: {reserva_atualizada['status_reserva']}")
        
        # 6. Criar comprovante (usando uma imagem de teste)
        print("\n📄 6. CRIANDO COMPROVANTE...")
        comprovante_repo = ComprovanteRepository(db)
        
        # Criar uma imagem de teste simples (1x1 pixel PNG)
        imagem_teste_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        imagem_base64 = base64.b64encode(imagem_teste_png).decode()
        
        comprovante_data = ComprovanteUpload(
            pagamento_id=pagamento['id'],
            tipo_comprovante=TipoComprovante.DINHEIRO,
            arquivo_base64=imagem_base64,
            nome_arquivo="comprovante_teste.png",
            observacoes="Teste de sinergia comprovante-reserva",
            valor_confirmado=200.0
        )
        
        resultado_upload = await comprovante_repo.upload_comprovante(comprovante_data)
        print(f"   ✅ Comprovante uploaded: {resultado_upload['success']}")
        
        # 7. Verificar status após upload
        print("\n📊 7. VERIFICANDO STATUS APÓS UPLOAD...")
        pagamento_apos_upload = await pagamento_repo.get_by_id(pagamento['id'])
        reserva_apos_upload = await reserva_repo.get_by_id(reserva['id'])
        
        print(f"   💰 Status pagamento: {pagamento_apos_upload['status']}")
        print(f"   📋 Status reserva: {reserva_apos_upload['status_reserva']}")
        
        # 8. APROVAR COMPROVANTE
        print("\n✅ 8. APROVANDO COMPROVANTE...")
        from app.schemas.comprovante_schema import ValidacaoPagamento, StatusValidacao
        
        validacao_data = ValidacaoPagamento(
            pagamento_id=pagamento['id'],
            status=StatusValidacao.APROVADO,
            motivo="Teste de aprovação - sinergia",
            usuario_validador_id=1
        )
        
        resultado_aprovacao = await comprovante_repo.validar_comprovante(validacao_data)
        print(f"   ✅ Resultado aprovação: {resultado_aprovacao['success']}")
        
        # 9. VERIFICAR GATILHO - STATUS FINAL
        print("\n🎯 9. VERIFICANDO GATILHO - STATUS FINAL...")
        pagamento_final = await pagamento_repo.get_by_id(pagamento['id'])
        reserva_final = await reserva_repo.get_by_id(reserva['id'])
        
        print(f"\n📊 RESULTADOS FINAIS:")
        print(f"   💰 Pagamento: {pagamento_final['status']}")
        print(f"   📋 Reserva: {reserva_final['status_reserva']}")
        
        # 10. ANALISAR SINERGIA
        print("\n🔍 10. ANÁLISE DE SINERGIA:")
        
        # Verificar se houve mudança de status
        status_reserva_mudou = reserva_atualizada['status_reserva'] != reserva_final['status_reserva']
        status_pagamento_mudou = pagamento['status'] != pagamento_final['status']
        
        print(f"   🔄 Status reserva mudou? {'✅ SIM' if status_reserva_mudou else '❌ NÃO'}")
        print(f"   🔄 Status pagamento mudou? {'✅ SIM' if status_pagamento_mudou else '❌ NÃO'}")
        
        # Verificar semântica dos status
        semantica_correta = (
            reserva_final['status_reserva'] == "CONFIRMADA" and
            pagamento_final['status'] == "CONFIRMADO"
        )
        
        print(f"   🎯 Semântica correta (CONFIRMADA/CONFIRMADO)? {'✅ SIM' if semantica_correta else '❌ NÃO'}")
        
        # 11. CONCLUSÃO
        print("\n📋 11. CONCLUSÃO:")
        if status_reserva_mudou and status_pagamento_mudou and semantica_correta:
            print("   ✅ SINERGIA PERFEITA!")
            print("   ✅ Gatilho funcionando")
            print("   ✅ Semântica correta")
            print("   ✅ Contrato de domínio respeitado")
        else:
            print("   ❌ PROBLEMAS ENCONTRADOS:")
            if not status_reserva_mudou:
                print("      - Status da reserva NÃO mudou")
            if not status_pagamento_mudou:
                print("      - Status do pagamento NÃO mudou")
            if not semantica_correta:
                print("      - Semântica incorreta")
        
        # 12. Limpeza
        print("\n🧹 12. LIMPANDO DADOS DE TESTE...")
        try:
            # Remover na ordem correta para evitar FK constraints
            await comprovante_repo.delete_by_pagamento_id(pagamento['id'])
            await pagamento_repo.delete(pagamento['id'])
            await reserva_repo.delete(reserva['id'])
            await cliente_repo.delete(cliente['id'])
            print("   ✅ Dados limpos com sucesso")
        except Exception as e:
            print(f"   ⚠️ Erro na limpeza: {e}")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(testar_sinergia_comprovante_reserva())
