#!/usr/bin/env python3
"""
Script Python para criar tunnel ngrok usando a API do ngrok
"""

import sys
import os
sys.path.append('/app')

import requests
import json
import time
import subprocess

def instalar_ngrok_manual():
    """Instala ngrok manualmente"""
    
    print('🔧 Instalando Ngrok Manualmente')
    print('=' * 40)
    
    try:
        # 1. Baixar ngrok usando requests
        print('📥 Baixando ngrok...')
        
        # URL direta do ngrok
        ngrok_url = "https://bin.equinox.io/c/b4bFn9hHtbh/ngrok-stable-linux-amd64.zip"
        
        response = requests.get(ngrok_url, stream=True)
        response.raise_for_status()
        
        with open('/tmp/ngrok.zip', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print('✅ Ngrok baixado')
        
        # 2. Extrair
        print('📦 Extraindo ngrok...')
        
        import zipfile
        with zipfile.ZipFile('/tmp/ngrok.zip', 'r') as zip_ref:
            zip_ref.extractall('/tmp/')
        
        # 3. Mover para PATH
        subprocess.run(['mv', '/tmp/ngrok', '/usr/local/bin/'], check=True)
        subprocess.run(['chmod', '+x', '/usr/local/bin/ngrok'], check=True)
        
        # 4. Verificar
        result = subprocess.run(['/usr/local/bin/ngrok', 'version'], 
                              capture_output=True, text=True)
        
        print(f'✅ Ngrok instalado: {result.stdout.strip()}')
        return True
        
    except Exception as e:
        print(f'❌ Erro: {str(e)}')
        return False

def iniciar_ngrok_tunnel():
    """Inicia tunnel ngrok para o backend"""
    
    print('🚀 Iniciando Tunnel Ngrok')
    print('=' * 40)
    
    try:
        # Verificar se ngrok está instalado
        result = subprocess.run(['which', 'ngrok'], capture_output=True, text=True)
        
        if result.returncode != 0:
            print('❌ Ngrok não encontrado, tentando instalar...')
            if not instalar_ngrok_manual():
                return None
        
        # Iniciar ngrok em background
        print('🔧 Iniciando ngrok para porta 8000...')
        
        # Criar arquivo de configuração
        config_content = """
web_addr: localhost:4040
tunnels:
  backend:
    proto: http
    addr: 8000
    bind_tls: true
    inspect: false
"""
        
        with open('/tmp/ngrok.yml', 'w') as f:
            f.write(config_content)
        
        # Iniciar ngrok
        ngrok_process = subprocess.Popen([
            '/usr/local/bin/ngrok',
            'start',
            '--config=/tmp/ngrok.yml',
            'backend'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguardar ngrok iniciar
        time.sleep(3)
        
        # Obter URL do ngrok
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            response.raise_for_status()
            
            tunnels = response.json()['tunnels']
            
            if tunnels:
                public_url = tunnels[0]['public_url']
                print(f'✅ Ngrok iniciado com sucesso!')
                print(f'🌐 URL Pública: {public_url}')
                print(f'🔗 Dashboard: http://localhost:4040')
                
                # Salvar URL em arquivo para facilitar acesso
                with open('/tmp/ngrok_url.txt', 'w') as f:
                    f.write(public_url)
                
                return public_url
            else:
                print('❌ Nenhum tunnel encontrado')
                return None
                
        except Exception as e:
            print(f'❌ Erro ao obter URL: {str(e)}')
            return None
        
    except Exception as e:
        print(f'❌ Erro ao iniciar ngrok: {str(e)}')
        return None

def verificar_backend():
    """Verifica se o backend está rodando"""
    
    print('🔍 Verificando Backend')
    print('-' * 30)
    
    try:
        response = requests.get('http://localhost:8000/docs', timeout=5)
        if response.status_code == 200:
            print('✅ Backend está rodando na porta 8000')
            return True
        else:
            print(f'⚠️  Backend respondeu com status {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Backend não está respondendo: {str(e)}')
        return False

def main():
    """Função principal"""
    
    print('🚀 CONFIGURAÇÃO NGROK - HOTEL CABO FRIO')
    print('=' * 50)
    
    # 1. Verificar backend
    if not verificar_backend():
        print('\n❌ Backend não está rodando!')
        print('Por favor, inicie o backend primeiro:')
        print('docker-compose up backend')
        return
    
    # 2. Iniciar ngrok
    ngrok_url = iniciar_ngrok_tunnel()
    
    if ngrok_url:
        print('\n🎉 NGROK CONFIGURADO COM SUCESSO!')
        print('=' * 50)
        print(f'🌐 URL de Acesso: {ngrok_url}')
        print(f'📚 Documentação: {ngrok_url}/docs')
        print(f'🔧 Dashboard: http://localhost:4040')
        print('\n📋 ENDPOINTS DISPONÍVEIS:')
        print(f'   📊 {ngrok_url}/docs - Documentação Swagger')
        print(f'   🔍 {ngrok_url}/redoc - Documentação ReDoc')
        print(f'   ❤️  {ngrok_url}/health - Health Check')
        print(f'   👤 {ngrok_url}/auth/login - Login')
        print(f'   🏨 {ngrok_url}/api/v1/quartos - Quartos')
        print(f'   💰 {ngrok_url}/api/v1/pontos - Pontos RP')
        print('\n✨ Sistema pronto para testes! ✨')
        
        # Manter script rodando
        try:
            print('\n⏳ Mantendo ngrok ativo... (Ctrl+C para parar)')
            while True:
                time.sleep(10)
                # Verificar se ngrok ainda está ativo
                try:
                    response = requests.get('http://localhost:4040/api/tunnels')
                    if response.status_code != 200:
                        print('❌ Ngrok parou respondendo')
                        break
                except:
                    print('❌ Ngrok não está respondendo')
                    break
        except KeyboardInterrupt:
            print('\n👋 Parando ngrok...')
            subprocess.run(['pkill', 'ngrok'], ignore_errors=True)
            print('✅ Ngrok parado')
    else:
        print('\n❌ Falha ao configurar ngrok')
        print('Verifique os logs acima para mais detalhes')

if __name__ == "__main__":
    main()
