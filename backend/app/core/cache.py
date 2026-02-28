"""
Cache Manager usando Redis
Gerencia cache de dados com TTL configurável
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
from contextlib import asynccontextmanager
import asyncio
import uuid
import hashlib
from functools import wraps
import os

class CacheManager:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Conectar ao Redis"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            print(f"[CACHE] Conectado ao Redis: {redis_url}")
        except Exception as e:
            print(f"[CACHE] Erro ao conectar ao Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Desconectar do Redis"""
        if self.redis:
            await self.redis.close()
            print("[CACHE] Desconectado do Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Buscar valor do cache"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            print(f"[CACHE] Erro ao buscar chave {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300  # 5 minutos padrão
    ):
        """Armazenar valor no cache"""
        if not self.redis:
            return
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            await self.redis.setex(key, ttl, value)
        except Exception as e:
            print(f"[CACHE] Erro ao armazenar chave {key}: {e}")
    
    async def delete(self, key: str):
        """Remover valor do cache"""
        if not self.redis:
            return
        
        try:
            await self.redis.delete(key)
        except Exception as e:
            print(f"[CACHE] Erro ao deletar chave {key}: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Remover múltiplas chaves por padrão"""
        if not self.redis:
            return
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
                print(f"[CACHE] Deletadas {len(keys)} chaves com padrão {pattern}")
        except Exception as e:
            print(f"[CACHE] Erro ao deletar padrão {pattern}: {e}")
    
    async def incr(self, key: str) -> int:
        """Incrementar contador"""
        if not self.redis:
            return 0
        
        try:
            return await self.redis.incr(key)
        except Exception as e:
            print(f"[CACHE] Erro ao incrementar {key}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int):
        """Definir expiração de chave"""
        if not self.redis:
            return
        
        try:
            await self.redis.expire(key, seconds)
        except Exception as e:
            print(f"[CACHE] Erro ao definir expiração de {key}: {e}")
    
    async def ttl(self, key: str) -> int:
        """Obter tempo restante de expiração"""
        if not self.redis:
            return -1
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            print(f"[CACHE] Erro ao obter TTL de {key}: {e}")
            return -1


# Instância global
cache = CacheManager()


def _generate_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """Gerar chave de cache única"""
    key_parts = [prefix]
    
    for arg in args:
        if hasattr(arg, '__dict__'):
            # Objeto (ex: self), pular
            continue
        key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    key_string = ":".join(key_parts)
    
    # Hash para evitar chaves muito longas
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator para cachear resultado de função
    
    Args:
        ttl: Tempo de vida em segundos
        key_prefix: Prefixo da chave de cache
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave única baseada em argumentos
            cache_key = _generate_cache_key(
                key_prefix or func.__name__,
                args,
                kwargs
            )
            
            # Tentar buscar do cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Executar função
            result = await func(*args, **kwargs)
            
            # Armazenar no cache
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


@asynccontextmanager
async def redis_lock(key: str, timeout: int = 10):
    """
    Lock distribuído usando Redis
    
    Args:
        key: Chave do lock
        timeout: Timeout em segundos
    
    Yields:
        None quando lock adquirido
    
    Raises:
        TimeoutError: Se não conseguir adquirir lock
    """
    lock_key = f"lock:{key}"
    lock_value = str(uuid.uuid4())
    
    # Tentar adquirir lock
    acquired = False
    for _ in range(timeout * 10):  # Tentar por timeout segundos
        if cache.redis:
            acquired = await cache.redis.set(
                lock_key,
                lock_value,
                ex=timeout,
                nx=True  # Set only if not exists
            )
            if acquired:
                break
        await asyncio.sleep(0.1)
    
    if not acquired:
        raise TimeoutError(f"Não foi possível adquirir lock: {key}")
    
    try:
        yield
    finally:
        # Liberar lock apenas se ainda é nosso
        if cache.redis:
            try:
                current = await cache.redis.get(lock_key)
                if current == lock_value:
                    await cache.redis.delete(lock_key)
            except Exception as e:
                print(f"[LOCK] Erro ao liberar lock {key}: {e}")
