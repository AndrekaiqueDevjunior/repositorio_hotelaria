#!/usr/bin/env python3
"""
Teste simplificado da validação de resgate com histórico
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o backend ao path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import get_db_connected

async def test_validacao_simplificada():
    """Testar validação de resgate com dados básicos"""
    print("🔍 TESTE DE VALIDAÇÃO COM HISTÓRICO")
    print("=" * 50)
    
    db = await get_db_connected()
    
    try:
        # 1. Buscar resgates existentes
        print("\n📋 1. BUSCANDO RESGATES")
        
        resgates = await db.resgatepremio.find_many(
            take=5,
            order={"id": "desc"},
            include={
                "cliente": True,
                "premio": True,
                "funcionario": True
            }
        )
        
        print(f"   Encontrados: {len(resgates)} resgates")
        
        if not resgates:
            print("   ❌ Nenhum resgate encontrado")
            return
        
        # 2. Analisar o primeiro resgate
        resgate = resgates[0]
        codigo_resgate = f"RES-{str(resgate.id).zfill(6)}"
        
        print(f"\n🎯 2. RESGATE SELECIONADO: {codigo_resgate}")
        print(f"   Cliente: {resgate.cliente.nomeCompleto}")
        print(f"   Documento: {resgate.cliente.documento}")
        print(f"   Prêmio: {resgate.premio.nome}")
        print(f"   Pontos usados: {resgate.pontosUsados}")
        print(f"   Status: {resgate.status}")
        
        # 3. Buscar dados de pontos do cliente separadamente
        print(f"\n💰 3. DADOS DE PONTOS DO CLIENTE")
        
        usuario_pontos = await db.usuariopontos.find_unique(
            where={"clienteId": resgate.cliente.id}
        )
        
        if usuario_pontos:
            print(f"   Saldo atual: {usuario_pontos.saldo}")
        else:
            print(f"   ❌ Cliente não tem registro de pontos")
        
        # 4. Buscar histórico de transações
        print(f"\n📜 4. HISTÓRICO DE TRANSAÇÕES")
        
        transacoes = await db.transacaopontos.find_many(
            where={"clienteId": resgate.cliente.id},
            take=10,
            order={"createdAt": "desc"}
        )
        
        print(f"   Transações encontradas: {len(transacoes)}")
        
        if transacoes:
            print(f"\n   Últimas transações:")
            for i, transacao in enumerate(transacoes[:5], 1):
                print(f"   {i}. {transacao.createdAt.strftime('%d/%m/%Y %H:%M')} - {transacao.tipo}")
                print(f"      Pontos: {transacao.pontos:+d}")
                print(f"      Origem: {transacao.origem}")
                if transacao.motivo:
                    print(f"      Motivo: {transacao.motivo}")
                print()
        else:
            print("   ❌ Nenhuma transação encontrada")
        
        # 5. Buscar resgates anteriores
        print(f"🎁 5. RESGATES ANTERIORES")
        
        outros_resgates = await db.resgatepremio.find_many(
            where={
                "clienteId": resgate.cliente.id,
                "id": {"not": resgate.id}
            },
            take=5,
            order={"createdAt": "desc"},
            include={"premio": True}
        )
        
        print(f"   Outros resgates: {len(outros_resgates)}")
        
        if outros_resgates:
            print(f"\n   Resgates anteriores:")
            for i, outro in enumerate(outros_resgates, 1):
                codigo_outro = f"RES-{str(outro.id).zfill(6)}"
                print(f"   {i}. {codigo_outro} - {outro.premio.nome}")
                print(f"      Pontos: {outro.pontosUsados}")
                print(f"      Status: {outro.status}")
                print(f"      Data: {outro.createdAt.strftime('%d/%m/%Y')}")
                print()
        else:
            print("   ❌ Nenhum outro resgate encontrado")
        
        # 6. Calcular estatísticas
        print(f"📊 6. ESTATÍSTICAS DO CLIENTE")
        
        if transacoes:
            pontos_ganhos = sum(t.pontos for t in transacoes if t.pontos > 0)
            pontos_perdidos = sum(t.pontos for t in transacoes if t.pontos < 0)
            pontos_totais = sum(t.pontos for t in transacoes)
            
            print(f"   💰 Pontos ganhos: {pontos_ganhos}")
            print(f"   💸 Pontos perdidos: {pontos_perdidos}")
            print(f"   📊 Total transacionado: {pontos_totais}")
            print(f"   💰 Saldo atual: {usuario_pontos.saldo if usuario_pontos else 0}")
            
            # Principais origens
            origens = {}
            for t in transacoes:
                origem = t.origem
                if origem not in origens:
                    origens[origem] = {'count': 0, 'pontos': 0}
                origens[origem]['count'] += 1
                origens[origem]['pontos'] += t.pontos
            
            print(f"\n   📋 Principais origens:")
            for origem, dados in sorted(origens.items(), key=lambda x: x[1]['pontos'], reverse=True)[:3]:
                print(f"      - {origem}: {dados['count']}x, {dados['pontos']} pontos")
        
        # 7. Simular resposta da API
        print(f"\n🔐 7. RESPOSTA DA API COM HISTÓRICO")
        
        resposta = {
            "valido": True,
            "resgate_id": resgate.id,
            "cliente_nome": resgate.cliente.nomeCompleto,
            "cliente_documento": resgate.cliente.documento,
            "premio_nome": resgate.premio.nome,
            "pontos_usados": resgate.pontosUsados,
            "status": resgate.status,
            "data_resgate": resgate.createdAt.isoformat(),
            "ja_entregue": resgate.status == "ENTREGUE",
            "funcionario_resgate": resgate.funcionario.nome if resgate.funcionario else "Sistema",
            "mensagem": "✅ Código válido!" if resgate.status != "ENTREGUE" else "⚠️ Este prêmio já foi entregue!",
            # 🆕 Dados da trajetória
            "pontos_atuais": usuario_pontos.saldo if usuario_pontos else 0,
            "total_gasto": resgate.cliente.totalGasto,
            "total_reservas": resgate.cliente.totalReservas,
            "nivel_fidelidade": resgate.cliente.nivelFidelidade,
            "historico_pontos": [
                {
                    "data": t.createdAt.isoformat(),
                    "tipo": t.tipo,
                    "pontos": t.pontos,
                    "origem": t.origem,
                    "motivo": t.motivo,
                    "reserva_id": t.reservaId
                } for t in transacoes[:5]
            ],
            "resgates_anteriores": [
                {
                    "id": r.id,
                    "codigo": f"RES-{str(r.id).zfill(6)}",
                    "premio": r.premio.nome,
                    "pontos_usados": r.pontosUsados,
                    "status": r.status,
                    "data": r.createdAt.isoformat()
                } for r in outros_resgates
            ]
        }
        
        print(f"   ✅ Dados incluídos na resposta:")
        print(f"      - Pontos atuais: {resposta['pontos_atuais']}")
        print(f"      - Total gasto: R$ {resposta['total_gasto'] or 0:.2f}")
        print(f"      - Total reservas: {resposta['total_reservas'] or 0}")
        print(f"      - Nível fidelidade: {resposta['nivel_fidelidade'] or 'N/A'}")
        print(f"      - Histórico: {len(resposta['historico_pontos'])} transações")
        print(f"      - Resgates anteriores: {len(resposta['resgates_anteriores'])}")
        
        # 8. Benefícios para o funcionário
        print(f"\n👨‍💼 8. BENEFÍCIOS PARA O FUNCIONÁRIO")
        print(f"   ✅ Verifica se cliente tem pontos suficientes")
        print(f"   ✅ Entende de onde vieram os pontos")
        print(f"   ✅ Identifica clientes fiéis vs novos")
        print(f"   ✅ Previne fraudes (histórico consistente)")
        print(f"   ✅ Contexto completo para decisão")
        
        # 9. Exemplo de análise
        print(f"\n🔍 9. ANÁLISE DE EXEMPLO")
        
        if resposta['total_reservas'] and resposta['total_reservas'] > 5:
            print(f"   🏆 Cliente fiel: {resposta['total_reservas']} reservas")
        
        if resposta['total_gasto'] and resposta['total_gasto'] > 1000:
            print(f"   💰 Cliente valioso: R$ {resposta['total_gasto']:.2f} em gastos")
        
        if len(resposta['resgates_anteriores']) > 2:
            print(f"   🎁 Cliente frequente: {len(resposta['resgates_anteriores'])} resgates anteriores")
        
        if resposta['pontos_atuais'] > resposta['pontos_usados'] * 2:
            print(f"   ✅ Pontos suficientes: {resposta['pontos_atuais']} disponíveis")
        else:
            print(f"   ⚠️ Pontos baixos: {resposta['pontos_atuais']} disponíveis")
        
        print(f"\n🎉 TESTE CONCLUÍDO!")
        print(f"   O sistema agora fornece contexto completo sobre os pontos do cliente")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_validacao_simplificada())
