"""
Script de Consolidação de Status
Corrige TODOS os status inconsistentes no banco de dados
"""
import asyncio
from prisma import Prisma

async def consolidar():
    db = Prisma()
    await db.connect()
    
    print("=" * 60)
    print("CONSOLIDAÇÃO DE STATUS - SISTEMA HOTEL")
    print("=" * 60)
    
    # 1. RESERVAS: Corrigir status obsoletos
    print("\n[1/5] Corrigindo status de RESERVAS...")
    
    # CHECKIN_LIBERADO -> CONFIRMADA
    checkin_lib = await db.reserva.find_many(where={'statusReserva': 'CHECKIN_LIBERADO'})
    for r in checkin_lib:
        await db.reserva.update(where={'id': r.id}, data={'statusReserva': 'CONFIRMADA'})
        print(f"  ✓ Reserva {r.codigoReserva}: CHECKIN_LIBERADO -> CONFIRMADA")
    
    # PAGA_APROVADA -> CONFIRMADA
    paga_aprov = await db.reserva.find_many(where={'statusReserva': 'PAGA_APROVADA'})
    for r in paga_aprov:
        await db.reserva.update(where={'id': r.id}, data={'statusReserva': 'CONFIRMADA'})
        print(f"  ✓ Reserva {r.codigoReserva}: PAGA_APROVADA -> CONFIRMADA")
    
    # PENDENTE -> PENDENTE_PAGAMENTO
    pendente = await db.reserva.find_many(where={'statusReserva': 'PENDENTE'})
    for r in pendente:
        await db.reserva.update(where={'id': r.id}, data={'statusReserva': 'PENDENTE_PAGAMENTO'})
        print(f"  ✓ Reserva {r.codigoReserva}: PENDENTE -> PENDENTE_PAGAMENTO")
    
    # HOSPEDADO -> CHECKIN_REALIZADO
    hospedado = await db.reserva.find_many(where={'statusReserva': 'HOSPEDADO'})
    for r in hospedado:
        await db.reserva.update(where={'id': r.id}, data={'statusReserva': 'CHECKIN_REALIZADO'})
        print(f"  ✓ Reserva {r.codigoReserva}: HOSPEDADO -> CHECKIN_REALIZADO")
    
    # CHECKED_OUT -> CHECKOUT_REALIZADO
    checked_out = await db.reserva.find_many(where={'statusReserva': 'CHECKED_OUT'})
    for r in checked_out:
        await db.reserva.update(where={'id': r.id}, data={'statusReserva': 'CHECKOUT_REALIZADO'})
        print(f"  ✓ Reserva {r.codigoReserva}: CHECKED_OUT -> CHECKOUT_REALIZADO")
    
    # CANCELADO -> CANCELADA
    cancelado = await db.reserva.find_many(where={'statusReserva': 'CANCELADO'})
    for r in cancelado:
        await db.reserva.update(where={'id': r.id}, data={'statusReserva': 'CANCELADA'})
        print(f"  ✓ Reserva {r.codigoReserva}: CANCELADO -> CANCELADA")
    
    total_reservas = len(checkin_lib) + len(paga_aprov) + len(pendente) + len(hospedado) + len(checked_out) + len(cancelado)
    print(f"  → Total: {total_reservas} reservas corrigidas")
    
    # 2. PAGAMENTOS: Corrigir status obsoletos
    print("\n[2/5] Corrigindo status de PAGAMENTOS...")
    
    # APROVADO -> CONFIRMADO
    aprovado = await db.pagamento.find_many(where={'statusPagamento': 'APROVADO'})
    for p in aprovado:
        await db.pagamento.update(where={'id': p.id}, data={'statusPagamento': 'CONFIRMADO'})
        print(f"  ✓ Pagamento {p.id}: APROVADO -> CONFIRMADO")
    
    # RECUSADO -> NEGADO
    recusado = await db.pagamento.find_many(where={'statusPagamento': 'RECUSADO'})
    for p in recusado:
        await db.pagamento.update(where={'id': p.id}, data={'statusPagamento': 'NEGADO'})
        print(f"  ✓ Pagamento {p.id}: RECUSADO -> NEGADO")
    
    total_pagamentos = len(aprovado) + len(recusado)
    print(f"  → Total: {total_pagamentos} pagamentos corrigidos")
    
    # 3. HOSPEDAGENS: Criar para reservas CONFIRMADA sem hospedagem
    print("\n[3/5] Criando HOSPEDAGENS faltantes...")
    
    reservas_confirmadas = await db.reserva.find_many(
        where={'statusReserva': 'CONFIRMADA'},
        include={'hospedagem': True}
    )
    
    criadas = 0
    for r in reservas_confirmadas:
        if not r.hospedagem:
            await db.hospedagem.create(
                data={
                    'reserva': {'connect': {'id': r.id}},
                    'statusHospedagem': 'NAO_INICIADA'
                }
            )
            print(f"  ✓ Criada hospedagem para reserva {r.codigoReserva}")
            criadas += 1
    
    print(f"  → Total: {criadas} hospedagens criadas")
    
    # 4. VALIDAÇÃO: Contar status atuais
    print("\n[4/5] Validando status atuais...")
    
    status_reserva = await db.reserva.group_by(
        by=['statusReserva'],
        count=True
    )
    print("  Reservas por status:")
    for s in status_reserva:
        print(f"    - {s['statusReserva']}: {s['_count']}")
    
    status_pagamento = await db.pagamento.group_by(
        by=['statusPagamento'],
        count=True
    )
    print("  Pagamentos por status:")
    for s in status_pagamento:
        print(f"    - {s['statusPagamento']}: {s['_count']}")
    
    status_hospedagem = await db.hospedagem.group_by(
        by=['statusHospedagem'],
        count=True
    )
    print("  Hospedagens por status:")
    for s in status_hospedagem:
        print(f"    - {s['statusHospedagem']}: {s['_count']}")
    
    # 5. RELATÓRIO FINAL
    print("\n[5/5] Relatório de consolidação:")
    print(f"  ✅ {total_reservas} reservas atualizadas")
    print(f"  ✅ {total_pagamentos} pagamentos atualizados")
    print(f"  ✅ {criadas} hospedagens criadas")
    print(f"\n{'=' * 60}")
    print("CONSOLIDAÇÃO CONCLUÍDA COM SUCESSO")
    print("=" * 60)
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(consolidar())
