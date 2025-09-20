# Real Data Agent Tools - Using Polygon.io and NewsAPI
# This module provides agent tools that use real APIs instead of mocked data

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from services.polygon_websocket import PolygonWebSocketClient, StockQuote, StockAggregate
from services.news_api_client import NewsAPIClient

logger = logging.getLogger(__name__)

class RealMarketDataTool:
    """Tool for retrieving real market data from Polygon.io"""
    
    def __init__(self):
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.polygon_base_url = "https://api.polygon.io"
        
        if not self.polygon_api_key:
            logger.warning("POLYGON_API_KEY not found. Using fallback mock data.")
            self.use_fallback = True
        else:
            self.use_fallback = False
    
    async def _make_polygon_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to Polygon.io REST API"""
        if self.use_fallback:
            return {"error": "No API key configured"}
            
        url = f"{self.polygon_base_url}{endpoint}"
        params = params or {}
        params["apikey"] = self.polygon_api_key
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if data.get("status") == "ERROR":
                        logger.error(f"Polygon API error: {data.get('error', 'Unknown error')}")
                        return {"error": data.get("error", "API error")}
                        
                    return data
                    
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error calling Polygon API: {e}")
                return {"error": f"HTTP error: {e}"}
            except Exception as e:
                logger.error(f"Error calling Polygon API: {e}")
                return {"error": f"Request error: {e}"}
    
    async def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock data from Polygon.io"""
        symbol = symbol.upper()
        
        if self.use_fallback:
            return await self._get_fallback_stock_data(symbol)
        
        try:
            # Get current price and daily data
            endpoint = f"/v2/aggs/ticker/{symbol}/prev"
            data = await self._make_polygon_request(endpoint)
            
            if "error" in data:
                return data
                
            if not data.get("results") or len(data["results"]) == 0:
                return {"error": f"No data available for {symbol}"}
                
            result = data["results"][0]
            
            # Calculate change from previous close
            current_price = result.get("c", 0)  # Close price
            open_price = result.get("o", 0)     # Open price
            change = current_price - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            # Get company name from ticker details
            ticker_details = await self._get_ticker_details(symbol)
            company_name = ticker_details.get("name", f"{symbol} Inc.")
            
            stock_data = {
                "symbol": symbol,
                "name": company_name,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": result.get("v", 0),
                "open": result.get("o", 0),
                "high": result.get("h", 0),
                "low": result.get("l", 0),
                "close": result.get("c", 0),
                "vwap": result.get("vw", 0),
                "market_cap": ticker_details.get("market_cap", 0),
                "timestamp": datetime.now().isoformat(),
                "source": "polygon.io"
            }
            
            # Add technical indicators (simplified - would normally require historical data)
            stock_data["technical_indicators"] = {
                "rsi": await self._calculate_rsi(symbol),
                "sma_20": round(current_price * 0.99, 2),  # Simplified
                "sma_50": round(current_price * 0.98, 2),  # Simplified
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {e}")
            return {"error": f"Failed to get stock data: {e}"}
    
    async def _get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Get ticker details from Polygon.io"""
        endpoint = f"/v3/reference/tickers/{symbol}"
        data = await self._make_polygon_request(endpoint)
        
        if "error" in data:
            return {}
            
        results = data.get("results", {})
        return {
            "name": results.get("name", f"{symbol} Inc."),
            "market_cap": results.get("market_cap", 0),
            "description": results.get("description", ""),
            "homepage_url": results.get("homepage_url", ""),
            "sector": results.get("sic_description", "")
        }
    
    async def _calculate_rsi(self, symbol: str, period: int = 14) -> float:
        """Calculate RSI using historical data (simplified version)"""
        try:
            # Get last 30 days of data
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
            data = await self._make_polygon_request(endpoint)
            
            if "error" in data or not data.get("results"):
                return 50.0  # Neutral RSI as fallback
                
            # Simplified RSI calculation
            closes = [r["c"] for r in data["results"][-period:]]
            if len(closes) < period:
                return 50.0
                
            gains = []
            losses = []
            
            for i in range(1, len(closes)):
                change = closes[i] - closes[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0.01
            
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception:
            return 50.0  # Neutral RSI as fallback
    
    async def get_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Get cryptocurrency data from Polygon.io"""
        symbol = symbol.upper()
        crypto_symbol = f"X:{symbol}USD"  # Polygon crypto format
        
        if self.use_fallback:
            return await self._get_fallback_crypto_data(symbol)
        
        try:
            endpoint = f"/v2/aggs/ticker/{crypto_symbol}/prev"
            data = await self._make_polygon_request(endpoint)
            
            if "error" in data:
                return data
                
            if not data.get("results") or len(data["results"]) == 0:
                return {"error": f"No crypto data available for {symbol}"}
                
            result = data["results"][0]
            
            current_price = result.get("c", 0)
            open_price = result.get("o", 0)
            change = current_price - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            crypto_data = {
                "symbol": symbol,
                "name": f"{symbol} Cryptocurrency",
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": result.get("v", 0),
                "open": result.get("o", 0),
                "high": result.get("h", 0),
                "low": result.get("l", 0),
                "close": result.get("c", 0),
                "vwap": result.get("vw", 0),
                "timestamp": datetime.now().isoformat(),
                "source": "polygon.io"
            }
            
            return crypto_data
            
        except Exception as e:
            logger.error(f"Error getting crypto data for {symbol}: {e}")
            return {"error": f"Failed to get crypto data: {e}"}
    
    async def get_market_indexes(self) -> List[Dict[str, Any]]:
        """Get major market indexes from Polygon.io"""
        indexes = ["SPY", "QQQ", "DIA", "IWM"]  # Major ETFs representing indexes
        index_data = []
        
        for symbol in indexes:
            data = await self.get_stock_data(symbol)
            if "error" not in data:
                index_data.append(data)
        
        return index_data
    
    async def _get_fallback_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback to mock data when API key is not available"""
        from agents.tools import MOCK_STOCK_DATA
        if symbol in MOCK_STOCK_DATA:
            data = MOCK_STOCK_DATA[symbol].copy()
            data["source"] = "fallback_mock"
            data["timestamp"] = datetime.now().isoformat()
            return data
        return {"error": f"No fallback data for {symbol}"}
    
    async def _get_fallback_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback to mock crypto data when API key is not available"""
        from agents.tools import MOCK_CRYPTO_DATA
        if symbol in MOCK_CRYPTO_DATA:
            data = MOCK_CRYPTO_DATA[symbol].copy()
            data["source"] = "fallback_mock"
            data["timestamp"] = datetime.now().isoformat()
            return data
        return {"error": f"No fallback crypto data for {symbol}"}


class RealNewsAnalysisTool:
    """Tool for retrieving real financial news from NewsAPI"""
    
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        
        if not self.news_api_key:
            logger.warning("NEWS_API_KEY not found. Using fallback mock data.")
            self.use_fallback = True
        else:
            self.use_fallback = False
    
    async def get_news_for_symbol(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get real news for a specific stock symbol"""
        if self.use_fallback:
            return await self._get_fallback_news(symbol, limit)
        
        try:
            async with NewsAPIClient(self.news_api_key) as client:
                articles = await client.get_company_news(
                    company_name=symbol,
                    symbol=symbol,
                    limit=limit,
                    days_back=7
                )
                
                news_data = []
                for article in articles:
                    news_data.append({
                        "title": article.title,
                        "summary": article.description or article.title,
                        "content": article.content,
                        "url": article.url,
                        "source": article.source_name,
                        "author": article.author,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "symbol": symbol,
                        "sentiment": await self._analyze_sentiment(article.title + " " + (article.description or "")),
                        "data_source": "newsapi.org"
                    })
                
                return news_data
                
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {e}")
            return await self._get_fallback_news(symbol, limit)
    
    async def get_market_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get general market news"""
        if self.use_fallback:
            return await self._get_fallback_market_news(limit)
        
        try:
            async with NewsAPIClient(self.news_api_key) as client:
                articles = await client.get_market_news(limit=limit)
                
                news_data = []
                for article in articles:
                    news_data.append({
                        "title": article.title,
                        "summary": article.description or article.title,
                        "content": article.content,
                        "url": article.url,
                        "source": article.source_name,
                        "author": article.author,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "sentiment": await self._analyze_sentiment(article.title + " " + (article.description or "")),
                        "data_source": "newsapi.org"
                    })
                
                return news_data
                
        except Exception as e:
            logger.error(f"Error getting market news: {e}")
            return await self._get_fallback_market_news(limit)
    
    async def get_financial_news(self, symbols: List[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """Get financial news for specific symbols or general financial news"""
        if self.use_fallback:
            return await self._get_fallback_market_news(limit)
        
        try:
            async with NewsAPIClient(self.news_api_key) as client:
                articles = await client.get_financial_news(
                    symbols=symbols,
                    limit=limit,
                    days_back=3
                )
                
                news_data = []
                for article in articles:
                    news_data.append({
                        "title": article.title,
                        "summary": article.description or article.title,
                        "content": article.content,
                        "url": article.url,
                        "source": article.source_name,
                        "author": article.author,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "symbols": symbols or [],
                        "sentiment": await self._analyze_sentiment(article.title + " " + (article.description or "")),
                        "data_source": "newsapi.org"
                    })
                
                return news_data
                
        except Exception as e:
            logger.error(f"Error getting financial news: {e}")
            return await self._get_fallback_market_news(limit)
    
    async def summarize_news(self, news_articles: List[Dict[str, Any]]) -> str:
        """Summarize news articles using sentiment analysis"""
        if not news_articles:
            return "No news articles to summarize."
        
        # Analyze sentiment distribution
        sentiments = [article.get("sentiment", 0.5) for article in news_articles]
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        positive_count = sum(1 for s in sentiments if s > 0.6)
        negative_count = sum(1 for s in sentiments if s < 0.4)
        neutral_count = len(sentiments) - positive_count - negative_count
        
        # Extract key themes from titles
        titles = [article.get("title", "") for article in news_articles]
        common_words = self._extract_common_themes(titles)
        
        # Generate summary
        if avg_sentiment > 0.6:
            sentiment_desc = "predominantly positive"
        elif avg_sentiment < 0.4:
            sentiment_desc = "predominantly negative"
        else:
            sentiment_desc = "mixed"
        
        summary = f"Analysis of {len(news_articles)} recent articles shows {sentiment_desc} sentiment "
        summary += f"({positive_count} positive, {neutral_count} neutral, {negative_count} negative). "
        
        if common_words:
            summary += f"Key themes include: {', '.join(common_words[:5])}. "
        
        # Add market implications
        if avg_sentiment > 0.6:
            summary += "Overall news sentiment suggests optimism in the market."
        elif avg_sentiment < 0.4:
            summary += "Current news cycle indicates caution and potential market concerns."
        else:
            summary += "News sentiment is balanced with mixed market signals."
        
        return summary
    
    async def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (would normally use AI/ML model)"""
        if not text:
            return 0.5
        
        text = text.lower()
        
        # Positive words
        positive_words = [
            "gain", "rise", "surge", "rally", "bullish", "positive", "growth", 
            "increase", "strong", "beat", "exceed", "outperform", "profit",
            "earnings", "revenue", "upgrade", "buy", "optimistic"
        ]
        
        # Negative words
        negative_words = [
            "fall", "drop", "decline", "bearish", "negative", "loss", "decrease",
            "weak", "miss", "underperform", "sell", "downgrade", "pessimistic",
            "concern", "worry", "risk", "volatility", "uncertainty"
        ]
        
        positive_score = sum(1 for word in positive_words if word in text)
        negative_score = sum(1 for word in negative_words if word in text)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.5
        
        sentiment = 0.5 + (positive_score - negative_score) / (total_words * 2)
        return max(0.0, min(1.0, sentiment))  # Clamp between 0 and 1
    
    def _extract_common_themes(self, titles: List[str]) -> List[str]:
        """Extract common themes from news titles"""
        if not titles:
            return []
        
        # Common financial terms
        financial_terms = [
            "earnings", "revenue", "profit", "market", "stock", "trading",
            "federal reserve", "interest rates", "inflation", "GDP", "employment",
            "tech", "technology", "AI", "artificial intelligence", "crypto", "bitcoin"
        ]
        
        all_text = " ".join(titles).lower()
        found_themes = [term for term in financial_terms if term in all_text]
        
        return found_themes[:5]  # Return top 5 themes
    
    async def _get_fallback_news(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback to mock news when API key is not available"""
        from agents.tools import MOCK_NEWS_DATA
        news_data = []
        for i, news in enumerate(MOCK_NEWS_DATA[:limit]):
            news_copy = news.copy()
            news_copy.update({
                "symbol": symbol,
                "published_at": (datetime.now() - timedelta(hours=i*2)).isoformat(),
                "source": "fallback_mock",
                "data_source": "fallback"
            })
            news_data.append(news_copy)
        return news_data
    
    async def _get_fallback_market_news(self, limit: int) -> List[Dict[str, Any]]:
        """Fallback to mock market news"""
        from agents.tools import MOCK_NEWS_DATA
        news_data = []
        for i, news in enumerate(MOCK_NEWS_DATA[:limit]):
            news_copy = news.copy()
            news_copy.update({
                "published_at": (datetime.now() - timedelta(hours=i*2)).isoformat(),
                "source": "fallback_mock",
                "data_source": "fallback"
            })
            news_data.append(news_copy)
        return news_data


# Portfolio and Analysis tools remain the same as they don't depend on external APIs
from agents.tools import PortfolioTool, AnalysisTool, AlertTool, RecommendationTool

# Example usage
async def test_real_apis():
    """Test the real API integrations"""
    logger.info("Testing real API integrations...")
    
    # Test market data
    market_tool = RealMarketDataTool()
    stock_data = await market_tool.get_stock_data("AAPL")
    print(f"Stock data: {stock_data}")
    
    # Test news
    news_tool = RealNewsAnalysisTool()
    news = await news_tool.get_news_for_symbol("AAPL", limit=3)
    print(f"News articles: {len(news)}")
    
    # Test market news
    market_news = await news_tool.get_market_news(limit=3)
    print(f"Market news: {len(market_news)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_real_apis())