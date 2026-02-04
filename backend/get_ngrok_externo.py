#!/usr/bin/env python3
"""
Script para obter URL do ngrok externo
"""

import requests
import json
import time

def get_ngrok_url():
    """Obtém URL do ngrok externo"""
    
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
    
    print('🔍 Procurando URL do Ngrok Externo...')
    
    # Tentar várias vezes
    for i in range(15):
        url = get_ngrok_url()
        
        if url:
            print(f'\n🎉 NGROK EXTERNO ENCONTRADO!')
            print(f'🌐 URL EXTERNA: {url}')
            print(f'📚 Docs: {url}/docs')
            print(f'🔧 Dashboard: http://localhost:4040')
            print(f'🏨 Hotel Cabo Frio: {url}/docs')
            
            # Salvar URL
            with open('/tmp/ngrok_url.txt', 'w') as f:
                f.write(url)
            
            print(f'\n✅ URL salva em /tmp/ngrok_url.txt')
            print(f'\n📋 ENDPOINTS DISPONÍVEIS:')
            print(f'   📊 {url}/docs - Documentação Swagger')
            print(f'   🔍 {url}/redoc - Documentação ReDoc')
            print(f'   ❤️  {url}/health - Health Check')
            print(f'   👤 {url}/api/v1/auth/login - Login')
            print(f'   🏨 {url}/api/v1/quartos - Quartos')
            print(f'   💰 {url}/api/v1/pontos - Pontos RP')
            print(f'   📋 {url}/api/v1/reservas - Reservas')
            print(f'   💳 {url}/api/v1/pagamentos - Pagamentos')
            print(f'   🏆 {url}/api/v1/public/status - Status API Pública')
            
            print(f'\n✨ SISTEMA ACESSÍVEL EXTERNAMENTE! ✨')
            print(f'🎯 Compartilhe este link: {url}')
            
            return url
        else:
            print(f'Tentativa {i+1}/15 - Aguardando ngrok...')
            time.sleep(2)
    
    print('\n❌ Ngrok não encontrado após 15 tentativas')
    print('Verifique se o ngrok está rodando corretamente')
    return None

if __name__ == "__main__":
    main()
