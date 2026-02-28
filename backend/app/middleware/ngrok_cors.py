"""
Middleware para suporte dinâmico de CORS com ngrok
Permite automaticamente origens ngrok.io e ngrok-free.app
"""
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
import re


class DynamicCORSMiddleware:
    """
    Middleware que permite CORS dinâmico para domínios ngrok
    """
    
    def __init__(self, app: ASGIApp, base_origins: list = None):
        self.app = app
        self.base_origins = base_origins or []
        
        # Padrões de domínios permitidos para desenvolvimento
        self.allowed_patterns = [
            r"https://.*\.ngrok\.io",
            r"https://.*\.ngrok-free\.app", 
            r"https://.*\.ngrok-free\.dev",
            r"https://.*\.loca\.lt",
            r"https://.*\.tunnel\.dev",
            r"http://localhost:\d+",
            r"http://127\.0\.0\.1:\d+"
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        origin = request.headers.get("origin")
        
        # Verificar se é uma origem permitida
        allowed = self._is_origin_allowed(origin)
        
        if allowed and origin:
            # Adicionar headers CORS
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    headers[b"access-control-allow-origin"] = origin.encode()
                    headers[b"access-control-allow-credentials"] = b"true"
                    headers[b"access-control-allow-methods"] = b"GET,POST,PUT,PATCH,DELETE,OPTIONS"
                    headers[b"access-control-allow-headers"] = b"Content-Type,Authorization,Accept,Origin,User-Agent,DNT,Cache-Control,X-Requested-With,ngrok-skip-browser-warning,Cookie"
                    headers[b"access-control-expose-headers"] = b"Set-Cookie"
                    headers[b"access-control-max-age"] = b"3600"
                    
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Verifica se a origem é permitida
        """
        if not origin:
            return False
            
        # Verificar origens base
        if origin in self.base_origins:
            return True
            
        # Verificar padrões regex
        for pattern in self.allowed_patterns:
            if re.match(pattern, origin):
                return True
                
        return False
