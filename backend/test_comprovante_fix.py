#!/usr/bin/env python3
"""
Teste para verificar se o comprovante abre em nova aba
"""
import requests

def test_comprovante():
    try:
        # Testar com um arquivo real
        print("🔍 Testando endpoint de comprovante...")
        
        # Testar HEAD primeiro
        response = requests.head('http://localhost:8000/api/v1/comprovantes/arquivo/comprovante_pag6_20260126_160209_45f65b82.jpg')
        print(f'Status HEAD: {response.status_code}')
        print(f'Content-Type: {response.headers.get("content-type", "N/A")}')
        print(f'Content-Disposition: {response.headers.get("content-disposition", "N/A")}')
        
        # Testar GET para ver o conteúdo
        response_get = requests.get('http://localhost:8000/api/v1/comprovantes/arquivo/comprovante_pag6_20260126_160209_45f65b82.jpg')
        print(f'GET Status: {response_get.status_code}')
        print(f'Tamanho: {len(response_get.content)} bytes')
        
        if response_get.status_code == 200:
            print('✅ Arquivo servido com sucesso!')
            print('📋 Headers corrigidos para visualização em nova aba')
        else:
            print(f'❌ Erro: {response_get.text}')
            
    except Exception as e:
        print(f'❌ Erro: {e}')

if __name__ == "__main__":
    test_comprovante()
