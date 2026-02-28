#!/usr/bin/env python3
"""
Script simples para obter URL do ngrok
"""

import requests
import json
import time

def get_ngrok_url():
    """Obtém URL do ngrok"""
    
    try:
        # Tentar obter tunnels
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('tunnels') and len(data['tunnels']) > 0:
                tunnel = data['tunnels'][0]
                public_url = tunnel.get('public_url')
                
                if public_url:
                    return public_url
            else:
                return None
        else:
            return None
            
    except Exception as e:
        print(f'Erro: {str(e)}')
        return None

def main():
    """Função principal"""
    
    print('🔍 Procurando URL do Ngrok...')
    
    # Tentar várias vezes
    for i in range(10):
        url = get_ngrok_url()
        
        if url:
            print(f'\n🎉 NGROK ENCONTRADO!')
            print(f'🌐 URL: {url}')
            print(f'📚 Docs: {url}/docs')
            print(f'🔧 Dashboard: http://localhost:4040')
            
            # Salvar URL
            with open('/tmp/ngrok_url.txt', 'w') as f:
                f.write(url)
            
            print(f'\n✅ URL salva em /tmp/ngrok_url.txt')
            return url
        else:
            print(f'Tentativa {i+1}/10 - Aguardando ngrok...')
            time.sleep(2)
    
    print('\n❌ Ngrok não encontrado após 10 tentativas')
    print('Verifique se o ngrok está rodando corretamente')
    return None

if __name__ == "__main__":
    main()
