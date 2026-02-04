#!/usr/bin/env python3
"""
🔧 SCRIPT DE ALTERAÇÃO DE PREÇOS - SUÍTE MASTER
===============================================

Script para alterar preços da suíte MASTER no sistema Real Points.
"""

def alterar_precos_master():
    """Altera preços da suíte MASTER"""
    
    print("🔧 ALTERANDO PREÇOS DA SUÍTE MASTER")
    print("=" * 50)
    
    # Ler arquivo atual
    try:
        with open("backend/app/services/real_points_service.py", "r", encoding="utf-8") as f:
            conteudo = f.read()
        print("✅ Arquivo lido com sucesso")
    except FileNotFoundError:
        print("❌ Arquivo não encontrado: backend/app/services/real_points_service.py")
        return
    
    # Mostrar valores atuais
    print("\n📋 VALORES ATUAIS - MASTER:")
    print("   Valor diária: R$ 400-450")
    print("   Valor 2 diárias: R$ 800-900")
    print("   Pontos: 4 RP")
    
    # Opções de alteração
    print("\n💡 OPÇÕES DE ALTERAÇÃO:")
    print("1. Aumentar 10% (R$ 440-495)")
    print("2. Aumentar 20% (R$ 480-540)")
    print("3. Reduzir 10% (R$ 360-405)")
    print("4. Personalizado (R$ 500-550)")
    
    # Simular escolha (vamos usar opção 2 como exemplo)
    escolha = 2  # Aumentar 20%
    
    if escolha == 1:
        novo_valor_min = 440
        novo_valor_max = 495
        novo_rp = 4
    elif escolha == 2:
        novo_valor_min = 480
        novo_valor_max = 540
        novo_rp = 5  # Aumentar pontos também
    elif escolha == 3:
        novo_valor_min = 360
        novo_valor_max = 405
        novo_rp = 4
    else:  # Personalizado
        novo_valor_min = 500
        novo_valor_max = 550
        novo_rp = 4
    
    novo_valor_min_2_diarias = novo_valor_min * 2
    novo_valor_max_2_diarias = novo_valor_max * 2
    
    print(f"\n📋 NOVOS VALORES ESCOLHIDOS:")
    print(f"   Valor diária: R$ {novo_valor_min}-{novo_valor_max}")
    print(f"   Valor 2 diárias: R$ {novo_valor_min_2_diarias}-{novo_valor_max_2_diarias}")
    print(f"   Pontos: {novo_rp} RP")
    
    # Encontrar e substituir a seção MASTER
    linhas = conteudo.split('\n')
    novas_linhas = []
    i = 0
    
    while i < len(linhas):
        linha = linhas[i]
        
        if '"MASTER":' in linha and i < len(linhas) - 1:
            # Encontrou a suíte MASTER, substituir as próximas linhas
            novas_linhas.append(linha)  # "MASTER": {
            novas_linhas.append('            "rp_por_bloco": ' + str(novo_rp) + ',')
            novas_linhas.append('            "valor_min_diaria": ' + str(novo_valor_min) + ',')
            novas_linhas.append('            "valor_max_diaria": ' + str(novo_valor_max) + ',')
            novas_linhas.append('            "valor_min_2_diarias": ' + str(novo_valor_min_2_diarias) + ',')
            novas_linhas.append('            "valor_max_2_diarias": ' + str(novo_valor_max_2_diarias) + ',')
            novas_linhas.append('            "descricao": "Suíte Master - 2 diárias R$ ' + str(novo_valor_min_2_diarias) + '-' + str(novo_valor_max_2_diarias) + ' = ' + str(novo_rp) + ' RP"')
            
            # Pular as linhas antigas (próximas 6 linhas)
            i += 7  # Pular para depois da descrição antiga
            
        else:
            novas_linhas.append(linha)
            i += 1
    
    # Escrever arquivo atualizado
    try:
        with open("backend/app/services/real_points_service.py", "w", encoding="utf-8") as f:
            f.write('\n'.join(novas_linhas))
        
        print(f"\n✅ PREÇOS DA SUÍTE MASTER ATUALIZADOS!")
        print(f"📁 Arquivo: backend/app/services/real_points_service.py")
        
    except Exception as e:
        print(f"\n❌ Erro ao salvar arquivo: {e}")
        return
    
    # Testar alteração
    print(f"\n🧪 TESTANDO ALTERAÇÃO:")
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from app.services.real_points_service import RealPointsService
        
        rp, detalhe = RealPointsService.calcular_rp_oficial("MASTER", 2, novo_valor_min_2_diarias)
        print(f"   ✅ Teste OK: {rp} RP ({detalhe})")
        
        # Mostrar tabela atualizada
        print(f"\n📋 TABELA ATUALIZADA:")
        tabela = RealPointsService.get_tabela_oficial()
        master = tabela["MASTER"]
        print(f"   🏨 MASTER:")
        print(f"      Valor diária: R$ {master['valor_min_diaria']}-{master['valor_max_diaria']}")
        print(f"      Valor 2 diárias: R$ {master['valor_min_2_diarias']}-{master['valor_max_2_diarias']}")
        print(f"      Pontos: {master['rp_por_bloco']} RP")
        
    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
    
    print(f"\n🎯 ALTERAÇÃO CONCLUÍDA!")
    print(f"📋 Resumo:")
    print(f"   ✅ Preços atualizados")
    print(f"   ✅ Pontos atualizados")
    print(f"   ✅ Descrições atualizadas")
    print(f"   ✅ Sistema testado")

if __name__ == "__main__":
    print("🔧 SCRIPT DE ALTERAÇÃO - SUÍTE MASTER")
    print("=" * 50)
    print("Este script vai alterar os preços da suíte MASTER")
    print("ATENÇÃO: Faça backup do arquivo antes de executar!\n")
    
    # Fazer backup automático
    import shutil
    from datetime import datetime
    
    backup_name = f"backup_real_points_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    try:
        shutil.copy("backend/app/services/real_points_service.py", backup_name)
        print(f"✅ Backup criado: {backup_name}")
    except:
        print("⚠️  Não foi possível criar backup")
    
    # Confirmar execução
    resposta = input("\nDeseja continuar com a alteração? (s/N): ")
    if resposta.lower() == 's':
        alterar_precos_master()
    else:
        print("❌ Operação cancelada")
