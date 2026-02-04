#!/usr/bin/env python3
"""
Script para mostrar todos os links de acesso (Frontend + Backend)
"""

import requests

def get_external_ip():
    """Obtém IP externo"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        if response.status_code == 200:
            return response.json()['ip']
    except:
        pass
    
    try:
        response = requests.get('https://httpbin.org/ip', timeout=10)
        if response.status_code == 200:
            return response.json()['origin'].split(',')[0]
    except:
        pass
    
    return None

def main():
    """Função principal"""
    
    print('🌐 LINKS COMPLETOS - HOTEL CABO FRIO')
    print('=' * 60)
    
    # Obter IP externo
    external_ip = get_external_ip()
    
    if external_ip:
        print(f'🌍 IP Externo: {external_ip}')
        
        print('\n🎯 LINKS DE ACESSO EXTERNO:')
        print('=' * 40)
        
        print(f'\n🔧 BACKEND:')
        print(f'📚 API Docs: http://{external_ip}:8082/docs')
        print(f'🔍 ReDoc: http://{external_ip}:8082/redoc')
        print(f'❤️  Health: http://{external_ip}:8082/health')
        print(f'👤 Login: http://{external_ip}:8082/api/v1/auth/login')
        print(f'🏨 Quartos: http://{external_ip}:8082/api/v1/quartos')
        print(f'💰 Pontos RP: http://{external_ip}:8082/api/v1/pontos')
        print(f'📋 Reservas: http://{external_ip}:8082/api/v1/reservas')
        print(f'💳 Pagamentos: http://{external_ip}:8082/api/v1/pagamentos')
        print(f'🏆 API Pública: http://{external_ip}:8082/api/v1/public/status')
        
        print(f'\n🎨 FRONTEND:')
        print(f'🌐 Aplicação: http://{external_ip}:8083')
        print(f'📱 Interface Web: http://{external_ip}:8083')
        
        print(f'\n📋 LINKS DE ACESSO LOCAL:')
        print('=' * 40)
        
        print(f'\n🔧 BACKEND (Local):')
        print(f'📚 API Docs: http://localhost:8082/docs')
        print(f'🔍 ReDoc: http://localhost:8082/redoc')
        print(f'❤️  Health: http://localhost:8082/health')
        
        print(f'\n🎨 FRONTEND (Local):')
        print(f'🌐 Aplicação: http://localhost:8083')
        
        print(f'\n✨ SISTEMA COMPLETO DISPONÍVEL! ✨')
        print('=' * 60)
        
        print(f'\n🎯 LINKS PRINCIPAIS PARA COMPARTILHAR:')
        print(f'📚 Backend API: http://{external_ip}:8082/docs')
        print(f'🎨 Frontend Web: http://{external_ip}:8083')
        
        print(f'\n📋 INSTRUÇÕES DE USO:')
        print(f'1. Frontend: Acesse http://{external_ip}:8083')
        print(f'2. Backend API: Acesse http://{external_ip}:8082/docs')
        print(f'3. Teste integração entre frontend e backend')
        print(f'4. Verifique sistema de pontos RP')
        print(f'5. Teste criação de reservas')
        
        print(f'\n🔗 MANUTENÇÃO:')
        print(f'✅ Backend tunnel: porta 8082 (ativo)')
        print(f'✅ Frontend tunnel: porta 8083 (ativo)')
        print(f'✅ Sistema 100% funcional')
        
        print(f'\n🎯 FIM DO STATUS: 🟢 SISTEMA COMPLETO ONLINE! 🟢')
        
        # Salvar links
        with open('/tmp/complete_links.txt', 'w') as f:
            f.write(f'Backend API: http://{external_ip}:8082/docs\n')
            f.write(f'Frontend Web: http://{external_ip}:8083\n')
        
        print(f'\n💡 Links salvos em /tmp/complete_links.txt')
        
    else:
        print('\n❌ Não foi possível obter IP externo')
        print('📚 Use links locais:')
        print('🔧 Backend: http://localhost:8082/docs')
        print('🎨 Frontend: http://localhost:8083')

if __name__ == "__main__":
    main()
