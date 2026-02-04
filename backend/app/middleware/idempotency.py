"""
Middleware de Idempotência
Garante que operações críticas não sejam duplicadas mesmo com retry/timeout
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import json
from app.core.cache import cache


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware que implementa idempotência usando Redis
    
    Funciona verificando o header Idempotency-Key:
    - Se key já existe no cache: retorna resposta cacheada
    - Se key não existe: processa normalmente e cacheia resultado
    
    TTL padrão: 24 horas
    """
    
    def __init__(self, app, ttl: int = 86400):
        super().__init__(app)
        self.ttl = ttl  # 24 horas padrão
        
        # Métodos que devem usar idempotência
        self.idempotent_methods = ["POST", "PUT", "PATCH"]
        
        # Rotas que DEVEM ter idempotency key
        self.required_routes = [
            "/api/v1/pagamentos",  # CRÍTICO: pagamentos
        ]
        
        # Rotas que PODEM ter idempotency key (opcional mas recomendado)
        self.optional_routes = [
            "/api/v1/reservas",
            "/api/v1/pontos/ajustar",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Processar requisição com verificação de idempotência"""
        
        # Verificar se método deve usar idempotência
        if request.method not in self.idempotent_methods:
            return await call_next(request)
        
        # Obter idempotency key do header
        idempotency_key = request.headers.get("Idempotency-Key")
        
        # Verificar se rota requer idempotency key
        path = request.url.path
        is_required = any(path.startswith(route) for route in self.required_routes)
        is_optional = any(path.startswith(route) for route in self.optional_routes)
        
        # Se rota requer mas não tem key, retornar erro
        if is_required and not idempotency_key:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Idempotency-Key é obrigatório para esta operação",
                    "error_code": "IDEMPOTENCY_KEY_REQUIRED"
                }
            )
        
        # Se não tem key, processar normalmente
        if not idempotency_key:
            return await call_next(request)
        
        # Verificar se já foi processado
        cached_response = await self._get_cached_response(idempotency_key)
        if cached_response:
            print(f"[IDEMPOTENCY] Cache hit: {idempotency_key}")
            return JSONResponse(
                status_code=cached_response["status_code"],
                content=cached_response["body"],
                headers=cached_response.get("headers", {})
            )
        
        # Processar requisição
        print(f"[IDEMPOTENCY] Cache miss: {idempotency_key}")
        response = await call_next(request)
        
        # Cachear apenas respostas de sucesso (2xx)
        if 200 <= response.status_code < 300:
            await self._cache_response(idempotency_key, response)
        
        return response
    
    async def _get_cached_response(self, key: str) -> Optional[dict]:
        """Buscar resposta cacheada"""
        try:
            cached = await cache.get(f"idempotency:{key}")
            return cached
        except Exception as e:
            print(f"[IDEMPOTENCY] Erro ao buscar cache: {e}")
            return None
    
    async def _cache_response(self, key: str, response: Response):
        """Cachear resposta"""
        try:
            # Ler body da resposta
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Decodificar body
            try:
                body_json = json.loads(body.decode())
            except:
                body_json = body.decode()
            
            # Preparar dados para cache
            cache_data = {
                "status_code": response.status_code,
                "body": body_json,
                "headers": dict(response.headers)
            }
            
            # Armazenar no cache
            await cache.set(
                f"idempotency:{key}",
                cache_data,
                ttl=self.ttl
            )
            
            print(f"[IDEMPOTENCY] Resposta cacheada: {key}")
            
            # Recriar response com body
            response.body_iterator = self._create_body_iterator(body)
            
        except Exception as e:
            print(f"[IDEMPOTENCY] Erro ao cachear resposta: {e}")
    
    @staticmethod
    async def _create_body_iterator(body: bytes):
        """Criar iterador de body"""
        yield body


async def check_idempotency(key: str) -> Optional[dict]:
    """
    Verificar se requisição já foi processada
    
    Args:
        key: Idempotency key
    
    Returns:
        Resposta cacheada ou None
    """
    if not key:
        return None
    
    try:
        cached = await cache.get(f"idempotency:{key}")
        return cached
    except Exception:
        return None


async def store_idempotency_result(
    key: str,
    result: dict,
    status_code: int = 200,
    ttl: int = 86400
):
    """
    Armazenar resultado de operação idempotente
    
    Args:
        key: Idempotency key
        result: Resultado da operação
        status_code: Status HTTP
        ttl: Tempo de vida em segundos (padrão: 24h)
    """
    if not key:
        return
    
    try:
        cache_data = {
            "status_code": status_code,
            "body": result,
            "headers": {}
        }
        
        await cache.set(
            f"idempotency:{key}",
            cache_data,
            ttl=ttl
        )
    except Exception as e:
        print(f"[IDEMPOTENCY] Erro ao armazenar resultado: {e}")
