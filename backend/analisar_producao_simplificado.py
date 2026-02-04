#!/usr/bin/env python3
"""
Análise simplificada do que falta para produção
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def analisar_para_producao_simplificado():
    """Análise simplificada focada no essencial para produção"""
    
    print('🎯 ANÁLISE ESSENCIAL - Sistema para Produção')
    print('=' * 60)
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        # 1. Verificar estrutura básica
        print('\n📊 1. ESTRUTURA BÁSICA')
        print('-' * 40)
        
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        total_tabelas = cursor.fetchone()["total"]
        print(f'   📋 Tabelas: {total_tabelas}')
        
        # 2. Verificar dados essenciais
        print('\n👥 2. DADOS ESSENCIAIS')
        print('-' * 40)
        
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE perfil = 'ADMIN'")
        admins = cursor.fetchone()["total"]
        print(f'   👤 Admins: {admins}')
        
        cursor.execute("SELECT COUNT(*) as total FROM quartos WHERE status = 'ATIVO'")
        quartos = cursor.fetchone()["total"]
        print(f'   🏨 Quartos ativos: {quartos}')
        
        cursor.execute("SELECT COUNT(*) as total FROM premios WHERE ativo = TRUE")
        premios = cursor.fetchone()["total"]
        print(f'   🏆 Prêmios: {premios}')
        
        # 3. Verificar segurança crítica
        print('\n🔒 3. SEGURANÇA CRÍTICA')
        print('-' * 40)
        
        # Senhas inseguras
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM usuarios 
            WHERE senha_hash NOT LIKE '$2%' AND senha_hash NOT LIKE 'pbkdf2%'
        """)
        senhas_inseguras = cursor.fetchone()["total"]
        print(f'   🔐 Senhas inseguras: {senhas_inseguras}')
        
        # 4. Verificar sistema de pontos
        print('\n💎 4. SISTEMA DE PONTOS')
        print('-' * 40)
        
        # Verificar coluna rp_points
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM information_schema.columns 
            WHERE table_name = 'usuarios_pontos' 
            AND column_name = 'rp_points'
        """)
        coluna_rp = cursor.fetchone()["total"]
        print(f'   💰 Coluna rp_points: {"OK" if coluna_rp > 0 else "FALTANDO"}')
        
        # Verificar função
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM pg_proc 
            WHERE proname = 'calcular_pontos_rp'
        """)
        func_rp = cursor.fetchone()["total"]
        print(f'   ⚙️  Função calcular_pontos_rp: {"OK" if func_rp > 0 else "FALTANDO"}')
        
        # 5. Verificar endpoints
        print('\n🌐 5. ENDPOINTS')
        print('-' * 40)
        
        import glob
        routes_files = glob.glob('/app/app/api/v1/*routes.py')
        print(f'   📁 Arquivos de routes: {len(routes_files)}')
        
        # 6. Verificar ambiente
        print('\n⚙️ 6. AMBIENTE')
        print('-' * 40)
        
        env_vars = ['DATABASE_URL', 'SECRET_KEY', 'ENVIRONMENT']
        for var in env_vars:
            status = "✅" if os.environ.get(var) else "❌"
            print(f'   {status} {var}')
        
        # 7. Calcular score
        print('\n📊 7. SCORE DE PRONTIDÃO')
        print('-' * 40)
        
        score = 0
        max_score = 7
        
        if total_tabelas >= 10: score += 1
        if admins > 0: score += 1
        if quartos > 0: score += 1
        if senhas_inseguras == 0: score += 1
        if coluna_rp > 0 and func_rp > 0: score += 1
        if len(routes_files) >= 5: score += 1
        if all(os.environ.get(var) for var in env_vars): score += 1
        
        percentual = (score / max_score) * 100
        
        print(f'🎯 Score: {score}/{max_score} ({percentual:.0f}%)')
        
        if percentual >= 85:
            print('🟢 PRONTO PARA PRODUÇÃO')
        elif percentual >= 70:
            print('🟡 QUASE PRONTO - Pequenos ajustes')
        else:
            print('🔴 PRECISA DE CORREÇÕES')
        
        # 8. Lista de correções necessárias
        print('\n🔧 8. CORREÇÕES NECESSÁRIAS')
        print('-' * 40)
        
        correcoes = []
        
        if senhas_inseguras > 0:
            correcoes.append(f'🔐 Corrigir {senhas_inseguras} senhas inseguras')
        
        if coluna_rp == 0:
            correcoes.append('💰 Adicionar coluna rp_points')
        
        if func_rp == 0:
            correcoes.append('⚙️  Criar função calcular_pontos_rp')
        
        if admins == 0:
            correcoes.append('👤 Criar usuário admin')
        
        if quartos == 0:
            correcoes.append('🏨 Configurar quartos ativos')
        
        if not os.environ.get('SECRET_KEY'):
            correcoes.append('🔑 Configurar SECRET_KEY')
        
        if len(routes_files) < 5:
            correcoes.append('📁 Implementar endpoints essenciais')
        
        if correcoes:
            print('Correções necessárias:')
            for i, correcao in enumerate(correcoes, 1):
                print(f'   {i}. {correcao}')
        else:
            print('✅ Nenhuma correção crítica necessária!')
        
        # 9. Recomendações adicionais
        print('\n💡 9. RECOMENDAÇÕES ADICIONAIS')
        print('-' * 40)
        
        recomendacoes = [
            '🔒 Implementar rate limiting',
            '📊 Adicionar monitoring e logs',
            '🔄 Configurar backups automáticos',
            '🚀 Configurar HTTPS em produção',
            '📝 Implementar health checks',
            '🧪 Adicionar testes automatizados',
            '📋 Documentar API endpoints',
            '🔧 Limpar endpoints fantasmas'
        ]
        
        for rec in recomendacoes:
            print(f'   {rec}')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    analisar_para_producao_simplificado()
