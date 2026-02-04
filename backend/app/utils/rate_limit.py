import time
import redis
from collections import defaultdict
from app.core.config import settings

# Redis client for rate limiting (string operations)
redis_rate_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Rate Limiting Simples (fallback)
rate_limit_store = defaultdict(list)

def check_rate_limit(ip: str, max_requests: int = 100, window_seconds: int = 3600):
    now = time.time()
    requests_list = rate_limit_store[ip]
    
    # Remover requisições antigas
    requests_list[:] = [req_time for req_time in requests_list if now - req_time < window_seconds]
    
    if len(requests_list) >= max_requests:
        return False
    
    requests_list.append(now)
    return True

def check_rate_limit_redis(key: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
    """Rate limiting using Redis with sliding window"""
    try:
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        # Remove old entries
        redis_rate_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_requests = redis_rate_client.zcard(key)
        
        if current_requests >= max_requests:
            return False
        
        # Add current request
        redis_rate_client.zadd(key, {str(current_time): current_time})
        redis_rate_client.expire(key, window_seconds)
        
        return True
        
    except Exception as e:
        print(f"[REDIS] Rate limit fallback due to error: {e}")
        # Fallback to in-memory rate limiting
        ip = key.split(':')[-1] if ':' in key else key
        return check_rate_limit(ip, max_requests, window_seconds)