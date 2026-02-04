#!/usr/bin/env python3
"""
Tunnel HTTP para frontend
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

class FrontendHandler(BaseHTTPRequestHandler):
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
            target_url = f"http://frontend:3000{path}"
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
            
            # Make request to frontend
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
            print(f"Error handling frontend request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_frontend_tunnel(port=8083):
    """Inicia servidor de tunnel para frontend"""
    
    try:
        server = HTTPServer(('0.0.0.0', port), FrontendHandler)
        
        print(f'🎨 Servidor de Tunnel Frontend iniciado na porta {port}')
        print(f'🌐 URL de acesso: http://localhost:{port}')
        print(f'📚 Frontend: http://frontend:3000')
        
        print(f'\n✨ Frontend pronto para testes!')
        
        # Start server
        server.serve_forever()
        
    except Exception as e:
        print(f'❌ Erro ao iniciar servidor frontend: {str(e)}')

def main():
    """Função principal"""
    
    print('🎨 SERVIDOR DE TUNNEL FRONTEND - HOTEL CABO FRIO')
    print('=' * 60)
    
    print('🔧 Iniciando servidor de tunnel para frontend...')
    
    # Iniciar servidor de tunnel
    start_frontend_tunnel()

if __name__ == "__main__":
    main()
