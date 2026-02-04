#!/usr/bin/env python3
"""
Análise completa do sistema para identificar o que falta para produção
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

def analisar_sistema_para_producao():
    """Analisa o sistema completo e identifica o que falta para produção"""
    
    print('🔍 ANÁLISE COMPLETA - Sistema para Produção')
    print('=' * 70)
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        print('✅ Conectado ao banco de dados')
        
        # 1. Verificar estrutura do banco
        print('\n📊 1. ESTRUTURA DO BANCO DE DADOS')
        print('-' * 50)
        
        cursor.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        print(f'   📋 Tabelas encontradas: {len(tabelas)}')
        
        tabelas_criticas = ['clientes', 'usuarios', 'reservas', 'pagamentos', 'usuarios_pontos', 'transacoes_pontos', 'premios']
        tabelas_faltantes = []
        
        for tabela in tabelas:
            print(f'      ✅ {tabela["table_name"]}')
        
        for critica in tabelas_criticas:
            if not any(t["table_name"] == critica for t in tabelas):
                tabelas_faltantes.append(critica)
        
        if tabelas_faltantes:
            print(f'   ❌ Tabelas críticas faltando: {tabelas_faltantes}')
        else:
            print('   ✅ Todas as tabelas críticas presentes')
        
        # 2. Verificar dados essenciais
        print('\n📊 2. DADOS ESSENCIAIS')
        print('-' * 50)
        
        # Usuários admin
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE perfil = 'ADMIN'")
        admins = cursor.fetchone()["total"]
        print(f'   👤 Usuários Admin: {admins}')
        
        if admins == 0:
            print('   ❌ CRÍTICO: Nenhum usuário admin encontrado')
        
        # Clientes
        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        clientes = cursor.fetchone()["total"]
        print(f'   🧑 Clientes: {clientes}')
        
        # Quartos
        cursor.execute("SELECT COUNT(*) as total FROM quartos WHERE status = 'ATIVO'")
        quartos_ativos = cursor.fetchone()["total"]
        print(f'   🏨 Quartos ativos: {quartos_ativos}')
        
        if quartos_ativos == 0:
            print('   ❌ CRÍTICO: Nenhum quarto ativo encontrado')
        
        # Prêmios
        cursor.execute("SELECT COUNT(*) as total FROM premios WHERE ativo = TRUE")
        premios_ativos = cursor.fetchone()["total"]
        print(f'   🏆 Prêmios ativos: {premios_ativos}')
        
        # 3. Verificar configurações do sistema
        print('\n📊 3. CONFIGURAÇÕES DO SISTEMA')
        print('-' * 50)
        
        # Verificar se há senhas em texto plano
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM usuarios 
            WHERE senha_hash NOT LIKE '$2%' AND senha_hash NOT LIKE 'pbkdf2%'
        """)
        
        senhas_inseguras = cursor.fetchone()["total"]
        if senhas_inseguras > 0:
            print(f'   ❌ CRÍTICO: {senhas_inseguras} senhas inseguras (texto plano)')
        else:
            print('   ✅ Senhas seguras (hash)')
        
        # Verificar índices importantes
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND tablename IN ('clientes', 'reservas', 'pagamentos', 'usuarios_pontos')
        """)
        
        indices = cursor.fetchall()
        print(f'   🔍 Índices encontrados: {len(indices)}')
        
        # 4. Verificar endpoints críticos
        print('\n📊 4. ENDPOINTS CRÍTICOS')
        print('-' * 50)
        
        app_dir = Path('/app/app')
        routes_files = list(app_dir.rglob('*routes*.py'))
        
        endpoints_criticos = [
            'auth_routes.py',      # Autenticação
            'cliente_routes.py',    # Gestão de clientes
            'reserva_routes.py',   # Reservas
            'pagamento_routes.py', # Pagamentos
            'pontos_routes.py'     # Sistema de pontos
        ]
        
        endpoints_encontrados = []
        endpoints_faltantes = []
        
        for route_file in routes_files:
            nome_arquivo = route_file.name
            if nome_arquivo in endpoints_criticos:
                endpoints_encontrados.append(nome_arquivo)
        
        for critico in endpoints_criticos:
            if critico not in endpoints_encontrados:
                endpoints_faltantes.append(critico)
        
        print(f'   📁 Routes files encontrados: {len(routes_files)}')
        print(f'   ✅ Endpoints críticos: {len(endpoints_encontrados)}')
        
        if endpoints_faltantes:
            print(f'   ❌ Endpoints faltando: {endpoints_faltantes}')
        
        # 5. Verificar variáveis de ambiente
        print('\n📊 5. VARIÁVEIS DE AMBIENTE')
        print('-' * 50)
        
        env_vars_criticas = [
            'DATABASE_URL',
            'SECRET_KEY',
            'ENVIRONMENT'
        ]
        
        env_status = {}
        for var in env_vars_criticas:
            valor = os.environ.get(var)
            if valor:
                env_status[var] = '✅ Configurada'
            else:
                env_status[var] = '❌ Não configurada'
        
        for var, status in env_status.items():
            print(f'   {status} {var}')
        
        # 6. Verificar segurança
        print('\n📊 6. SEGURANÇA')
        print('-' * 50)
        
        # Verificar CORS
        try:
            with open('/app/app/main.py', 'r') as f:
                main_content = f.read()
            
            if 'CORS' in main_content:
                print('   ✅ CORS configurado')
            else:
                print('   ⚠️  CORS não configurado')
        except:
            print('   ❌ Não foi possível verificar CORS')
        
        # Verificar rate limiting
        if 'rate_limit' in main_content.lower():
            print('   ✅ Rate limiting configurado')
        else:
            print('   ⚠️  Rate limiting não configurado')
        
        # 7. Verificar sistema de pontos
        print('\n📊 7. SISTEMA DE PONTOS RP')
        print('-' * 50)
        
        # Verificar função calcular_pontos_rp
        cursor.execute("""
            SELECT proname 
            FROM pg_proc 
            WHERE proname = 'calcular_pontos_rp'
        """)
        
        func_pontos = cursor.fetchone()
        if func_pontos:
            print('   ✅ Função calcular_pontos_rp existe')
            
            # Testar função
            try:
                cursor.execute("SELECT calcular_pontos_rp(650, 2)")
                resultado = cursor.fetchone()
                if resultado:
                    print(f'   ✅ Teste função: R$ 650 (2 diárias) = {resultado[0]} RP')
                else:
                    print('   ❌ Função não retornou resultado')
            except Exception as e:
                print(f'   ❌ Erro ao testar função: {str(e)}')
        else:
            print('   ❌ Função calcular_pontos_rp não existe')
        
        # Verificar coluna rp_points
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuarios_pontos' 
            AND column_name = 'rp_points'
        """)
        
        coluna_rp = cursor.fetchone()
        if coluna_rp:
            print('   ✅ Coluna rp_points existe')
        else:
            print('   ❌ Coluna rp_points não existe')
        
        # 8. Verificar problemas conhecidos
        print('\n📊 8. PROBLEMAS CONHECIDOS')
        print('-' * 50)
        
        problemas = []
        
        # Verificar endpoints fantasmas
        if len(routes_files) > 10:
            problemas.append(f'Muitos arquivos de routes: {len(routes_files)} (possíveis fantasmas)')
        
        # Verificar datetime issues
        try:
            with open('/app/app/utils/datetime_utils.py', 'r') as f:
                datetime_utils = f.read()
            
            if 'now_utc' in datetime_utils:
                print('   ✅ Utils de datetime seguros')
            else:
                problemas.append('Utils de datetime não encontrados')
        except:
            problemas.append('Arquivo datetime_utils.py não encontrado')
        
        # Verificar validadores de estado
        try:
            with open('/app/app/core/state_validators.py', 'r') as f:
                state_validators = f.read()
            
            if 'StatusReserva' in state_validators:
                print('   ✅ Validadores de estado presentes')
            else:
                problemas.append('Validadores de estado inconsistentes')
        except:
            problemas.append('Arquivo state_validators.py não encontrado')
        
        if problemas:
            print('   ⚠️  Problemas identificados:')
            for i, problema in enumerate(problemas, 1):
                print(f'      {i}. {problema}')
        else:
            print('   ✅ Nenhum problema crítico identificado')
        
        # 9. Verificar performance
        print('\n📊 9. PERFORMANCE')
        print('-' * 50)
        
        # Verificar tamanho das tabelas (simplificado)
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                n_live_tup as live_tuples
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY live_tuples DESC
        """)
        
        stats_tabelas = cursor.fetchall()
        total_registros = sum(stat["live_tuples"] or 0 for stat in stats_tabelas)
        
        print(f'   📊 Total de registros: {total_registros}')
        
        if total_registros > 10000:
            print('   ⚠️  Muitos registros - considerar particionamento')
        else:
            print('   ✅ Volume de dados adequado')
        
        # 10. Resumo final
        print('\n📊 10. RESUMO FINAL - PRONTIDÃO PARA PRODUÇÃO')
        print('=' * 70)
        
        # Calcular score de prontidão
        score = 0
        max_score = 10
        
        if len(tabelas_faltantes) == 0: score += 1
        if admins > 0: score += 1
        if quartos_ativos > 0: score += 1
        if senhas_inseguras == 0: score += 1
        if len(endpoints_faltantes) == 0: score += 1
        if all('✅' in status for status in env_status.values()): score += 1
        if func_pontos and coluna_rp: score += 1
        if len(problemas) == 0: score += 1
        if total_registros < 10000: score += 1
        if len(indices) > 5: score += 1
        
        percentual = (score / max_score) * 100
        
        print(f'🎯 SCORE DE PRONTIDÃO: {score}/{max_score} ({percentual:.0f}%)')
        
        if percentual >= 90:
            print('🟢 SISTEMA PRONTO PARA PRODUÇÃO')
        elif percentual >= 70:
            print('🟡 SISTEMA QUASE PRONTO - Pequenos ajustes necessários')
        elif percentual >= 50:
            print('🟠 SISTEMA PRECISA DE AJUSTES - Várias correções necessárias')
        else:
            print('🔴 SISTEMA NÃO ESTÁ PRONTO - Muitas correções necessárias')
        
        # Lista de ações necessárias
        print('\n📋 AÇÕES NECESSÁRIAS:')
        
        if len(tabelas_faltantes) > 0:
            print(f'   🔧 Criar tabelas faltantes: {tabelas_faltantes}')
        
        if admins == 0:
            print('   🔧 Criar usuário administrador')
        
        if quartos_ativos == 0:
            print('   🔧 Configurar quartos ativos')
        
        if senhas_inseguras > 0:
            print(f'   🔧 Corrigir {senhas_inseguras} senhas inseguras')
        
        if len(endpoints_faltantes) > 0:
            print(f'   🔧 Implementar endpoints: {endpoints_faltantes}')
        
        if any('❌' in status for status in env_status.values()):
            print('   🔧 Configurar variáveis de ambiente')
        
        if not func_pontos or not coluna_rp:
            print('   🔧 Completar implementação do sistema RP')
        
        if len(problemas) > 0:
            print('   🔧 Resolver problemas conhecidos')
        
        if len(indices) < 5:
            print('   🔧 Otimizar índices do banco')
        
    except Exception as e:
        print(f'\n❌ Erro na análise: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    analisar_sistema_para_producao()
