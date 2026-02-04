#!/usr/bin/env python3
"""
Correção da função de cálculo RP para Suíte Dupla
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def corrigir_funcao_rp():
    """Corrige a função de cálculo para Suíte Dupla"""
    
    print('🔧 Corrigindo Função de Cálculo RP')
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
        
        # Corrigir a função - Suíte Dupla deve ser 4 RP (1200-1400)
        cursor.execute("""
            DROP FUNCTION IF EXISTS calcular_pontos_rp;
            
            CREATE OR REPLACE FUNCTION calcular_pontos_rp(
                p_valor_total NUMERIC,
                p_num_diarias INTEGER
            ) RETURNS INTEGER AS $$
            DECLARE
                v_pontos_por_duas_diarias INTEGER;
                v_pontos_totais INTEGER;
                v_pares_diarias INTEGER;
            BEGIN
                -- Regra: a cada duas diárias
                IF p_num_diarias < 2 THEN
                    RETURN 0;
                END IF;
                
                -- Calcular número de pares de diárias
                v_pares_diarias := p_num_diarias / 2;
                
                -- Calcular pontos baseado no valor total por 2 diárias
                -- Suíte Luxo: R$ 600-700 = 3 RP
                -- Suíte Dupla: R$ 1200-1400 = 4 RP (CORREÇÃO!)
                -- Suíte Master: R$ 800-900 = 4 RP
                -- Suíte Real: R$ 1000-1200 = 5 RP
                
                IF p_valor_total >= 1200 AND p_valor_total <= 1400 THEN
                    v_pontos_por_duas_diarias := 4; -- Dupla (faixa específica)
                ELSIF p_valor_total >= 1000 THEN
                    v_pontos_por_duas_diarias := 5; -- Real
                ELSIF p_valor_total >= 800 THEN
                    v_pontos_por_duas_diarias := 4; -- Master
                ELSIF p_valor_total >= 600 THEN
                    v_pontos_por_duas_diarias := 3; -- Luxo
                ELSE
                    v_pontos_por_duas_diarias := 0;
                END IF;
                
                -- Calcular pontos totais
                v_pontos_totais := v_pares_diarias * v_pontos_por_duas_diarias;
                
                RETURN v_pontos_totais;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        print('✅ Função corrigida - Suíte Dupla agora tem faixa específica')
        
        # Testar novamente
        print('\n🧪 Testando Função Corrigida...')
        
        testes = [
            (650, 2, 3, 'Suíte Luxo: 2 diárias'),
            (1300, 2, 4, 'Suíte Dupla: 2 diárias'),
            (850, 2, 4, 'Suíte Master: 2 diárias'),
            (1100, 2, 5, 'Suíte Real: 2 diárias'),
            (650, 4, 6, 'Suíte Luxo: 4 diárias'),
            (1300, 4, 8, 'Suíte Dupla: 4 diárias'),
            (850, 4, 8, 'Suíte Master: 4 diárias'),
            (1100, 4, 10, 'Suíte Real: 4 diárias'),
        ]
        
        for valor, diarias, esperado, descricao in testes:
            cursor.execute("SELECT calcular_pontos_rp(%s, %s)", (valor, diarias))
            resultado = cursor.fetchone()["calcular_pontos_rp"]
            
            status = "✅" if resultado == esperado else "❌"
            print(f'   {status} {descricao}')
            print(f'      R$ {valor} ({diarias} diárias) = {resultado} RP (esperado: {esperado})')
        
        conn.commit()
        print('\n✅ Função RP corrigida com sucesso!')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        if 'conn' in locals():
            conn.rollback()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    corrigir_funcao_rp()
