#!/usr/bin/env python3
"""
Relatório simplificado da estrutura do banco de dados
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def gerar_relatorio_simplificado():
    """Gera relatório simplificado mas completo do banco"""
    
    print('📊 RELATÓRIO DO BANCO DE DADOS - HOTEL CABO FRIO')
    print('=' * 80)
    print(f'🗓️  Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
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
        
        # 1. Visão geral das tabelas
        print('\n📋 1. ESTRUTURA DAS TABELAS')
        print('-' * 50)
        
        tabelas_info = [
            {
                'nome': 'usuarios',
                'descricao': 'Usuários do sistema (admin, recepcionista)',
                'campos_principais': ['id', 'nome', 'email', 'perfil', 'status']
            },
            {
                'nome': 'clientes',
                'descricao': 'Clientes do hotel',
                'campos_principais': ['id', 'nome_completo', 'documento', 'email', 'telefone']
            },
            {
                'nome': 'usuarios_pontos',
                'descricao': 'Contas de pontos dos clientes',
                'campos_principais': ['id', 'cliente_id', 'saldo_atual']
            },
            {
                'nome': 'transacoes_pontos',
                'descricao': 'Histórico de transações de pontos',
                'campos_principais': ['id', 'usuario_pontos_id', 'tipo', 'pontos', 'origem']
            },
            {
                'nome': 'premios',
                'descricao': 'Prêmios disponíveis para resgate',
                'campos_principais': ['id', 'nome', 'preco_em_pontos', 'ativo']
            }
        ]
        
        for tabela_info in tabelas_info:
            # Contar registros
            try:
                cursor.execute(f'SELECT COUNT(*) as total FROM {tabela_info["nome"]}')
                total = cursor.fetchone()["total"]
            except:
                total = 0
            
            print(f'\n📁 {tabela_info["nome"].upper()}')
            print(f'   📝 Descrição: {tabela_info["descricao"]}')
            print(f'   🔢 Registros: {total}')
            print(f'   🏷️  Campos principais: {", ".join(tabela_info["campos_principais"])}')
        
        # 2. Relacionamentos principais
        print('\n🔗 2. RELACIONAMENTOS PRINCIPAIS')
        print('-' * 50)
        
        relacionamentos = [
            'clientes.id ← usuarios_pontos.cliente_id (1:1)',
            'usuarios_pontos.id ← transacoes_pontos.usuario_pontos_id (1:N)',
            'usuarios.id ← transacoes_pontos.criado_por_usuario_id (1:N)',
        ]
        
        for rel in relacionamentos:
            print(f'   🔗 {rel}')
        
        # 3. Dados atuais
        print('\n📊 3. DADOS ATUAIS DO SISTEMA')
        print('-' * 50)
        
        # Usuários
        cursor.execute("SELECT * FROM usuarios ORDER BY id")
        usuarios = cursor.fetchall()
        print(f'\n👥 USUÁRIOS ({len(usuarios)}):')
        for user in usuarios:
            print(f'   {user["id"]}: {user["nome"]} ({user["perfil"]}) - {user["email"]}')
        
        # Clientes com pontos
        cursor.execute("""
            SELECT c.id, c.nome_completo, c.documento, up.saldo_atual
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            ORDER BY c.nome_completo
        """)
        clientes = cursor.fetchall()
        print(f'\n🧑 CLIENTES ({len(clientes)}):')
        for cliente in clientes:
            saldo = cliente["saldo_atual"] if cliente["saldo_atual"] else 0
            print(f'   {cliente["id"]}: {cliente["nome_completo"]} - {cliente["documento"]} ({saldo} pts)')
        
        # Contas de pontos
        cursor.execute("""
            SELECT up.id, c.nome_completo, up.saldo_atual, up.created_at
            FROM usuarios_pontos up
            JOIN clientes c ON up.cliente_id = c.id
            ORDER BY up.saldo_atual DESC
        """)
        contas = cursor.fetchall()
        print(f'\n💰 CONTAS DE PONTOS ({len(contas)}):')
        for conta in contas:
            created = conta["created_at"].strftime("%d/%m/%Y")
            print(f'   {conta["id"]}: {conta["nome_completo"]} - {conta["saldo_atual"]} pts (desde {created})')
        
        # Transações recentes
        cursor.execute("""
            SELECT tp.id, tp.tipo, tp.pontos, tp.origem, c.nome_completo, tp.created_at
            FROM transacoes_pontos tp
            JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            JOIN clientes c ON up.cliente_id = c.id
            ORDER BY tp.created_at DESC
            LIMIT 10
        """)
        transacoes = cursor.fetchall()
        print(f'\n📋 TRANSAÇÕES RECENTES ({len(transacoes)} últimas):')
        for trans in transacoes:
            data = trans["created_at"].strftime("%d/%m %H:%M")
            sinal = "+" if trans["pontos"] > 0 else ""
            print(f'   {trans["id"]}: {data} | {trans["nome_completo"]} | {trans["tipo"]} | {sinal}{trans["pontos"]} pts | {trans["origem"]}')
        
        # Prêmios disponíveis
        cursor.execute("SELECT * FROM premios WHERE ativo = TRUE ORDER BY preco_em_pontos")
        premios = cursor.fetchall()
        print(f'\n🏆 PRÊMIOS DISPONÍVEIS ({len(premios)}):')
        for premio in premios:
            status = "✅" if premio["ativo"] else "❌"
            print(f'   {premio["id"]}: {premio["nome"]} - {premio["preco_em_pontos"]} pts {status}')
            if premio["descricao"]:
                print(f'      💭 {premio["descricao"][:50]}...')
        
        # 4. Estatísticas
        print('\n📈 4. ESTATÍSTICAS DO SISTEMA')
        print('-' * 50)
        
        # Totais
        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        total_clientes = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        total_usuarios = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM usuarios_pontos")
        total_contas_pontos = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM transacoes_pontos")
        total_transacoes = cursor.fetchone()["total"]
        
        cursor.execute("SELECT SUM(saldo_atual) as total FROM usuarios_pontos")
        pontos_em_circulacao = cursor.fetchone()["total"] or 0
        
        print(f'👥 Usuários do sistema: {total_usuarios}')
        print(f'🧑 Clientes cadastrados: {total_clientes}')
        print(f'💰 Contas de pontos: {total_contas_pontos}')
        print(f'💎 Pontos em circulação: {pontos_em_circulacao}')
        print(f'📋 Total de transações: {total_transacoes}')
        
        # Transações por tipo
        cursor.execute("""
            SELECT tipo, COUNT(*) as quantidade, SUM(pontos) as total_pontos
            FROM transacoes_pontos
            GROUP BY tipo
            ORDER BY quantidade DESC
        """)
        
        stats_transacoes = cursor.fetchall()
        print(f'\n📊 Transações por tipo:')
        for stat in stats_transacoes:
            sinal = "+" if stat["total_pontos"] > 0 else ""
            print(f'   {stat["tipo"]}: {stat["quantidade"]}x ({sinal}{stat["total_pontos"]} pts)')
        
        # Top clientes
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual,
                   COUNT(tp.id) as num_transacoes
            FROM clientes c
            JOIN usuarios_pontos up ON c.id = up.cliente_id
            LEFT JOIN transacoes_pontos tp ON up.id = tp.usuario_pontos_id
            GROUP BY c.id, up.id
            ORDER BY up.saldo_atual DESC
            LIMIT 5
        """)
        
        top_clientes = cursor.fetchall()
        print(f'\n🏆 Top clientes por saldo:')
        for i, cliente in enumerate(top_clientes, 1):
            print(f'   {i}. {cliente["nome_completo"]}: {cliente["saldo_atual"]} pts ({cliente["num_transacoes"]} transações)')
        
        # 5. Qualidade dos dados
        print('\n🔍 5. QUALIDADE DOS DADOS')
        print('-' * 50)
        
        # Verificar integridade básica
        problemas = []
        
        # Clientes sem conta de pontos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            WHERE up.id IS NULL
        """)
        sem_pontos = cursor.fetchone()["total"]
        if sem_pontos > 0:
            problemas.append(f'{sem_pontos} clientes sem conta de pontos')
        
        # Transações sem usuário_pontos válido
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM transacoes_pontos tp
            LEFT JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            WHERE up.id IS NULL
        """)
        transacoes_orfas = cursor.fetchone()["total"]
        if transacoes_orfas > 0:
            problemas.append(f'{transacoes_orfas} transações órfãs')
        
        # Saldos negativos
        cursor.execute("SELECT COUNT(*) as total FROM usuarios_pontos WHERE saldo_atual < 0")
        saldos_negativos = cursor.fetchone()["total"]
        if saldos_negativos > 0:
            problemas.append(f'{saldos_negativos} contas com saldo negativo')
        
        if problemas:
            print('⚠️  Problemas encontrados:')
            for problema in problemas:
                print(f'   • {probleblema}')
        else:
            print('✅ Nenhum problema de integridade encontrado')
        
        # 6. Resumo executivo
        print('\n📋 6. RESUMO EXECUTIVO')
        print('-' * 50)
        
        print(f'🏨 Hotel Cabo Frio - Sistema de Gestão')
        print(f'🗓️  Data do relatório: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        print(f'💾 Banco: PostgreSQL (hotel_cabo_frio)')
        print(f'📊 Tabelas principais: 5 (usuários, clientes, pontos, transações, prêmios)')
        print(f'👥 Usuários ativos: {total_usuarios}')
        print(f'🧑 Clientes cadastrados: {total_clientes}')
        print(f'💰 Sistema de pontos: {total_contas_pontos} contas, {pontos_em_circulacao} pontos em circulação')
        print(f'📋 Transações processadas: {total_transacoes}')
        print(f'🏆 Prêmios disponíveis: {len(premios)}')
        
        # Status do sistema
        if len(problemas) == 0:
            status = "🟢 OPERACIONAL"
        elif len(problemas) <= 2:
            status = "🟡 ATENÇÃO"
        else:
            status = "🔴 PROBLEMAS"
        
        print(f'🎯 Status do sistema: {status}')
        
        print('\n✅ Relatório concluído com sucesso!')
        
    except Exception as e:
        print(f'\n❌ Erro ao gerar relatório: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    gerar_relatorio_simplificado()
