#!/usr/bin/env python3
"""
Verificar estrutura da tabela usuarios_pontos
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def verificar_estrutura_pontos():
    """Verifica a estrutura da tabela usuarios_pontos"""
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'usuarios_pontos' 
            ORDER BY ordinal_position
        """)
        
        print('📋 Estrutura da tabela usuarios_pontos:')
        for row in cursor.fetchall():
            nullable = "NULL" if row["is_nullable"] == "YES" else "NOT NULL"
            default = f" DEFAULT {row['column_default']}" if row["column_default"] else ""
            print(f'   {row["column_name"]}: {row["data_type"]} {nullable}{default}')
        
    except Exception as e:
        print(f'❌ Erro: {str(e)}')
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verificar_estrutura_pontos()
