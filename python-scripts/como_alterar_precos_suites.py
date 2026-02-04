#!/usr/bin/env python3
"""
💰 COMO ALTERAR PREÇOS DAS SUÍTES - REAL POINTS
============================================

Guia completo para alterar preços e pontos das suítes no sistema Real Points.
"""

import sys
import os

# Adicionar backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def mostrar_precos_atuais():
    """Mostra preços atuais das suítes"""
    
    print("💰 PREÇOS ATUAIS DAS SUÍTES")
    print("=" * 60)
    
    try:
        from app.services.real_points_service import RealPointsService
        
        tabela = RealPointsService.get_tabela_oficial()
        
        print("\n📋 TABELA OFICIAL ATUAL:")
        for suite, dados in tabela.items():
            print(f"\n🏨 {suite}:")
            print(f"   📊 Valor diária: R$ {dados['valor_min_diaria']}-{dados['valor_max_diaria']}")
            print(f"   💰 Valor 2 diárias: R$ {dados['valor_min_2_diarias']}-{dados['valor_max_2_diarias']}")
            print(f"   🎯 Pontos por 2 diárias: {dados['rp_por_bloco']} RP")
            print(f"   📝 Descrição: {dados['descricao']}")
        
        return tabela
        
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return {}

def simular_alteracao_master():
    """Simula alteração de preços da suíte MASTER"""
    
    print("\n🔧 SIMULAÇÃO DE ALTERAÇÃO - SUÍTE MASTER")
    print("=" * 60)
    
    try:
        from app.services.real_points_service import RealPointsService
        
        # Preços atuais
        tabela_atual = RealPointsService.get_tabela_oficial()
        master_atual = tabela_atual["MASTER"]
        
        print(f"\n📋 PREÇOS ATUAIS - MASTER:")
        print(f"   Valor diária: R$ {master_atual['valor_min_diaria']}-{master_atual['valor_max_diaria']}")
        print(f"   Valor 2 diárias: R$ {master_atual['valor_min_2_diarias']}-{master_atual['valor_max_2_diarias']}")
        print(f"   Pontos: {master_atual['rp_por_bloco']} RP")
        
        # Novos preços sugeridos
        print(f"\n💡 OPÇÕES DE ALTERAÇÃO:")
        
        opcoes = [
            {
                "nome": "Aumento 10%",
                "valor_min": int(master_atual['valor_min_diaria'] * 1.1),
                "valor_max": int(master_atual['valor_max_diaria'] * 1.1),
                "rp_por_bloco": 4
            },
            {
                "nome": "Aumento 20%",
                "valor_min": int(master_atual['valor_min_diaria'] * 1.2),
                "valor_max": int(master_atual['valor_max_diaria'] * 1.2),
                "rp_por_bloco": 5  # Pode aumentar pontos também
            },
            {
                "nome": "Redução 10%",
                "valor_min": int(master_atual['valor_min_diaria'] * 0.9),
                "valor_max": int(master_atual['valor_max_diaria'] * 0.9),
                "rp_por_bloco": 4
            },
            {
                "nome": "Personalizado",
                "valor_min": 500,
                "valor_max": 550,
                "rp_por_bloco": 4
            }
        ]
        
        for i, opcao in enumerate(opcoes, 1):
            valor_2_diarias_min = opcao["valor_min"] * 2
            valor_2_diarias_max = opcao["valor_max"] * 2
            
            print(f"\n{i}. {opcao['nome']}:")
            print(f"   Nova diária: R$ {opcao['valor_min']}-{opcao['valor_max']}")
            print(f"   Novo 2 diárias: R$ {valor_2_diarias_min}-{valor_2_diarias_max}")
            print(f"   Pontos: {opcao['rp_por_bloco']} RP")
            
            # Simular cálculo
            rp, detalhe = RealPointsService.calcular_rp_oficial(
                "MASTER", 2, valor_2_diarias_min
            )
            print(f"   Exemplo 2 diárias: {rp} RP ({detalhe})")
        
        return opcoes
        
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return []

def gerar_script_alteracao(suite, novo_valor_min, novo_valor_max, novo_rp):
    """Gera script para alterar preços"""
    
    print(f"\n🔧 GERANDO SCRIPT DE ALTERAÇÃO - {suite}")
    print("=" * 60)
    
    script = f'''#!/usr/bin/env python3
"""
🔧 SCRIPT DE ALTERAÇÃO DE PREÇOS - SUÍTE {suite}
===============================================

Script para alterar preços da suíte {suite} no sistema Real Points.
"""

def alterar_precos_suite():
    """Altera preços da suíte {suite}"""
    
    print("🔧 ALTERANDO PREÇOS DA SUÍTE {suite}")
    print("=" * 50)
    
    # Ler arquivo atual
    with open("backend/app/services/real_points_service.py", "r", encoding="utf-8") as f:
        conteudo = f.read()
    
    # Novos valores
    novo_valor_min_2_diarias = {novo_valor_min * 2}
    novo_valor_max_2_diarias = {novo_valor_max * 2}
    
    print(f"📋 NOVOS VALORES:")
    print(f"   Valor diária: R$ {novo_valor_min}-{novo_valor_max}")
    print(f"   Valor 2 diárias: R$ {novo_valor_min_2_diarias}-{novo_valor_max_2_diarias}")
    print(f"   Pontos: {novo_rp} RP")
    
    # Substituir valores no arquivo
    linhas = conteudo.split("\\n")
    novas_linhas = []
    
    for linha in linhas:
        if f'"{suite}":' in linha and "rp_por_bloco" in linhas[linhas.index(linha) + 1]:
            # Encontrou a suíte, substituir as próximas linhas
            novas_linhas.append(linha)
            novas_linhas.append(f'            "rp_por_bloco": {novo_rp},')
            novas_linhas.append(f'            "valor_min_diaria": {novo_valor_min},')
            novas_linhas.append(f'            "valor_max_diaria": {novo_valor_max},')
            novas_linhas.append(f'            "valor_min_2_diarias": {novo_valor_min_2_diarias},')
            novas_linhas.append(f'            "valor_max_2_diarias": {novo_valor_max_2_diarias},')
            
            # Pular as linhas antigas
            for _ in range(5):
                if linhas.index(linha) + 1 < len(linhas):
                    linha = linhas[linhas.index(linha) + 1]
            
            novas_linhas.append(f'            "descricao": "Suíte {suite} - 2 diárias R$ {novo_valor_min_2_diarias}-{novo_valor_max_2_diarias} = {novo_rp} RP"')
        else:
            novas_linhas.append(linha)
    
    # Escrever arquivo atualizado
    with open("backend/app/services/real_points_service.py", "w", encoding="utf-8") as f:
        f.write("\\n".join(novas_linhas))
    
    print(f"\\n✅ PREÇOS DA SUÍTE {suite} ATUALIZADOS!")
    print(f"📁 Arquivo: backend/app/services/real_points_service.py")
    
    # Testar alteração
    print(f"\\n🧪 TESTANDO ALTERAÇÃO:")
    try:
        from app.services.real_points_service import RealPointsService
        
        rp, detalhe = RealPointsService.calcular_rp_oficial("{suite}", 2, novo_valor_min_2_diarias)
        print(f"   ✅ Teste OK: {rp} RP ({detalhe})")
        
    except Exception as e:
        print(f"   ❌ Erro no teste: {{e}}")

if __name__ == "__main__":
    alterar_precos_suite()
'''
    
    # Salvar script
    nome_arquivo = f"alterar_precos_{suite.lower()}.py"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(script)
    
    print(f"✅ Script gerado: {nome_arquivo}")
    print(f"📋 Para executar: py {nome_arquivo}")
    
    return nome_arquivo

def mostrar_impactos_alteracao():
    """Mostra impactos da alteração de preços"""
    
    print("\n📊 IMPACTOS DA ALTERAÇÃO DE PREÇOS")
    print("=" * 60)
    
    print("\n🎯 O QUE MUDA AO ALTERAR PREÇOS:")
    
    impactos = [
        {
            "area": "Cálculo de Pontos",
            "impacto": "Não afeta diretamente (baseado em diárias, não valor)",
            "observacao": "Pontos são por bloco de 2 diárias, não por valor"
        },
        {
            "area": "Validações de Valor",
            "impacto": "Atualiza faixas de validação",
            "observacao": "Sistema valida se valor está na faixa esperada"
        },
        {
            "area": "Relatórios",
            "impacto": "Novos valores aparecerão nos relatórios",
            "observacao": "Descrições e faixas de valor atualizadas"
        },
        {
            "area": "Reservas Existentes",
            "impacto": "Não afeta reservas já concluídas",
            "observacao": "Pontos já creditados permanecem"
        },
        {
            "area": "Novas Reservas",
            "impacto": "Usarão novas faixas de valor",
            "observacao": "Validação baseada nos novos preços"
        }
    ]
    
    for impacto in impactos:
        print(f"\n📋 {impacto['area']}:")
        print(f"   🎯 Impacto: {impacto['impacto']}")
        print(f"   📝 Observação: {impacto['observacao']}")
    
    print(f"\n⚠️  ATENÇÃO:")
    print(f"   • Alteração não afeta cálculo de pontos (baseado em diárias)")
    print(f"   • Altera apenas faixas de validação de valor")
    print(f"   • Descrições e relatórios serão atualizados")
    print(f"   • Faça backup antes de alterar")

def main():
    """Função principal"""
    
    print("💰 COMO ALTERAR PREÇOS DAS SUÍTES - REAL POINTS")
    print("=" * 70)
    print("Guia completo para alterar preços das suítes no sistema.")
    
    # 1. Mostrar preços atuais
    tabela_atual = mostrar_precos_atuais()
    
    if not tabela_atual:
        print("❌ Não foi possível carregar preços atuais")
        return
    
    # 2. Simular alteração MASTER
    opcoes = simular_alteracao_master()
    
    # 3. Mostrar impactos
    mostrar_impactos_alteracao()
    
    # 4. Gerar script para alteração
    print(f"\n🔧 GERANDO SCRIPTS DE ALTERAÇÃO:")
    print("-" * 40)
    
    # Script para MASTER (exemplo)
    if opcoes:
        # Usar primeira opção como exemplo
        opcao_exemplo = opcoes[1]  # Aumento 20%
        script_master = gerar_script_alteracao(
            "MASTER", 
            opcao_exemplo["valor_min"], 
            opcao_exemplo["valor_max"], 
            opcao_exemplo["rp_por_bloco"]
        )
    
    print(f"\n📋 PASSOS PARA ALTERAR PREÇOS:")
    print(f"1. ⚠️  Faça backup do arquivo real_points_service.py")
    print(f"2. 🔧 Execute o script gerado: py alterar_precos_master.py")
    print(f"3. 🧪 Teste com: py test_real_points_final.py")
    print(f"4. ✅ Verifique se tudo funcionou corretamente")
    
    print(f"\n🎯 RESPOSTA DIRETA:")
    print(f"✅ SIM, você pode mudar o preço da suíte MASTER!")
    print(f"💰 Preço atual: R$ 400-450 por diária")
    print(f"🎯 Pontos: 4 RP por 2 diárias")
    print(f"🔧 Use o script gerado para alterar facilmente!")

if __name__ == "__main__":
    main()
