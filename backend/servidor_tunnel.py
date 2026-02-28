#!/usr/bin/env python3
"""
Servidor de túnel simples para expor o backend para internet
"""

import sys
import os
sys.path.append('/app')

import socket
import threading
import time
import json

def handle_client(client_socket, backend_host='localhost', backend_port=8000):
    """Handle client connection and forward to backend"""
    try:
        print(f"🔗 Conexão recebida de {client_socket.getpeername()}")
        
        # Conectar ao backend
        backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend_socket.connect((backend_host, backend_port))
        
        print(f"✅ Conectado ao backend em {backend_host}:{backend_port}")
        
        # Forward data entre cliente e backend
        while True:
            # Receber dados do cliente
            client_data = client_socket.recv(4096)
            if not client_data:
                break
                
            print(f"📨 Recebido {len(client_data)} bytes do cliente")
            
            # Enviar para backend
            backend_socket.send(client_data)
            
            # Receber resposta do backend
            try:
                backend_data = backend_socket.recv(4096)
                if backend_data:
                    print(f'📤 Enviados {len(backend_data)} bytes para cliente')
                    client_socket.send(backend_data)
            except:
                break
                
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
    finally:
        client_socket.close()
        backend_socket.close()

def start_tunnel_server(port=8081):
    """Inicia servidor de túnel"""
    
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        
        print(f'🚀 Servidor de túnel iniciado na porta {port}')
        print(f'🌐 URL de acesso: http://localhost:{port}')
        print(f'📚 Backend: http://localhost:8000')
        print(f'📚 API Docs: http://localhost:{port}/docs')
        print(f'🔧 Dashboard: http://localhost:{port}/status')
        print(f'\n📋 ENDPOINTS DISPONÍVEIS:')
        print(f'   📊 {port}/docs - Documentação Swagger')
        print(f'   🔍 {port}/redoc - Documentação ReDoc')
        print(f'   ❤️  {port}/health - Health Check')
        print(f'   👤 {port}/api/v1/auth/login - Login')
        print(f'   🏨 {port}/api/v1/quartos - Quartos')
        print(f'   💰 {port}/api/v1/pontos - Pontos RP')
        print(f'   📋 {port}/api/v1/reservas - Reservas')
        print(f'   💳 {port}/api/v1/pagamentos - Pagamentos')
        print(f'   🏆 {port}/api/v1/public/status - Status API Pública')
        print('\n✨ Sistema pronto para testes!')
        print('⏳ Mantenha esta janela aberta para manter o túnel ativo')
        
        # Aceitar conexões
        while True:
            try:
                client_socket, addr = server_socket.accept()
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except KeyboardInterrupt:
                print('\n👋 Parando servidor de túnel...')
                break
            except Exception as e:
                print(f'❌ Erro no servidor: {str(e)}')
                break
                
    except Exception as e:
        print(f'❌ Erro ao iniciar servidor: {str(e)}')
    finally:
        server_socket.close()

def main():
    """Função principal"""
    
    print('🚀 SERVIDOR DE TÚNEL - HOTEL CABO FRIO')
    print('=' * 60)
    
    print('🔧 Iniciando servidor de túnel...')
    
    # Iniciar servidor de túnel
    start_tunnel_server()
    
    print('\n🎉 TÚNEL CONFIGURADO COM SUCESSO!')
    print('=' * 60)
    print('🌐 URL de Acesso: http://localhost:8081')
    print('📚 Backend: http://localhost:8000')
    print('📚 API Docs: http://localhost:8081/docs')
    print('🔍 Dashboard: http://localhost:8081/status')
    print('\n📋 TESTE OS ENDPOINTS:')
    print(f'   📊 http://localhost:8081/docs - Documentação Swagger')
    print(f'   🔍 http://localhost:8081/redoc - Documentação ReDoc')
    print(f'   ❤️  http://localhost:8081/health - Health Check')
    print(f'   👤 http://localhost:8081/api/v1/auth/login - Login')
    print(f'   🏨 http://localhost:8081/api/v1/quartos - Quartos')
    print(f'   💰 http://localhost:8081/api/v1/pontos - Pontos RP')
    print(f'   📋 http://localhost:8081/api/v1/reservas - Reservas')
    print(f'   💳 http://localhost:8081/api/v1/pagamentos - Pagamentos')
    print(f'   🏆 http://localhost:8081/api/v1/public/status - Status API Pública')
    print('\n✨ Sistema pronto para testes! ✨')
    
    # Manter servidor rodando
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print('\n👋 Servidor de túnel parado')
        print('✅ Túnel desconectado')

if __name__ == "__main__":
    main()
