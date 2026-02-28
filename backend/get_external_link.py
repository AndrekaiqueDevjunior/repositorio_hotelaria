#!/usr/bin/env python3
"""
Script para obter IP externo e criar link de acesso
"""

import requests
import socket

def get_local_ip():
    """Obtém IP local"""
    try:
        # Conectar a um servidor externo para obter IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

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
    
    print('🌐 OBTENDO LINK DE ACESSO EXTERNO')
    print('=' * 50)
    
    # Obter IPs
    local_ip = get_local_ip()
    external_ip = get_external_ip()
    
    print(f'🏠 IP Local: {local_ip}')
    
    if external_ip:
        print(f'🌍 IP Externo: {external_ip}')
        
        print('\n🎯 LINKS DE ACESSO:')
        print(f'📚 Local: http://{local_ip}:8082/docs')
        print(f'🌐 Externo: http://{external_ip}:8082/docs')
        
        print(f'\n📋 ENDPOINTS EXTERNOS:')
        print(f'   📊 http://{external_ip}:8082/docs - Documentação Swagger')
        print(f'   🔍 http://{external_ip}:8082/redoc - Documentação ReDoc')
        print(f'   ❤️  http://{external_ip}:8082/health - Health Check')
        print(f'   👤 http://{external_ip}:8082/api/v1/auth/login - Login')
        print(f'   🏨 http://{external_ip}:8082/api/v1/quartos - Quartos')
        print(f'   💰 http://{external_ip}:8082/api/v1/pontos - Pontos RP')
        print(f'   📋 http://{external_ip}:8082/api/v1/reservas - Reservas')
        print(f'   💳 http://{external_ip}:8082/api/v1/pagamentos - Pagamentos')
        print(f'   🏆 http://{external_ip}:8082/api/v1/public/status - Status API Pública')
        
        print(f'\n✨ LINK EXTERNO PRONTO! ✨')
        print(f'🎯 Compartilhe: http://{external_ip}:8082/docs')
        
        # Salvar links
        with open('/tmp/access_links.txt', 'w') as f:
            f.write(f'Local: http://{local_ip}:8082/docs\n')
            f.write(f'Externo: http://{external_ip}:8082/docs\n')
        
        print(f'\n💡 Links salvos em /tmp/access_links.txt')
        
    else:
        print('\n❌ Não foi possível obter IP externo')
        print(f'📚 Use link local: http://{local_ip}:8082/docs')
        
        print('\n🔧 Para acesso externo:')
        print('1. Configure port forwarding no seu roteador')
        print('2. Ou use um serviço como ngrok/localtunnel')
    
    print('\n📋 INSTRUÇÕES:')
    print('1. Acesse o link acima')
    print('2. Teste os endpoints via Swagger UI')
    print('3. Verifique API Pública')
    print('4. Teste sistema de pontos')
    print('5. Teste criação de reservas')
    
    print('\n🔗 MANUTENÇÃO:')
    print('- O túnel HTTP está rodando na porta 8082')
    print('- Backend está rodando na porta 8000')
    print('- Mantenha as janelas abertas')

if __name__ == "__main__":
    main()
