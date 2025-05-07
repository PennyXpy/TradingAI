import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# 简单的内存缓存
cache_store = {}

def cache_result(expire_seconds=300):  # 默认缓存5分钟
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 创建缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 检查缓存
            if cache_key in cache_store:
                result, timestamp = cache_store[cache_key]
                if time.time() - timestamp < expire_seconds:
                    logger.info(f"✅ 使用缓存: {func.__name__}")
                    return result
            
            # 执行原始函数
            result = await func(*args, **kwargs)
            
            # 存储结果到缓存
            cache_store[cache_key] = (result, time.time())
            logger.info(f"🔄 更新缓存: {func.__name__}")
            
            return result
        return wrapper
    return decorator