from fastapi import HTTPException, Request
from typing import Dict, Callable
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc, timedelta
import asyncio


class RateLimiter:
    """
    Rate limiter simples baseado em memória
    Para produção, usar Redis ou similar
    """
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Verificar se requisição está dentro do limite
        
        Args:
            key: Identificador único (ex: IP + endpoint)
            max_requests: Número máximo de requisições
            window_seconds: Janela de tempo em segundos
        
        Returns:
            True se dentro do limite, False caso contrário
        """
        async with self.lock:
            now = now_utc()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Inicializar se não existir
            if key not in self.requests:
                self.requests[key] = []
            
            # Remover requisições antigas
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff
            ]
            
            # Verificar limite
            if len(self.requests[key]) >= max_requests:
                return False
            
            # Adicionar nova requisição
            self.requests[key] = self.requests[key]
            self.requests[key].append(now)
            
            return True
    
    async def cleanup_old_entries(self, max_age_hours: int = 24):
        """Limpar entradas antigas para evitar memory leak"""
        async with self.lock:
            cutoff = now_utc() - timedelta(hours=max_age_hours)
            keys_to_remove = []
            
            for key, timestamps in self.requests.items():
                # Remover timestamps antigos
                self.requests[key] = [t for t in timestamps if t > cutoff]
                
                # Marcar chave vazia para remoção
                if not self.requests[key]:
                    keys_to_remove.append(key)
            
            # Remover chaves vazias
            for key in keys_to_remove:
                del self.requests[key]


# Instância global
rate_limiter = RateLimiter()


def get_client_identifier(request: Request) -> str:
    """Obter identificador único do cliente"""
    # Tentar obter IP real (considerando proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    
    return ip


async def rate_limit_dependency(
    request: Request,
    max_requests: int = 10,
    window_seconds: int = 60
) -> None:
    """
    Dependency para rate limiting
    
    Usage:
        @router.post("/endpoint")
        async def my_endpoint(
            _: None = Depends(lambda r: rate_limit_dependency(r, max_requests=5, window_seconds=60))
        ):
            ...
    """
    client_id = get_client_identifier(request)
    endpoint = request.url.path
    key = f"{client_id}:{endpoint}"
    
    allowed = await rate_limiter.check_rate_limit(key, max_requests, window_seconds)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds."
        )


# Decorators específicos para diferentes limites
def rate_limit_strict(request: Request) -> None:
    """Rate limit estrito: 5 requisições por minuto"""
    return rate_limit_dependency(request, max_requests=5, window_seconds=60)


def rate_limit_moderate(request: Request) -> None:
    """Rate limit moderado: 20 requisições por minuto"""
    return rate_limit_dependency(request, max_requests=20, window_seconds=60)


def rate_limit_generous(request: Request) -> None:
    """Rate limit generoso: 100 requisições por minuto"""
    return rate_limit_dependency(request, max_requests=100, window_seconds=60)
