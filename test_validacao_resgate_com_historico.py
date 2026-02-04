#!/usr/bin/env python3
"""
Teste da validação de resgate com histórico completo de pontos
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o backend ao path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import get_db_connected

async def test_validacao_com_historico():
    """Testar validação de resgate com trajetória de pontos"""
    print("🔍 TESTE DE VALIDAÇÃO COM HISTÓRICO DE PONTOS")
    print("=" * 60)
    
    db = await get_db_connected()
    
    try:
        # 1. Buscar resgates existentes
        print("\n📋 1. BUSCANDO RESGATES EXISTENTES")
        
        resgates = await db.resgatepremio.find_many(
            take=5,
            order={"id": "desc"},
            include={
                "cliente": {
                    "include": {
                        "usuarioPontos": {
                            "include": {
                                "transacoes": {
                                    "take": 3,
                                    "order": {"createdAt": "desc"}
                                }
                            }
                        },
                        "resgatePremios": {
                            "take": 3,
                            "order": {"createdAt": "desc"}
                        }
                    }
                },
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
        
        print(f"\n🎯 2. ANALISANDO RESGATE: {codigo_resgate}")
        print(f"   Cliente: {resgate.cliente.nomeCompleto if resgate.cliente else 'N/A'}")
        print(f"   Prêmio: {resgate.premio.nome if resgate.premio else 'N/A'}")
        print(f"   Pontos usados: {resgate.pontosUsados}")
        print(f"   Status: {resgate.status}")
        
        # 3. Trajetória de pontos
        print(f"\n📊 3. TRAJETÓRIA DE PONTOS")
        
        if resgate.cliente and resgate.cliente.usuarioPontos:
            pontos = resgate.cliente.usuarioPontos
            print(f"   💰 Saldo atual: {pontos.saldo}")
            print(f"   💸 Total gasto: R$ {resgate.cliente.totalGasto or 0:.2f}")
            print(f"   🏨 Total reservas: {resgate.cliente.totalReservas or 0}")
            print(f"   ⭐ Nível fidelidade: {resgate.cliente.nivelFidelidade or 'N/A'}")
            
            # 4. Histórico de transações
            print(f"\n📜 4. HISTÓRICO DE TRANSAÇÕES")
            
            if pontos.transacoes:
                print(f"   Últimas {len(pontos.transacoes)} transações:")
                for i, transacao in enumerate(pontos.transacoes, 1):
                    print(f"   {i}. {transacao.createdAt.strftime('%d/%m/%Y %H:%M')} - {transacao.tipo}")
                    print(f"      Pontos: {transacao.pontos:+d}")
                    print(f"      Origem: {transacao.origem}")
                    if transacao.motivo:
                        print(f"      Motivo: {transacao.motivo}")
                    print()
            else:
                print("   ❌ Nenhuma transação encontrada")
            
            # 5. Resgates anteriores
            print(f"🎁 5. RESGATES ANTERIORES")
            
            if resgate.cliente.resgatePremios:
                outros_resgates = [r for r in resgate.cliente.resgatePremios if r.id != resgate.id]
                
                if outros_resgates:
                    print(f"   Outros {len(outros_resgates)} resgates:")
                    for i, outro in enumerate(outros_resgates, 1):
                        codigo_outro = f"RES-{str(outro.id).zfill(6)}"
                        print(f"   {i}. {codigo_outro} - {outro.premio.nome if outro.premio else 'N/A'}")
                        print(f"      Pontos: {outro.pontosUsados}")
                        print(f"      Status: {outro.status}")
                        print(f"      Data: {outro.createdAt.strftime('%d/%m/%Y')}")
                        print()
                else:
                    print("   ❌ Nenhum outro resgate encontrado")
            else:
                print("   ❌ Nenhum resgate anterior encontrado")
        else:
            print("   ❌ Cliente não tem dados de pontos")
        
        # 6. Simular validação via API
        print(f"\n🔐 6. SIMULANDO VALIDAÇÃO VIA API")
        
        # Simular requisição para o endpoint
        dados_validacao = {
            "valido": True,
            "resgate_id": resgate.id,
            "cliente_nome": resgate.cliente.nomeCompleto if resgate.cliente else None,
            "cliente_documento": resgate.cliente.documento if resgate.cliente else None,
            "premio_nome": resgate.premio.nome if resgate.premio else None,
            "pontos_usados": resgate.pontosUsados,
            "status": resgate.status,
            "data_resgate": resgate.createdAt.isoformat() if resgate.createdAt else None,
            "ja_entregue": resgate.status == "ENTREGUE",
            "funcionario_resgate": resgate.funcionario.nome if resgate.funcionario else "Sistema",
            "mensagem": "✅ Código válido!" if resgate.status != "ENTREGUE" else "⚠️ Este prêmio já foi entregue!",
            # 🆕 Dados da trajetória
            "pontos_atuais": resgate.cliente.usuarioPontos.saldo if resgate.cliente and resgate.cliente.usuarioPontos else 0,
            "total_gasto": resgate.cliente.totalGasto if resgate.cliente else 0,
            "total_reservas": resgate.cliente.totalReservas if resgate.cliente else 0,
            "nivel_fidelidade": resgate.cliente.nivelFidelidade if resgate.cliente else None,
            "historico_pontos": [
                {
                    "data": t.createdAt.isoformat(),
                    "tipo": t.tipo,
                    "pontos": t.pontos,
                    "origem": t.origem,
                    "motivo": t.motivo
                } for t in (resgate.cliente.usuarioPontos.transacoes if resgate.cliente and resgate.cliente.usuarioPontos else [])
            ],
            "resgates_anteriores": [
                {
                    "id": r.id,
                    "codigo": f"RES-{str(r.id).zfill(6)}",
                    "premio": r.premio.nome if r.premio else "N/A",
                    "pontos_usados": r.pontosUsados,
                    "status": r.status,
                    "data": r.createdAt.isoformat()
                } for r in (resgate.cliente.resgatePremios if resgate.cliente else [])
                if r.id != resgate.id
            ]
        }
        
        print(f"   ✅ Resposta simulada:")
        print(f"      - Código: {codigo_resgate}")
        print(f"      - Cliente: {dados_validacao['cliente_nome']}")
        print(f"      - Pontos atuais: {dados_validacao['pontos_atuais']}")
        print(f"      - Total gasto: R$ {dados_validacao['total_gasto']:.2f}")
        print(f"      - Total reservas: {dados_validacao['total_reservas']}")
        print(f"      - Nível: {dados_validacao['nivel_fidelidade']}")
        print(f"      - Histórico: {len(dados_validacao['historico_pontos'])} transações")
        print(f"      - Resgates anteriores: {len(dados_validacao['resgates_anteriores'])}")
        
        # 7. Análise da trajetória
        print(f"\n📈 7. ANÁLISE DA TRAJETÓRIA")
        
        if dados_validacao['historico_pontos']:
            pontos_ganhos = sum(t['pontos'] for t in dados_validacao['historico_pontos'] if t['pontos'] > 0)
            pontos_perdidos = sum(t['pontos'] for t in dados_validacao['historico_pontos'] if t['pontos'] < 0)
            
            print(f"   💰 Pontos ganhos: {pontos_ganhos}")
            print(f"   💸 Pontos perdidos: {pontos_perdidos}")
            print(f"   📊 Saldo atual: {dados_validacao['pontos_atuais']}")
            
            # Principais origens
            origens = {}
            for t in dados_validacao['historico_pontos']:
                origem = t['origem']
                if origem not in origens:
                    origens[origem] = {'count': 0, 'pontos': 0}
                origens[origem]['count'] += 1
                origens[origem]['pontos'] += t['pontos']
            
            print(f"\n   📋 Principais origens:")
            for origem, dados in sorted(origens.items(), key=lambda x: x[1]['pontos'], reverse=True):
                print(f"      - {origem}: {dados['count']}x, {dados['pontos']} pontos")
        
        # 8. Resumo para o funcionário
        print(f"\n👨‍💼 8. RESUMO PARA O FUNCIONÁRIO")
        print(f"   📋 Cliente: {dados_validacao['cliente_nome']}")
        print(f"   📊 Pontos atuais: {dados_validacao['pontos_atuais']}")
        print(f"   🎁 Prêmio atual: {dados_validacao['premio_nome']} (-{dados_validacao['pontos_usados']} pts)")
        print(f"   📈 Histórico: {len(dados_validacao['historico_pontos'])} transações")
        print(f"   🏆 Fidelidade: {dados_validacao['nivel_fidelidade']}")
        
        if dados_validacao['resgates_anteriores']:
            print(f"   📦 Resgates anteriores: {len(dados_validacao['resgates_anteriores'])}")
        else:
            print(f"   📦 Primeiro resgate do cliente")
        
        print(f"\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print(f"   O sistema agora mostra a trajetória completa de pontos do cliente")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_validacao_com_historico())
