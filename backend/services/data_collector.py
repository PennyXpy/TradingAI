# Layer 1: Data Collection and Caching Service
# Collects data from third-party APIs (currently using mock data) and stores in global cache

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

# Mock data imports (later replaced with real APIs)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mock_data.financial_data_generator import (
    generate_stock_price, generate_historical_prices, generate_news_article,
    generate_multiple_news, generate_technical_indicators, generate_crypto_price,
    generate_market_summary, STOCK_SYMBOLS, COMPANY_NAMES, SECTORS
)


from services.redis_cache import get_cache, RedisCache

class CacheManager:
    """Cache manager using Redis with in-memory fallback"""
    
    def __init__(self):
        self.redis_cache = None
    
    async def initialize(self):
        """Initialize the Redis cache connection"""
        self.redis_cache = await get_cache()
    
    async def store(self, key: str, data: Any, ttl: int = 300) -> None:
        """Store data in cache with TTL (Time To Live)"""
        if not self.redis_cache:
            await self.initialize()
        await self.redis_cache.set(key, data, ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cache if not expired"""
        if not self.redis_cache:
            await self.initialize()
        return await self.redis_cache.get(key)
    
    async def delete(self, key: str) -> None:
        """Delete data from cache"""
        if not self.redis_cache:
            await self.initialize()
        await self.redis_cache.delete(key)
    
    async def clear_expired(self) -> int:
        """Redis automatically handles TTL, return 0 for compatibility"""
        return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics from Redis"""
        if not self.redis_cache:
            await self.initialize()
        return await self.redis_cache.get_cache_info()


class DataCollector:
    """Main data collection service - Layer 1 of the 5-layer architecture"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.collection_status = {
            "last_update": None,
            "next_update": None,
            "collection_count": 0,
            "errors": []
        }
    
    async def collect_all_market_data(self) -> Dict[str, Any]:
        """Collect all market data and store in cache - Main Layer 1 function"""
        start_time = time.time()
        results = {}
        
        try:
            print("🔄 Layer 1: Starting data collection...")
            
            # Collect different types of data in parallel
            tasks = [
                self.collect_stocks_data(),
                self.collect_crypto_data(),
                self.collect_market_indices(),
                self.collect_news_data(),
                self.collect_market_summary()
            ]
            
            # Execute all collection tasks
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(task_results):
                if isinstance(result, Exception):
                    error_msg = f"Task {i} failed: {str(result)}"
                    self.collection_status["errors"].append(error_msg)
                    print(f"❌ {error_msg}")
                else:
                    results.update(result)
            
            # Update collection status
            self.collection_status.update({
                "last_update": datetime.now(),
                "next_update": datetime.now() + timedelta(minutes=5),
                "collection_count": self.collection_status["collection_count"] + 1,
                "collection_time": time.time() - start_time
            })
            
            print(f"✅ Layer 1: Data collection completed in {time.time() - start_time:.2f}s")
            return results
            
        except Exception as e:
            error_msg = f"Data collection failed: {str(e)}"
            self.collection_status["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return {}
    
    async def collect_stocks_data(self) -> Dict[str, Any]:
        """Collect stock market data"""
        try:
            stocks_data = {}
            
            for symbol in STOCK_SYMBOLS:
                # Generate current price data
                price_data = generate_stock_price(symbol)
                
                # Generate historical data (30 days)
                historical_data = generate_historical_prices(symbol, days=30)
                
                # Generate technical indicators
                technical_data = generate_technical_indicators(symbol, historical_data)
                
                # Combine all data
                stocks_data[symbol] = {
                    **price_data,
                    "company_name": COMPANY_NAMES.get(symbol, f"{symbol} Corp"),
                    "sector": SECTORS.get(symbol, "Unknown"),
                    "historical_prices": historical_data,
                    "technical_indicators": technical_data["technical_indicators"],
                    "moving_averages": technical_data["moving_averages"],
                    "last_updated": datetime.now().isoformat()
                }
            
            # Store in cache with 5-minute TTL
            await self.cache.store("stocks", stocks_data, ttl=300)
            print(f"📈 Collected data for {len(stocks_data)} stocks")
            
            return {"stocks": stocks_data}
            
        except Exception as e:
            print(f"❌ Error collecting stocks data: {str(e)}")
            return {}
    
    async def collect_crypto_data(self) -> Dict[str, Any]:
        """Collect cryptocurrency data"""
        try:
            crypto_symbols = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI"]
            crypto_data = {}
            
            for symbol in crypto_symbols:
                crypto_data[symbol] = generate_crypto_price(symbol)
            
            # Store in cache
            await self.cache.store("crypto", crypto_data, ttl=300)
            print(f"₿ Collected data for {len(crypto_data)} cryptocurrencies")
            
            return {"crypto": crypto_data}
            
        except Exception as e:
            print(f"❌ Error collecting crypto data: {str(e)}")
            return {}
    
    async def collect_market_indices(self) -> Dict[str, Any]:
        """Collect major market indices"""
        try:
            indices_symbols = ["^GSPC", "^DJI", "^IXIC", "^RUT"]  # S&P 500, Dow, NASDAQ, Russell 2000
            indices_data = {}
            
            for symbol in indices_symbols:
                # Generate index data (similar to stock data)
                index_data = generate_stock_price(symbol.replace("^", ""))
                index_data["symbol"] = symbol
                indices_data[symbol] = index_data
            
            # Store in cache
            await self.cache.store("market_indices", indices_data, ttl=300)
            print(f"📊 Collected data for {len(indices_data)} market indices")
            
            return {"market_indices": indices_data}
            
        except Exception as e:
            print(f"❌ Error collecting indices data: {str(e)}")
            return {}
    
    async def collect_news_data(self) -> Dict[str, Any]:
        """Collect financial news data"""
        try:
            # Generate general market news (15 articles)
            general_news = generate_multiple_news(
                symbols=STOCK_SYMBOLS[:5],  # Top 5 stocks for general news
                articles_per_symbol=3
            )
            
            # Generate stock-specific news for each symbol
            stock_news = {}
            for symbol in STOCK_SYMBOLS:
                stock_news[symbol] = generate_multiple_news([symbol], articles_per_symbol=2)
            
            news_data = {
                "general_news": general_news,
                "stock_specific_news": stock_news,
                "last_updated": datetime.now().isoformat()
            }
            
            # Store in cache with 30-minute TTL
            await self.cache.store("news", news_data, ttl=1800)
            print(f"📰 Collected {len(general_news)} general news articles and stock-specific news")
            
            return {"news": news_data}
            
        except Exception as e:
            print(f"❌ Error collecting news data: {str(e)}")
            return {}
    
    async def collect_market_summary(self) -> Dict[str, Any]:
        """Collect overall market summary"""
        try:
            market_summary = generate_market_summary()
            
            # Store in cache
            await self.cache.store("market_summary", market_summary, ttl=600)  # 10-minute TTL
            print("📈 Collected market summary data")
            
            return {"market_summary": market_summary}
            
        except Exception as e:
            print(f"❌ Error collecting market summary: {str(e)}")
            return {}
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status"""
        return self.collection_status


# Global instances
_cache_manager = CacheManager()
_data_collector = DataCollector(_cache_manager)


async def start_data_collection() -> None:
    """Start the data collection process"""
    await _data_collector.collect_all_market_data()


async def get_cached_data(key: str) -> Optional[Any]:
    """Get data from cache"""
    return await _cache_manager.get(key)


async def get_all_cached_data() -> Dict[str, Any]:
    """Get all cached data for Layer 2 (main page)"""
    data = {}
    
    # Get all cached data types
    for key in ["stocks", "crypto", "market_indices", "news", "market_summary"]:
        cached_data = await get_cached_data(key)
        if cached_data:
            data[key] = cached_data
    
    return data


def get_data_collector() -> DataCollector:
    """Get the global data collector instance"""
    return _data_collector


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    return _cache_manager


# Scheduler function for periodic data collection
async def schedule_data_collection(interval_minutes: int = 5):
    """Schedule periodic data collection"""
    print(f"🔄 Starting scheduled data collection every {interval_minutes} minutes")
    
    while True:
        try:
            await start_data_collection()
            print(f"⏰ Next collection in {interval_minutes} minutes")
            await asyncio.sleep(interval_minutes * 60)
        except Exception as e:
            print(f"❌ Scheduled collection error: {str(e)}")
            await asyncio.sleep(60)  # Retry in 1 minute on error


# Context manager for data collection service
@asynccontextmanager
async def data_collection_service():
    """Context manager to manage data collection lifecycle"""
    print("🚀 Starting Layer 1: Data Collection Service")
    
    # Initial data collection
    await start_data_collection()
    
    # Start background scheduler
    scheduler_task = asyncio.create_task(schedule_data_collection())
    
    try:
        yield _data_collector, _cache_manager
    finally:
        print("🛑 Stopping Layer 1: Data Collection Service")
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


# Testing and CLI functions
async def test_data_collection():
    """Test the data collection system"""
    print("🧪 Testing Layer 1: Data Collection")
    print("=" * 50)
    
    # Test data collection
    collector = get_data_collector()
    cache = get_cache_manager()
    
    # Run collection
    results = await collector.collect_all_market_data()
    
    # Test cache retrieval
    stocks_data = await cache.get("stocks")
    news_data = await cache.get("news")
    
    print(f"\n📊 Collection Results:")
    print(f"- Stocks collected: {len(stocks_data) if stocks_data else 0}")
    print(f"- News articles: {len(news_data.get('general_news', [])) if news_data else 0}")
    print(f"- Collection status: {collector.get_collection_status()}")
    print(f"- Cache stats: {cache.get_cache_stats()}")


if __name__ == "__main__":
    print("🚀 Layer 1: Data Collector - Testing Mode")
    asyncio.run(test_data_collection())