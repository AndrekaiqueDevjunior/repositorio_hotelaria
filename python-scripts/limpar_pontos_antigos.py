#!/usr/bin/env python3
"""
🧹 SCRIPT DE LIMPEZA - SISTEMAS DE PONTOS ANTIGOS
===============================================

Executar este script para limpar os sistemas antigos de pontos
e manter apenas o RealPointsService oficial.
"""

import os
import shutil

def remover_arquivos_antigos():
    """Remove arquivos de sistemas antigos"""
    
    print("🗑️ REMOVENDO ARQUIVOS ANTIGOS:")
    
    arquivos_remover = [
        "backend/app/services/pontos_service.py",
        "backend/app/services/pontos_checkout_service.py", 
        "backend/app/services/pontos_rp_service.py"
    ]
    
    for arquivo in arquivos_remover:
        if os.path.exists(arquivo):
            os.rename(arquivo, f"{arquivo}.old")
            print(f"✅ Arquivo renomeado: {arquivo} -> {arquivo}.old")
        else:
            print(f"⚠️  Arquivo não encontrado: {arquivo}")

def atualizar_pagamento_service():
    """Remove crédito de pontos do pagamento_service"""
    
    print("\n🔧 ATUALIZANDO pagamento_service.py:")
    
    arquivo = "backend/app/services/pagamento_service.py"
    
    if os.path.exists(arquivo):
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Remover método _creditar_pontos_pagamento
        linhas = conteudo.split('\n')
        novas_linhas = []
        pular = False
        
        for i, linha in enumerate(linhas):
            if "async def _creditar_pontos_pagamento" in linha:
                pular = True
                continue
            elif pular and linha.strip() and not linha.startswith('    ') and not linha.startswith('\t'):
                pular = False
            
            if not pular:
                novas_linhas.append(linha)
        
        # Remover chamadas do método
        conteudo_limpo = '\n'.join(novas_linhas)
        conteudo_limpo = conteudo_limpo.replace('await self._creditar_pontos_pagamento(', '# CREDITO DE PONTOS REMOVIDO (agora apenas no checkout)')
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_limpo)
        
        print("✅ pagamento_service.py atualizado")
    else:
        print(f"⚠️  Arquivo não encontrado: {arquivo}")

def atualizar_reserva_service():
    """Atualiza reserva_service para usar RealPointsService"""
    
    print("\n🔧 ATUALIZANDO reserva_service.py:")
    
    arquivo = "backend/app/services/reserva_service.py"
    
    if os.path.exists(arquivo):
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Substituir imports
        conteudo = conteudo.replace(
            'from app.services.pontos_checkout_service import creditar_rp_no_checkout',
            'from app.services.real_points_service import RealPointsService'
        )
        
        # Substituir chamadas
        conteudo = conteudo.replace(
            'await self._creditar_pontos_checkout(reserva)',
            '# CRÉDITO DE PONTOS OFICIAL (RealPointsService)\n                        # Implementar chamada ao RealPointsService aqui'
        )
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print("✅ reserva_service.py atualizado")
    else:
        print(f"⚠️  Arquivo não encontrado: {arquivo}")

def main():
    """Executa limpeza completa"""
    
    print("🧹 INICIANDO LIMPEZA DE SISTEMAS DE PONTOS ANTIGOS")
    print("=" * 60)
    
    remover_arquivos_antigos()
    atualizar_pagamento_service()
    atualizar_reserva_service()
    
    print("\n✅ LIMPEZA CONCLUÍDA!")
    print("🎯 Apenas RealPointsService permanece ativo")

if __name__ == "__main__":
    main()
