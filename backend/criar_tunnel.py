#!/usr/bin/env python3
"""
Script para criar tunnel usando localtunnel como alternativa ao ngrok
"""

import subprocess
import time
import requests
import json
import sys
import os

def instalar_localtunnel():
    """Instala localtunnel se não estiver disponível"""
    
    print('🔧 Verificando localtunnel...')
    
    try:
        # Verificar se npm está disponível
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        print(f'✅ npm encontrado: {result.stdout.strip()}')
        
        # Instalar localtunnel globalmente
        print('📦 Instalando localtunnel...')
        result = subprocess.run(['npm', 'install', '-g', 'localtunnel'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print('✅ localtunnel instalado com sucesso')
            return True
        else:
            print(f'❌ Erro ao instalar localtunnel: {result.stderr}')
            return False
            
    except FileNotFoundError:
        print('❌ npm não encontrado')
        return False

def iniciar_localtunnel():
    """Inicia tunnel localtunnel"""
    
    print('🚀 Iniciando localtunnel...')
    
    try:
        # Iniciar localtunnel em background
        process = subprocess.Popen([
            'localtunnel',
            '--port', '8000',
            '--subdomain', f'hotel-cabo-frio-{int(time.time())}'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguardar um pouco
        time.sleep(5)
        
        # Tentar obter a URL
        # localtunnel geralmente mostra a URL no stdout
        try:
            stdout, stderr = process.communicate(timeout=2)
            
            # Procurar por URL na saída
            output = stdout + stderr
            for line in output.split('\n'):
                if 'https://' in line:
                    url = line.strip()
                    print(f'✅ localtunnel iniciado: {url}')
                    return url
                    
        except subprocess.TimeoutExpired:
            pass
        
        # Se não conseguir pegar a URL, tentar padrão
        print('⚠️  Não foi possível obter URL automaticamente')
        print('Verifique o console do localtunnel para a URL')
        
        return None
        
    except Exception as e:
        print(f'❌ Erro ao iniciar localtunnel: {str(e)}')
        return None

def verificar_backend():
    """Verifica se o backend está rodando"""
    
    print('🔍 Verificando backend...')
    
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

def criar_tunnel_simples():
    """Cria um túnel simples usando Python"""
    
    print('🔧 Criando túnel simples...')
    
    try:
        import socket
        import threading
        
        def handle_client(client_socket):
            """Handle client connection"""
            try:
                # Forward request to backend
                backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                backend_socket.connect(('localhost', 8000))
                
                # Simple forwarding
                while True:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    backend_socket.send(data)
                    
                    response = backend_socket.recv(4096)
                    if not response:
                        break
                    client_socket.send(response)
                    
            except Exception as e:
                print(f'Error in tunnel: {e}')
            finally:
                client_socket.close()
                backend_socket.close()
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to port 8081
        server_socket.bind(('0.0.0.0', 8081))
        server_socket.listen(5)
        
        print('✅ Túnel simples criado na porta 8081')
        print('🌐 Acesse: http://localhost:8081')
        print('📚 Docs: http://localhost:8081/docs')
        
        # Start server in background
        def run_server():
            while True:
                client_socket, addr = server_socket.accept()
                client_thread = threading.Thread(target=handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        return 'http://localhost:8081'
        
    except Exception as e:
        print(f'❌ Erro ao criar túnel simples: {str(e)}')
        return None

def main():
    """Função principal"""
    
    print('🚀 CONFIGURAÇÃO DE TUNNEL - HOTEL CABO FRIO')
    print('=' * 50)
    
    # 1. Verificar backend
    if not verificar_backend():
        print('\n❌ Backend não está rodando!')
        print('Por favor, inicie o backend primeiro:')
        print('docker-compose up backend')
        return
    
    # 2. Tentar localtunnel
    print('\n📦 Tentando localtunnel...')
    
    if instalar_localtunnel():
        url = iniciar_localtunnel()
        if url:
            print(f'\n🎉 LOCALTUNNEL CONFIGURADO!')
            print(f'🌐 URL: {url}')
            print(f'📚 Docs: {url}/docs')
            return
    
    # 3. Se localtunnel falhar, criar túnel simples
    print('\n🔧 Criando túnel simples como alternativa...')
    
    url = criar_tunnel_simples()
    if url:
        print(f'\n🎉 TÚNEL SIMPLES CONFIGURADO!')
        print(f'🌐 URL: {url}')
        print(f'📚 Docs: {url}/docs')
        print(f'\n📋 ENDPOINTS DISPONÍVEIS:')
        print(f'   📊 {url}/docs - Documentação Swagger')
        print(f'   🔍 {url}/redoc - Documentação ReDoc')
        print(f'   ❤️  {url}/health - Health Check')
        print(f'   👤 {url}/api/v1/auth/login - Login')
        print(f'   🏨 {url}/api/v1/quartos - Quartos')
        print(f'   💰 {url}/api/v1/pontos - Pontos RP')
        
        print('\n✨ Sistema pronto para testes! ✨')
        print('🔗 O túnel está rodando em background')
        print('⏳ Mantenha esta janela aberta para manter o túnel ativo')
        
        # Manter rodando
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print('\n👋 Parando túnel...')
            print('✅ Túnel parado')
    else:
        print('\n❌ Não foi possível configurar nenhum túnel')
        print('Verifique os logs acima para mais detalhes')

if __name__ == "__main__":
    main()
