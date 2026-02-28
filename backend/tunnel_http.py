#!/usr/bin/env python3
"""
Tunnel HTTP simples para expor backend externamente
"""

import sys
import os
sys.path.append('/app')

import socket
import threading
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import urllib.request

class TunnelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
    
    def do_PUT(self):
        self.handle_request('PUT')
    
    def do_DELETE(self):
        self.handle_request('DELETE')
    
    def do_PATCH(self):
        self.handle_request('PATCH')
    
    def do_OPTIONS(self):
        self.handle_request('OPTIONS')
    
    def handle_request(self, method):
        try:
            # Parse URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query = parsed_url.query
            
            # Build target URL
            target_url = f"http://localhost:8000{path}"
            if query:
                target_url += f"?{query}"
            
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Prepare headers
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'content-length']:
                    headers[key] = value
            
            # Make request to backend
            if method == 'GET':
                response = requests.get(target_url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(target_url, data=body, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(target_url, data=body, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(target_url, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(target_url, data=body, headers=headers, timeout=30)
            elif method == 'OPTIONS':
                response = requests.options(target_url, headers=headers, timeout=30)
            else:
                self.send_error(405, f"Method {method} not allowed")
                return
            
            # Send response
            self.send_response(response.status_code)
            
            # Send headers
            for key, value in response.headers.items():
                if key.lower() not in ['server', 'date', 'connection']:
                    self.send_header(key, value)
            
            # Add CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            
            self.end_headers()
            
            # Send body
            if response.content:
                self.wfile.write(response.content)
                
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_tunnel_server(port=8082):
    """Inicia servidor de tunnel"""
    
    try:
        server = HTTPServer(('0.0.0.0', port), TunnelHandler)
        
        print(f'🚀 Servidor de Tunnel HTTP iniciado na porta {port}')
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
        
        # Start server
        server.serve_forever()
        
    except Exception as e:
        print(f'❌ Erro ao iniciar servidor: {str(e)}')

def main():
    """Função principal"""
    
    print('🚀 SERVIDOR DE TUNNEL HTTP - HOTEL CABO FRIO')
    print('=' * 60)
    
    print('🔧 Iniciando servidor de tunnel HTTP...')
    
    # Iniciar servidor de tunnel
    start_tunnel_server()
    
    print('\n🎉 TÚNEL HTTP CONFIGURADO COM SUCESSO!')
    print('=' * 60)
    print('🌐 URL de Acesso: http://localhost:8082')
    print('📚 Backend: http://localhost:8000')
    print('📚 API Docs: http://localhost:8082/docs')
    print('🔍 Dashboard: http://localhost:8082/status')
    print('\n📋 TESTE OS ENDPOINTS:')
    print(f'   📊 http://localhost:8082/docs - Documentação Swagger')
    print(f'   🔍 http://localhost:8082/redoc - Documentação ReDoc')
    print(f'   ❤️  http://localhost:8082/health - Health Check')
    print(f'   👤 http://localhost:8082/api/v1/auth/login - Login')
    print(f'   🏨 http://localhost:8082/api/v1/quartos - Quartos')
    print(f'   💰 http://localhost:8082/api/v1/pontos - Pontos RP')
    print(f'   📋 http://localhost:8082/api/v1/reservas - Reservas')
    print(f'   💳 http://localhost:8082/api/v1/pagamentos - Pagamentos')
    print(f'   🏆 http://localhost:8082/api/v1/public/status - Status API Pública')
    print('\n✨ Sistema pronto para testes! ✨')

if __name__ == "__main__":
    main()
