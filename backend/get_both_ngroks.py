#!/usr/bin/env python3
"""
Script para obter URLs de ambos os ngroks (backend e frontend)
"""

import requests
import json
import time

def get_ngrok_url(port):
    """Obtém URL do ngrok na porta especificada"""
    
    try:
        response = requests.get(f'http://localhost:{port}/api/tunnels', timeout=5)
        
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
        return None

def main():
    """Função principal"""
    
    print('🔍 Procurando URLs dos Ngroks...')
    print('=' * 50)
    
    # Tentar obter URLs
    backend_url = None
    frontend_url = None
    
    for i in range(15):
        backend_url = get_ngrok_url(4040)
        frontend_url = get_ngrok_url(4041)
        
        if backend_url or frontend_url:
            break
        
        print(f'Tentativa {i+1}/15 - Aguardando ngroks...')
        time.sleep(2)
    
    print('\n🎉 URLs ENCONTRADAS!')
    print('=' * 50)
    
    if backend_url:
        print(f'🔧 Backend: {backend_url}')
        print(f'📚 API Docs: {backend_url}/docs')
        print(f'🔍 Dashboard: http://localhost:4040')
        
        print(f'\n📋 ENDPOINTS BACKEND:')
        print(f'   📊 {backend_url}/docs - Documentação Swagger')
        print(f'   🔍 {backend_url}/redoc - Documentação ReDoc')
        print(f'   ❤️  {backend_url}/health - Health Check')
        print(f'   👤 {backend_url}/api/v1/auth/login - Login')
        print(f'   🏨 {backend_url}/api/v1/quartos - Quartos')
        print(f'   💰 {backend_url}/api/v1/pontos - Pontos RP')
        print(f'   📋 {backend_url}/api/v1/reservas - Reservas')
        print(f'   💳 {backend_url}/api/v1/pagamentos - Pagamentos')
        print(f'   🏆 {backend_url}/api/v1/public/status - Status API Pública')
        
        # Salvar URL do backend
        with open('/tmp/backend_url.txt', 'w') as f:
            f.write(backend_url)
    
    if frontend_url:
        print(f'\n🎨 Frontend: {frontend_url}')
        print(f'🔧 Dashboard: http://localhost:4041')
        
        # Salvar URL do frontend
        with open('/tmp/frontend_url.txt', 'w') as f:
            f.write(frontend_url)
    
    if backend_url and frontend_url:
        print(f'\n✨ SISTEMA COMPLETO ACESSÍVEL! ✨')
        print(f'🎯 Backend: {backend_url}')
        print(f'🎯 Frontend: {frontend_url}')
        
        print(f'\n📋 INSTRUÇÕES:')
        print(f'1. Frontend: Acesse {frontend_url}')
        print(f'2. Backend API: Acesse {backend_url}/docs')
        print(f'3. Teste integração frontend-backend')
        
        print(f'\n🔗 MANUTENÇÃO:')
        print(f'- Backend ngrok: porta 4040')
        print(f'- Frontend ngrok: porta 4041')
        print(f'- Mantenha containers rodando')
        
    elif backend_url:
        print(f'\n✅ Backend disponível: {backend_url}')
        print(f'❌ Frontend não encontrado')
        
    elif frontend_url:
        print(f'\n✅ Frontend disponível: {frontend_url}')
        print(f'❌ Backend não encontrado')
        
    else:
        print('\n❌ Nenhum ngrok encontrado após 15 tentativas')
        print('Verifique se os containers estão rodando corretamente')

if __name__ == "__main__":
    main()
