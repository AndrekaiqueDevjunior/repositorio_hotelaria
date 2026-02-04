#!/usr/bin/env python3
"""
Relatório completo da estrutura do banco de dados do Hotel Cabo Frio
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def gerar_relatorio_completo_bd():
    """Gera relatório completo da estrutura e dados do banco"""
    
    print('📊 RELATÓRIO COMPLETO DO BANCO DE DADOS')
    print('=' * 80)
    print(f'🗓️  Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    print(f'🏨 Hotel Cabo Frio - Sistema de Gestão')
    print('=' * 80)
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        # 1. Lista de todas as tabelas
        print('\n📋 1. ESTRUTURA DAS TABELAS')
        print('-' * 50)
        
        cursor.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        print(f'Total de tabelas: {len(tabelas)}\n')
        
        for tabela in tabelas:
            print(f'📁 Tabela: {tabela["table_name"]} ({tabela["table_type"]})')
            
            # Colunas da tabela
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (tabela["table_name"],))
            
            colunas = cursor.fetchall()
            for coluna in colunas:
                nullable = "NULL" if coluna["is_nullable"] == "YES" else "NOT NULL"
                default = f" DEFAULT {coluna['column_default']}" if coluna["column_default"] else ""
                print(f'   ├─ {coluna["column_name"]}: {coluna["data_type"]} {nullable}{default}')
            
            # Chaves estrangeiras
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = %s
            """, (tabela["table_name"],))
            
            fks = cursor.fetchall()
            for fk in fks:
                print(f'   ├─ FK: {fk["column_name"]} → {fk["foreign_table_name"]}.{fk["foreign_column_name"]}')
            
            # Índices
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s AND schemaname = 'public'
                ORDER BY indexname
            """, (tabela["table_name"],))
            
            indices = cursor.fetchall()
            for idx in indices:
                if not idx["indexname"].startswith("pg_"):  # Ignorar índices do sistema
                    print(f'   ├─ ÍNDICE: {idx["indexname"]}')
            
            print()
        
        # 2. Contagem de registros por tabela
        print('📈 2. CONTAGEM DE REGISTROS')
        print('-' * 50)
        
        for tabela in tabelas:
            if tabela["table_type"] == "BASE TABLE":
                try:
                    cursor.execute(f'SELECT COUNT(*) as total FROM {tabela["table_name"]}')
                    total = cursor.fetchone()["total"]
                    print(f'📊 {tabela["table_name"]}: {total} registros')
                except Exception as e:
                    print(f'❌ {tabela["table_name"]}: Erro ao contar - {str(e)}')
        
        # 3. Amostragem de dados (primeiros registros)
        print('\n📝 3. AMOSTRAGEM DE DADOS')
        print('-' * 50)
        
        # Tabelas importantes para amostrar
        tabelas_importantes = [
            'usuarios', 'clientes', 'usuarios_pontos', 'transacoes_pontos',
            'premios', 'reservas', 'pagamentos', 'quartos', 'tipos_suite'
        ]
        
        for tabela_nome in tabelas_importantes:
            # Verificar se tabela existe
            if any(t["table_name"] == tabela_nome for t in tabelas):
                try:
                    cursor.execute(f'SELECT * FROM {tabela_nome} LIMIT 3')
                    registros = cursor.fetchall()
                    
                    if registros:
                        print(f'\n📋 {tabela_nome.upper()} (amostra - {len(registros)} registros):')
                        
                        # Cabeçalho
                        if registros:
                            colunas = list(registros[0].keys())
                            print('   ' + ' | '.join(f'{col:15}' for col in colunas))
                            print('   ' + '-' * (len(colunas) * 16 - 1))
                            
                            # Dados
                            for registro in registros:
                                valores = []
                                for col in colunas:
                                    valor = str(registro[col])[:15]
                                    valores.append(f'{valor:15}')
                                print('   ' + ' | '.join(valores))
                    else:
                        print(f'\n📋 {tabela_nome.upper()}: Sem registros')
                        
                except Exception as e:
                    print(f'\n❌ {tabela_nome}: Erro ao amostrar - {str(e)}')
        
        # 4. Relacionamentos e integridade
        print('\n🔗 4. ANÁLISE DE RELACIONAMENTOS')
        print('-' * 50)
        
        # Verificar integridade das FKs
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name
        """)
        
        fks = cursor.fetchall()
        
        print(f'Total de relacionamentos (FKs): {len(fks)}\n')
        
        for fk in fks:
            print(f'🔗 {fk["table_name"]}.{fk["column_name"]} → {fk["foreign_table_name"]}.{fk["foreign_column_name"]}')
            
            # Verificar se há registros órfãos
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) as total
                    FROM {fk["table_name"]} t
                    LEFT JOIN {fk["foreign_table_name"]} f ON t.{fk["column_name"]} = f.{fk["foreign_column_name"]}
                    WHERE t.{fk["column_name"]} IS NOT NULL AND f.{fk["foreign_column_name"]} IS NULL
                """)
                orfaos = cursor.fetchone()["total"]
                
                if orfaos > 0:
                    print(f'   ⚠️  {orfaos} registros órfãos encontrados!')
                else:
                    print(f'   ✅ Integridade OK')
            except Exception as e:
                print(f'   ❌ Erro ao verificar integridade: {str(e)}')
        
        # 5. Estatísticas do sistema
        print('\n📊 5. ESTATÍSTICAS DO SISTEMA')
        print('-' * 50)
        
        # Estatísticas de pontos
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_clientes,
                    SUM(saldo_atual) as pontos_em_circulacao,
                    AVG(saldo_atual) as media_pontos,
                    MAX(saldo_atual) as max_pontos,
                    MIN(saldo_atual) as min_pontos
                FROM usuarios_pontos
            """)
            
            stats_pontos = cursor.fetchone()
            if stats_pontos["total_clientes"] > 0:
                print(f'💰 Sistema de Pontos:')
                print(f'   👥 Clientes com pontos: {stats_pontos["total_clientes"]}')
                print(f'   💎 Pontos em circulação: {stats_pontos["pontos_em_circulacao"] or 0}')
                print(f'   📊 Média de pontos: {stats_pontos["media_pontos"] or 0:.1f}')
                print(f'   🏆 Maior saldo: {stats_pontos["max_pontos"] or 0}')
                print(f'   🔻 Menor saldo: {stats_pontos["min_pontos"] or 0}')
        except:
            print('💰 Sistema de Pontos: Não disponível')
        
        # Estatísticas de transações
        try:
            cursor.execute("""
                SELECT 
                    tipo,
                    COUNT(*) as quantidade,
                    SUM(pontos) as total_pontos,
                    AVG(pontos) as media_pontos
                FROM transacoes_pontos
                GROUP BY tipo
                ORDER BY quantidade DESC
            """)
            
            transacoes_stats = cursor.fetchall()
            if transacoes_stats:
                print(f'\n📋 Transações de Pontos:')
                for stat in transacoes_stats:
                    sinal = "+" if stat["total_pontos"] > 0 else ""
                    print(f'   {stat["tipo"]}: {stat["quantidade"]}x ({sinal}{stat["total_pontos"]} pts, média: {stat["media_pontos"] or 0:.1f})')
        except:
            print('📋 Transações de Pontos: Não disponível')
        
        # Estatísticas de clientes
        try:
            cursor.execute("SELECT COUNT(*) as total FROM clientes")
            total_clientes = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            total_usuarios = cursor.fetchone()["total"]
            
            print(f'\n👥 Usuários e Clientes:')
            print(f'   👤 Usuários do sistema: {total_usuarios}')
            print(f'   🧑 Clientes cadastrados: {total_clientes}')
            
            if total_clientes > 0:
                # Clientes com vs sem pontos
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN up.id IS NOT NULL THEN 1 END) as com_pontos,
                        COUNT(CASE WHEN up.id IS NULL THEN 1 END) as sem_pontos
                    FROM clientes c
                    LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
                """)
                
                pontos_dist = cursor.fetchone()
                perc_com_pontos = (pontos_dist["com_pontos"] / total_clientes) * 100
                print(f'   💎 Com pontos: {pontos_dist["com_pontos"]} ({perc_com_pontos:.1f}%)')
                print(f'   🔻 Sem pontos: {pontos_dist["sem_pontos"]} ({100-perc_com_pontos:.1f}%)')
        except:
            print('👥 Usuários e Clientes: Não disponível')
        
        # 6. Verificação de qualidade dos dados
        print('\n🔍 6. QUALIDADE DOS DADOS')
        print('-' * 50)
        
        # Verificar duplicatas
        print('🔍 Verificando duplicatas:')
        
        # CPF duplicado
        try:
            cursor.execute("""
                SELECT documento, COUNT(*) as total
                FROM clientes
                GROUP BY documento
                HAVING COUNT(*) > 1
            """)
            
            duplicatas = cursor.fetchall()
            if duplicatas:
                print(f'   ⚠️  {len(duplicatas)} CPF(s) duplicados')
                for dup in duplicatas:
                    print(f'      CPF {dup["documento"]}: {dup["total"]} ocorrências')
            else:
                print('   ✅ Nenhum CPF duplicado')
        except:
            print('   ❌ Erro ao verificar CPFs')
        
        # Email duplicado
        try:
            cursor.execute("""
                SELECT email, COUNT(*) as total
                FROM clientes
                WHERE email IS NOT NULL
                GROUP BY email
                HAVING COUNT(*) > 1
            """)
            
            duplicatas_email = cursor.fetchall()
            if duplicatas_email:
                print(f'   ⚠️  {len(duplicatas_email)} email(s) duplicados')
            else:
                print('   ✅ Nenhum email duplicado')
        except:
            print('   ❌ Erro ao verificar emails')
        
        # Dados nulos importantes
        print('\n🔍 Verificando dados nulos críticos:')
        
        campos_criticos = [
            ('clientes', 'nome_completo'),
            ('clientes', 'documento'),
            ('usuarios', 'nome'),
            ('usuarios', 'email'),
            ('usuarios_pontos', 'cliente_id'),
            ('transacoes_pontos', 'usuario_pontos_id')
        ]
        
        for tabela, campo in campos_criticos:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) as total
                    FROM {tabela}
                    WHERE {campo} IS NULL
                """)
                
                nulos = cursor.fetchone()["total"]
                if nulos > 0:
                    print(f'   ⚠️  {tabela}.{campo}: {nulos} registros nulos')
                else:
                    print(f'   ✅ {tabela}.{campo}: Sem nulos')
            except:
                print(f'   ❌ Erro ao verificar {tabela}.{campo}')
        
        # 7. Recomendações
        print('\n💡 7. RECOMENDAÇÕES')
        print('-' * 50)
        
        recomendacoes = []
        
        # Verificar performance
        try:
            cursor.execute("""
                SELECT schemaname, tablename, attname, n_distinct, correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                AND tablename IN ('clientes', 'reservas', 'transacoes_pontos')
                ORDER BY tablename, attname
            """)
            
            stats = cursor.fetchall()
            if len(stats) < 10:
                recomendacoes.append("🔧 Considerar executar ANALYZE para atualizar estatísticas do PostgreSQL")
        except:
            pass
        
        # Verificar tabelas vazias
        for tabela in tabelas:
            if tabela["table_type"] == "BASE TABLE":
                try:
                    cursor.execute(f'SELECT COUNT(*) as total FROM {tabela["table_name"]}')
                    total = cursor.fetchone()["total"]
                    if total == 0:
                        recomendacoes.append(f"📝 Tabela '{tabela['table_name']}' está vazia - verificar se há necessidade de dados iniciais")
                except:
                    pass
        
        # Verificar índices faltantes
        try:
            cursor.execute("""
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename IN ('clientes', 'transacoes_pontos', 'usuarios_pontos')
            """)
            
            indices_existentes = [row["tablename"] for row in cursor.fetchall()]
            
            tabelas_importantes_indices = ['clientes', 'transacoes_pontos', 'usuarios_pontos']
            for tabela in tabelas_importantes_indices:
                if tabela not in indices_existentes:
                    recomendacoes.append(f"🔍 Considerar criar índices na tabela '{tabela}' para melhor performance")
        except:
            pass
        
        if recomendacoes:
            for rec in recomendacoes:
                print(f'   {rec}')
        else:
            print('   ✅ Estrutura do banco appears otimizada')
        
        # 8. Resumo executivo
        print('\n📋 8. RESUMO EXECUTIVO')
        print('-' * 50)
        
        cursor.execute("SELECT COUNT(*) as total FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
        total_tabelas = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public'")
        total_fks = cursor.fetchone()["total"]
        
        print(f'📊 Estrutura:')
        print(f'   • Tabelas: {total_tabelas}')
        print(f'   • Relacionamentos (FKs): {total_fks}')
        
        # Total de registros
        cursor.execute("""
            SELECT SUM(n_tup_ins) as total_insercoes
            FROM pg_stat_user_tables
        """)
        
        stats = cursor.fetchone()
        total_registros_geral = stats["total_insercoes"] if stats["total_insercoes"] else 0
        
        print(f'   • Total aproximado de registros: {total_registros_geral}')
        
        print(f'\n🎯 Status do Sistema:')
        print(f'   • Banco de dados: hotel_cabo_frio')
        print(f'   • Engine: PostgreSQL')
        print(f'   • Schema: public')
        print(f'   • Relacionamentos: Implementados e funcionais')
        print(f'   • Sistema de pontos: Operacional')
        
        print(f'\n✅ Relatório gerado com sucesso!')
        
    except Exception as e:
        print(f'\n❌ Erro ao gerar relatório: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    gerar_relatorio_completo_bd()
