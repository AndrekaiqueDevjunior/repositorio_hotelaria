import pickle
import redis
from functools import wraps
from typing import Callable, Any
from app.core.config import settings

# Redis client for caching
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=False,  # Keep binary for pickle
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)


def cache_result(key_prefix: str, ttl: int = 300):
    """Decorator for caching function results in Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Generate cache key
                cache_key = f"hotel:{key_prefix}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    return pickle.loads(cached_result)
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                redis_client.setex(
                    cache_key,
                    ttl,
                    pickle.dumps(result)
                )
                
                return result
                
            except Exception as e:
                print(f"[REDIS] Cache fallback due to error: {e}")
                # Fallback to direct function execution
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern"""
    try:
        search_pattern = f"hotel:{pattern}:*"
        keys = redis_client.keys(search_pattern)
        
        if keys:
            redis_client.delete(*keys)
            print(f"[REDIS] Invalidated {len(keys)} cache keys for pattern: {pattern}")
        
    except Exception as e:
        print(f"[REDIS] Cache invalidation error: {e}")
        # Continue silently - cache will expire naturally