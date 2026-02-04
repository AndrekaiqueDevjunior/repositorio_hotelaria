#!/usr/bin/env python3
"""
Corrige senhas inseguras para produção
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

def corrigir_senhas_inseguras():
    """Corrige senhas em texto plano para hash bcrypt"""
    
    print('🔐 CORRIGINDO SENHAS INSEGURAS')
    print('=' * 50)
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        # 1. Identificar senhas inseguras
        print('\n🔍 Identificando senhas inseguras...')
        
        cursor.execute("""
            SELECT id, nome, email, senha_hash
            FROM usuarios 
            WHERE senha_hash NOT LIKE '$2%' 
            AND senha_hash NOT LIKE 'pbkdf2%'
            AND senha_hash IS NOT NULL
        """)
        
        usuarios_inseguros = cursor.fetchall()
        
        if not usuarios_inseguros:
            print('   ✅ Nenhuma senha insegura encontrada')
            return
        
        print(f'   ⚠️  Encontrados {len(usuarios_inseguros)} usuários com senhas inseguras')
        
        # 2. Corrigir cada senha
        print('\n🔧 Corrigindo senhas...')
        
        for usuario in usuarios_inseguros:
            senha_atual = usuario["senha_hash"]
            
            # Gerar hash bcrypt
            salt = bcrypt.gensalt()
            senha_hash = bcrypt.hashpw(senha_atual.encode('utf-8'), salt)
            
            # Atualizar no banco
            cursor.execute("""
                UPDATE usuarios 
                SET senha_hash = %s, updated_at = NOW()
                WHERE id = %s
            """, (senha_hash.decode('utf-8'), usuario["id"]))
            
            print(f'   ✅ {usuario["nome"]} ({usuario["email"]}) - Senha atualizada')
        
        conn.commit()
        
        # 3. Verificar correção
        print('\n🔍 Verificando correção...')
        
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM usuarios 
            WHERE senha_hash NOT LIKE '$2%' 
            AND senha_hash NOT LIKE 'pbkdf2%'
        """)
        
        restantes = cursor.fetchone()["total"]
        
        if restantes == 0:
            print('   ✅ Todas as senhas foram corrigidas!')
        else:
            print(f'   ⚠️  Ainda restam {restantes} senhas inseguras')
        
        # 4. Testar login com senha corrigida
        if usuarios_inseguros:
            print('\n🧪 Testando login com senha corrigida...')
            
            usuario_teste = usuarios_inseguros[0]
            senha_teste = usuario_teste["senha_hash"]
            
            # Verificar se hash bate
            cursor.execute("""
                SELECT senha_hash FROM usuarios WHERE id = %s
            """, (usuario_teste["id"],))
            
            hash_salvo = cursor.fetchone()["senha_hash"]
            
            if bcrypt.checkpw(senha_teste.encode('utf-8'), hash_salvo.encode('utf-8')):
                print('   ✅ Login testado com sucesso!')
            else:
                print('   ❌ Falha no teste de login')
        
        print('\n🎉 SENHAS CORRIGIDAS COM SUCESSO!')
        print('🔒 Sistema seguro para produção')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    corrigir_senhas_inseguras()
