# Redis-compatible Cache System for TradingAI
# Falls back to in-memory cache if Redis is not available

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache fallback")


class RedisCache:
    """Redis-compatible cache with in-memory fallback"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.fallback_cache: Dict[str, Any] = {}
        self.fallback_timestamps: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        self.use_redis = False
        
    async def initialize(self):
        """Initialize Redis connection with fallback to in-memory"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
                self.use_redis = True
                logger.info("✅ Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory cache")
                self.use_redis = False
        else:
            logger.info("Redis not available, using in-memory cache")
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set a value in cache with TTL"""
        try:
            if self.use_redis and self.redis_client:
                # Redis implementation
                json_value = json.dumps(value, default=str)
                await self.redis_client.setex(f"tradingai:{key}", ttl, json_value)
                return True
            else:
                # In-memory fallback
                async with self._lock:
                    self.fallback_cache[key] = value
                    self.fallback_timestamps[key] = datetime.now() + timedelta(seconds=ttl)
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            if self.use_redis and self.redis_client:
                # Redis implementation
                value = await self.redis_client.get(f"tradingai:{key}")
                if value:
                    return json.loads(value)
                return None
            else:
                # In-memory fallback
                async with self._lock:
                    if key not in self.fallback_cache:
                        return None
                    
                    # Check expiration
                    if datetime.now() > self.fallback_timestamps[key]:
                        del self.fallback_cache[key]
                        del self.fallback_timestamps[key]
                        return None
                    
                    return self.fallback_cache[key]
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.delete(f"tradingai:{key}")
            else:
                async with self._lock:
                    if key in self.fallback_cache:
                        del self.fallback_cache[key]
                        del self.fallback_timestamps[key]
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        try:
            if self.use_redis and self.redis_client:
                return bool(await self.redis_client.exists(f"tradingai:{key}"))
            else:
                async with self._lock:
                    if key in self.fallback_cache:
                        # Check if not expired
                        if datetime.now() <= self.fallback_timestamps[key]:
                            return True
                        else:
                            # Clean up expired key
                            del self.fallback_cache[key]
                            del self.fallback_timestamps[key]
                    return False
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            if self.use_redis and self.redis_client:
                keys = await self.redis_client.keys(f"tradingai:{pattern}")
                return [key.decode().replace("tradingai:", "") for key in keys]
            else:
                # Simple pattern matching for in-memory cache
                async with self._lock:
                    all_keys = []
                    for key in self.fallback_cache.keys():
                        if datetime.now() <= self.fallback_timestamps[key]:
                            if pattern == "*" or pattern in key:
                                all_keys.append(key)
                    return all_keys
        except Exception as e:
            logger.error(f"Cache keys error: {e}")
            return []
    
    async def flush_all(self) -> bool:
        """Clear all cache data"""
        try:
            if self.use_redis and self.redis_client:
                keys = await self.redis_client.keys("tradingai:*")
                if keys:
                    await self.redis_client.delete(*keys)
            else:
                async with self._lock:
                    self.fallback_cache.clear()
                    self.fallback_timestamps.clear()
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.use_redis and self.redis_client:
                info = await self.redis_client.info()
                return {
                    "type": "redis",
                    "connected": True,
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                }
            else:
                async with self._lock:
                    return {
                        "type": "in_memory",
                        "connected": True,
                        "keys_count": len(self.fallback_cache),
                        "memory_usage": "in_memory_fallback"
                    }
        except Exception as e:
            return {
                "type": "error",
                "connected": False,
                "error": str(e)
            }
    
    async def close(self):
        """Close Redis connection"""
        if self.use_redis and self.redis_client:
            await self.redis_client.close()


# Alias for backward compatibility
RedisCompatibleCache = RedisCache

# Global cache instance
cache_instance = RedisCache()


async def get_cache() -> RedisCache:
    """Get the global cache instance"""
    if not cache_instance.use_redis and not cache_instance.fallback_cache:
        await cache_instance.initialize()
    return cache_instance

async def get_cache_manager() -> RedisCache:
    """Alias for get_cache() for backward compatibility"""
    return await get_cache()