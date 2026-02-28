#!/usr/bin/env python3
"""
Adiciona a coluna rp_points na tabela usuarios_pontos
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def adicionar_coluna_rp_points():
    """Adiciona a coluna rp_points se não existir"""
    
    print('🔧 Adicionando Coluna RP Points')
    print('=' * 40)
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        # Verificar se a coluna existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuarios_pontos' 
            AND column_name = 'rp_points'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE usuarios_pontos 
                ADD COLUMN rp_points INTEGER DEFAULT 0
            """)
            print('✅ Coluna rp_points adicionada com sucesso!')
        else:
            print('✅ Coluna rp_points já existe')
        
        conn.commit()
        
    except Exception as e:
        print(f'❌ Erro: {str(e)}')
        if 'conn' in locals():
            conn.rollback()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    adicionar_coluna_rp_points()
