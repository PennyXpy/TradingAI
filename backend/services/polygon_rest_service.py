# Polygon REST API Service for Stock Data and Search
import os
import httpx
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from services.redis_cache import get_cache

logger = logging.getLogger(__name__)

class PolygonRestService:
    """
    Polygon REST API service for stock data and search
    Handles tickers, market data, and search functionality
    """
    
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        self.cache = None
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests (5 requests per second max)
        
    async def initialize(self):
        """Initialize the service"""
        self.cache = await get_cache()
        
    async def _rate_limit(self):
        """Implement rate limiting to avoid 429 errors"""
        import time
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for stocks using Polygon tickers API
        """
        if not self.api_key:
            return await self._mock_search_results(query, limit)
            
        cache_key = f"stock_search:{query}:{limit}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
            
        try:
            await self._rate_limit()  # Apply rate limiting
            
            async with httpx.AsyncClient() as client:
                params = {
                    "search": query,
                    "market": "stocks",
                    "active": "true",
                    "limit": limit,
                    "apikey": self.api_key
                }
                
                response = await client.get(f"{self.base_url}/v3/reference/tickers", params=params)
                response.raise_for_status()
                
                data = response.json()
                results = []
                
                for ticker in data.get("results", []):
                    results.append({
                        "symbol": ticker.get("ticker", ""),
                        "name": ticker.get("name", ""),
                        "market": ticker.get("market", "stocks"),
                        "type": ticker.get("type", ""),
                        "active": ticker.get("active", True),
                        "currency_name": ticker.get("currency_name", "USD"),
                        "cik": ticker.get("cik"),
                        "composite_figi": ticker.get("composite_figi"),
                        "primary_exchange": ticker.get("primary_exchange")
                    })
                
                # Cache results for 10 minutes
                await self.cache.set(cache_key, results, ttl=600)
                return results
                
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return await self._mock_search_results(query, limit)
    
    async def get_stock_details(self, symbol: str) -> Dict:
        """
        Get detailed stock information using Polygon API
        """
        if not self.api_key:
            return await self._mock_stock_details(symbol)
            
        cache_key = f"stock_details:{symbol}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
            
        try:
            async with httpx.AsyncClient() as client:
                # Get ticker details with rate limiting
                await self._rate_limit()
                details_response = await client.get(
                    f"{self.base_url}/v3/reference/tickers/{symbol}",
                    params={"apikey": self.api_key}
                )
                
                # Get previous close with rate limiting
                await self._rate_limit()
                prev_close_response = await client.get(
                    f"{self.base_url}/v2/aggs/ticker/{symbol}/prev",
                    params={"adjusted": "true", "apikey": self.api_key}
                )
                
                details_data = details_response.json() if details_response.status_code == 200 else {}
                prev_close_data = prev_close_response.json() if prev_close_response.status_code == 200 else {}
                
                ticker_info = details_data.get("results", {})
                prev_close = prev_close_data.get("results", [{}])[0] if prev_close_data.get("results") else {}
                
                result = {
                    "symbol": symbol,
                    "name": ticker_info.get("name", symbol),
                    "market": ticker_info.get("market", "stocks"),
                    "type": ticker_info.get("type", ""),
                    "price": prev_close.get("c", 0),  # Close price
                    "open": prev_close.get("o", 0),
                    "high": prev_close.get("h", 0),
                    "low": prev_close.get("l", 0),
                    "volume": prev_close.get("v", 0),
                    "change": 0,  # Will be calculated from real-time data
                    "change_percent": 0,
                    "market_cap": ticker_info.get("market_cap"),
                    "description": ticker_info.get("description", ""),
                    "homepage_url": ticker_info.get("homepage_url", ""),
                    "primary_exchange": ticker_info.get("primary_exchange", ""),
                    "currency_name": ticker_info.get("currency_name", "USD"),
                    "timestamp": datetime.now().isoformat(),
                    "source": "polygon"
                }
                
                # Cache for 5 minutes
                await self.cache.set(cache_key, result, ttl=300)
                return result
                
        except Exception as e:
            logger.error(f"Error getting stock details for {symbol}: {e}")
            return await self._mock_stock_details(symbol)
    
    async def get_top_stocks(self, limit: int = 10) -> List[Dict]:
        """
        Get top performing stocks
        Note: Polygon doesn't have a direct "top stocks" endpoint,
        so we'll use a predefined list of popular stocks
        """
        cache_key = f"top_stocks:{limit}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
            
        popular_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMD", "META", "AMZN", "NFLX", "CRM"]
        stocks = []
        
        for i, symbol in enumerate(popular_symbols[:limit]):
            if i > 0:  # Add delay between requests to prevent rate limiting
                await asyncio.sleep(0.5)  # 500ms delay between stock requests
            stock_data = await self.get_stock_details(symbol)
            if stock_data and "error" not in stock_data:
                stocks.append(stock_data)
        
        # Cache for 2 minutes
        await self.cache.set(cache_key, stocks, ttl=120)
        return stocks
    
    async def get_market_indexes(self) -> List[Dict]:
        """
        Get major market indexes data
        """
        cache_key = "market_indexes"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
            
        index_symbols = ["SPY", "QQQ", "DIA", "IWM"]  # Major ETFs that track indexes
        indexes = []
        
        for i, symbol in enumerate(index_symbols):
            if i > 0:  # Add delay between requests to prevent rate limiting
                await asyncio.sleep(0.5)  # 500ms delay between index requests
            index_data = await self.get_stock_details(symbol)
            if index_data and "error" not in index_data:
                # Add index-specific naming
                index_names = {
                    "SPY": "S&P 500 ETF",
                    "QQQ": "NASDAQ ETF", 
                    "DIA": "Dow Jones ETF",
                    "IWM": "Russell 2000 ETF"
                }
                index_data["name"] = index_names.get(symbol, index_data["name"])
                indexes.append(index_data)
        
        # Cache for 1 minute
        await self.cache.set(cache_key, indexes, ttl=60)
        return indexes
    
    async def _mock_search_results(self, query: str, limit: int) -> List[Dict]:
        """Mock search results when API is not available"""
        mock_stocks = [
            {"symbol": "AAPL", "name": "Apple Inc.", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "TSLA", "name": "Tesla, Inc.", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "AMD", "name": "Advanced Micro Devices, Inc.", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "META", "name": "Meta Platforms, Inc.", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "AMZN", "name": "Amazon.com, Inc.", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "NFLX", "name": "Netflix, Inc.", "market": "stocks", "type": "CS", "active": True},
            {"symbol": "CRM", "name": "Salesforce, Inc.", "market": "stocks", "type": "CS", "active": True}
        ]
        
        query_lower = query.lower()
        filtered_stocks = [
            stock for stock in mock_stocks 
            if query_lower in stock["symbol"].lower() or query_lower in stock["name"].lower()
        ]
        
        return filtered_stocks[:limit]
    
    async def _mock_stock_details(self, symbol: str) -> Dict:
        """Mock stock details when API is not available"""
        import random
        
        mock_data = {
            "AAPL": {"name": "Apple Inc.", "price": 175.0},
            "GOOGL": {"name": "Alphabet Inc.", "price": 140.0},
            "MSFT": {"name": "Microsoft Corporation", "price": 380.0},
            "TSLA": {"name": "Tesla, Inc.", "price": 250.0},
            "NVDA": {"name": "NVIDIA Corporation", "price": 450.0},
            "AMD": {"name": "Advanced Micro Devices, Inc.", "price": 145.0},
            "META": {"name": "Meta Platforms, Inc.", "price": 320.0},
            "AMZN": {"name": "Amazon.com, Inc.", "price": 145.0},
            "NFLX": {"name": "Netflix, Inc.", "price": 480.0},
            "CRM": {"name": "Salesforce, Inc.", "price": 250.0}
        }
        
        if symbol in mock_data:
            base_data = mock_data[symbol]
            price = base_data["price"]
            change = random.uniform(-5, 5)
            
            return {
                "symbol": symbol,
                "name": base_data["name"],
                "market": "stocks",
                "type": "CS",
                "price": round(price + change, 2),
                "open": round(price * random.uniform(0.99, 1.01), 2),
                "high": round(price * random.uniform(1.01, 1.03), 2),
                "low": round(price * random.uniform(0.97, 0.99), 2),
                "volume": random.randint(1000000, 10000000),
                "change": round(change, 2),
                "change_percent": round((change / price) * 100, 2),
                "market_cap": random.randint(100000000000, 3000000000000),
                "description": f"Mock data for {base_data['name']}",
                "primary_exchange": "NASDAQ",
                "currency_name": "USD",
                "timestamp": datetime.now().isoformat(),
                "source": "mock"
            }
        else:
            return {"error": f"Stock {symbol} not found"}

# Global service instance
_polygon_rest_service: Optional[PolygonRestService] = None

async def get_polygon_rest_service() -> PolygonRestService:
    """Get or create the global Polygon REST service"""
    global _polygon_rest_service
    
    if _polygon_rest_service is None:
        _polygon_rest_service = PolygonRestService()
        await _polygon_rest_service.initialize()
    
    return _polygon_rest_service