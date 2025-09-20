# Layer 2: Main Page Data Service
# Provides data for the main page directly from Layer 1 cached data

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

from .data_collector import get_cached_data, get_cache_manager


class MainPageService:
    """Service for providing main page data - Layer 2 of 5-layer architecture"""
    
    def __init__(self):
        self.cache = get_cache_manager()
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get complete market overview for main page"""
        try:
            # Get all cached data
            stocks_data = await get_cached_data("stocks")
            crypto_data = await get_cached_data("crypto") 
            indices_data = await get_cached_data("market_indices")
            news_data = await get_cached_data("news")
            market_summary = await get_cached_data("market_summary")
            
            if not stocks_data:
                return {"error": "Market data not available"}
            
            # Process data for main page display
            overview = {
                "market_indices": await self._get_main_indices(indices_data),
                "top_stocks": await self._get_top_stocks(stocks_data),
                "top_gainers": await self._get_top_gainers(stocks_data),
                "top_losers": await self._get_top_losers(stocks_data), 
                "crypto_overview": await self._get_crypto_overview(crypto_data),
                "latest_news": await self._get_latest_news(news_data),
                "market_summary": market_summary,
                "last_updated": datetime.now().isoformat()
            }
            
            return overview
            
        except Exception as e:
            print(f"❌ Error getting market overview: {str(e)}")
            return {"error": str(e)}
    
    async def _get_main_indices(self, indices_data: Optional[Dict]) -> List[Dict]:
        """Get main market indices for display"""
        if not indices_data:
            return []
        
        # Map indices to display names
        index_mapping = {
            "^GSPC": {"name": "S&P 500", "symbol": "SPX"},
            "^DJI": {"name": "Dow Jones", "symbol": "DJI"},
            "^IXIC": {"name": "NASDAQ", "symbol": "IXIC"},
            "^RUT": {"name": "Russell 2000", "symbol": "RUT"}
        }
        
        main_indices = []
        for symbol, data in indices_data.items():
            if symbol in index_mapping:
                index_info = index_mapping[symbol]
                main_indices.append({
                    "symbol": index_info["symbol"],
                    "name": index_info["name"],
                    "price": data["current_price"],
                    "change": data["change"],
                    "change_percent": data["change_percent"],
                    "is_positive": data["change"] >= 0
                })
        
        return main_indices
    
    async def _get_top_stocks(self, stocks_data: Dict) -> List[Dict]:
        """Get top stocks by market cap for main page"""
        if not stocks_data:
            return []
        
        # Filter major stocks and sort by market cap
        major_stocks = []
        for symbol, data in stocks_data.items():
            if symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]:
                major_stocks.append({
                    "symbol": symbol,
                    "name": data["company_name"],
                    "category": data["sector"],
                    "price": data["current_price"],
                    "change": data["change"],
                    "change_percent": data["change_percent"],
                    "is_positive": data["change"] >= 0,
                    "market_cap": data["market_cap"],
                    "volume": data["volume"]
                })
        
        # Sort by market cap and return top 6
        major_stocks.sort(key=lambda x: x["market_cap"], reverse=True)
        return major_stocks[:6]
    
    async def _get_top_gainers(self, stocks_data: Dict) -> List[Dict]:
        """Get top gaining stocks"""
        if not stocks_data:
            return []
        
        gainers = []
        for symbol, data in stocks_data.items():
            if data["change_percent"] > 0:
                gainers.append({
                    "symbol": symbol,
                    "name": data["company_name"],
                    "price": data["current_price"],
                    "change": data["change"],
                    "change_percent": data["change_percent"],
                    "volume": data["volume"]
                })
        
        # Sort by change percentage and return top 5
        gainers.sort(key=lambda x: x["change_percent"], reverse=True)
        return gainers[:5]
    
    async def _get_top_losers(self, stocks_data: Dict) -> List[Dict]:
        """Get top losing stocks"""
        if not stocks_data:
            return []
        
        losers = []
        for symbol, data in stocks_data.items():
            if data["change_percent"] < 0:
                losers.append({
                    "symbol": symbol,
                    "name": data["company_name"],
                    "price": data["current_price"],
                    "change": data["change"],
                    "change_percent": data["change_percent"],
                    "volume": data["volume"]
                })
        
        # Sort by change percentage (most negative first) and return top 5
        losers.sort(key=lambda x: x["change_percent"])
        return losers[:5]
    
    async def _get_crypto_overview(self, crypto_data: Optional[Dict]) -> List[Dict]:
        """Get cryptocurrency overview"""
        if not crypto_data:
            return []
        
        crypto_overview = []
        for symbol, data in crypto_data.items():
            crypto_overview.append({
                "symbol": symbol,
                "name": data["name"],
                "price": data["current_price"],
                "change": data["change"],
                "change_percent": data["change_percent"],
                "is_positive": data["change"] >= 0,
                "market_cap": data.get("market_cap", 0),
                "volume_24h": data.get("volume_24h", 0)
            })
        
        # Sort by market cap
        crypto_overview.sort(key=lambda x: x["market_cap"], reverse=True)
        return crypto_overview[:6]
    
    async def _get_latest_news(self, news_data: Optional[Dict]) -> List[Dict]:
        """Get latest financial news for main page"""
        if not news_data or "general_news" not in news_data:
            return []
        
        news_articles = news_data["general_news"]
        
        # Format news for main page display
        formatted_news = []
        for article in news_articles[:12]:  # Get top 12 articles
            formatted_news.append({
                "id": article.get("id", ""),
                "title": article["headline"],
                "description": article["summary"],
                "category": article.get("category", "Market Update"),
                "sentiment_score": article["sentiment_score"],
                "sentiment_label": article["sentiment_label"],
                "related_symbols": article.get("related_symbols", []),
                "published_at": article["datetime"],
                "source": article.get("source", "Financial News")
            })
        
        return formatted_news
    
    async def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data"""
        try:
            stocks_data = await get_cached_data("stocks")
            if not stocks_data:
                return {"error": "No stocks data available"}
            
            # Group stocks by sector and calculate performance
            sector_performance = {}
            
            for symbol, data in stocks_data.items():
                sector = data["sector"]
                if sector not in sector_performance:
                    sector_performance[sector] = {
                        "sector": sector,
                        "stocks_count": 0,
                        "total_change": 0,
                        "positive_stocks": 0,
                        "stocks": []
                    }
                
                sector_data = sector_performance[sector]
                sector_data["stocks_count"] += 1
                sector_data["total_change"] += data["change_percent"]
                if data["change_percent"] > 0:
                    sector_data["positive_stocks"] += 1
                
                sector_data["stocks"].append({
                    "symbol": symbol,
                    "name": data["company_name"],
                    "change_percent": data["change_percent"]
                })
            
            # Calculate average performance for each sector
            sector_list = []
            for sector, data in sector_performance.items():
                avg_performance = data["total_change"] / data["stocks_count"] if data["stocks_count"] > 0 else 0
                sector_list.append({
                    "sector": sector,
                    "avg_performance": round(avg_performance, 2),
                    "stocks_count": data["stocks_count"],
                    "positive_ratio": data["positive_stocks"] / data["stocks_count"] if data["stocks_count"] > 0 else 0,
                    "top_stocks": sorted(data["stocks"], key=lambda x: x["change_percent"], reverse=True)[:3]
                })
            
            # Sort by performance
            sector_list.sort(key=lambda x: x["avg_performance"], reverse=True)
            
            return {
                "sectors": sector_list,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting sector performance: {str(e)}")
            return {"error": str(e)}
    
    async def get_trending_stocks(self, limit: int = 10) -> List[Dict]:
        """Get trending stocks based on volume and price movement"""
        try:
            stocks_data = await get_cached_data("stocks")
            if not stocks_data:
                return []
            
            trending = []
            for symbol, data in stocks_data.items():
                # Calculate trending score based on volume and price change
                volume_score = min(data["volume"] / 1000000, 10)  # Normalize volume
                change_score = abs(data["change_percent"]) * 2    # Weight by price movement
                trending_score = volume_score + change_score
                
                trending.append({
                    "symbol": symbol,
                    "name": data["company_name"],
                    "price": data["current_price"],
                    "change": data["change"],
                    "change_percent": data["change_percent"],
                    "volume": data["volume"],
                    "trending_score": trending_score,
                    "is_positive": data["change"] >= 0
                })
            
            # Sort by trending score and return top results
            trending.sort(key=lambda x: x["trending_score"], reverse=True)
            return trending[:limit]
            
        except Exception as e:
            print(f"❌ Error getting trending stocks: {str(e)}")
            return []


# Global service instance
_main_page_service = MainPageService()


async def get_market_overview() -> Dict[str, Any]:
    """Get market overview for main page - Layer 2 main function"""
    return await _main_page_service.get_market_overview()


async def get_sector_performance() -> Dict[str, Any]:
    """Get sector performance data"""
    return await _main_page_service.get_sector_performance()


async def get_trending_stocks(limit: int = 10) -> List[Dict]:
    """Get trending stocks"""
    return await _main_page_service.get_trending_stocks(limit)


def get_main_page_service() -> MainPageService:
    """Get the main page service instance"""
    return _main_page_service


# Testing function
async def test_main_page_service():
    """Test the main page service"""
    print("🧪 Testing Layer 2: Main Page Service")
    print("=" * 50)
    
    # Ensure we have data in cache first
    from .data_collector import start_data_collection
    await start_data_collection()
    
    # Test market overview
    overview = await get_market_overview()
    print(f"\n📊 Market Overview:")
    print(f"- Top stocks: {len(overview.get('top_stocks', []))}")
    print(f"- Gainers: {len(overview.get('top_gainers', []))}")
    print(f"- Losers: {len(overview.get('top_losers', []))}")
    print(f"- News articles: {len(overview.get('latest_news', []))}")
    print(f"- Crypto assets: {len(overview.get('crypto_overview', []))}")
    
    # Test sector performance
    sectors = await get_sector_performance()
    print(f"\n🏭 Sector Performance:")
    if "sectors" in sectors:
        for sector in sectors["sectors"][:5]:
            print(f"- {sector['sector']}: {sector['avg_performance']:.2f}%")
    
    # Test trending stocks
    trending = await get_trending_stocks(5)
    print(f"\n🔥 Trending Stocks:")
    for stock in trending:
        print(f"- {stock['symbol']}: {stock['change_percent']:.2f}% (Score: {stock['trending_score']:.1f})")


if __name__ == "__main__":
    print("🚀 Layer 2: Main Page Service - Testing Mode")
    asyncio.run(test_main_page_service())