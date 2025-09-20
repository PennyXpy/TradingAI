# Main API Routes - Updated to use Polygon.io WebSocket and REST APIs
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from services.polygon_rest_service import get_polygon_rest_service
from services.polygon_websocket_service import get_polygon_service
from agents.real_data_tools import RealNewsAnalysisTool
from pydantic import BaseModel

# Response models for Swagger documentation
class StockData(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    timestamp: str
    source: str

class NewsArticle(BaseModel):
    title: str
    summary: str
    source: str
    published_at: str
    sentiment: float
    url: Optional[str] = None

class MarketIndex(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    timestamp: str

class CryptoData(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: str
    source: str

router = APIRouter()

# Mock market indexes data
MOCK_MARKET_INDEXES = {
    "SPY": {"name": "SPDR S&P 500 ETF", "price": 450.25, "change": 3.75, "change_percent": 0.84},
    "QQQ": {"name": "Invesco QQQ Trust", "price": 380.60, "change": -2.15, "change_percent": -0.56},
    "DIA": {"name": "SPDR Dow Jones Industrial Average ETF", "price": 340.80, "change": 1.20, "change_percent": 0.35},
    "IWM": {"name": "iShares Russell 2000 ETF", "price": 195.45, "change": 2.85, "change_percent": 1.48}
}

@router.get(
    "/market/indexes",
    summary="Get Market Indexes",
    description="Retrieve major market indexes (SPY, QQQ, DIA, IWM) with real-time data from Polygon.io",
    response_model=Dict[str, Any],
    tags=["Market Data"]
)
async def market_indexes():
    """
    **Get Major Market Indexes**
    
    Returns real-time data for major market indexes including:
    - SPY (S&P 500 ETF)
    - QQQ (NASDAQ ETF) 
    - DIA (Dow Jones ETF)
    - IWM (Russell 2000 ETF)
    
    **Data Source**: Polygon.io (real-time or 15-min delayed based on subscription)
    """
    polygon_service = await get_polygon_rest_service()
    indexes_data = await polygon_service.get_market_indexes()
    
    # Get real-time updates from WebSocket service if available
    websocket_service = await get_polygon_service()
    for index in indexes_data:
        latest_data = websocket_service.get_latest_data(index["symbol"])
        if latest_data:
            index.update(latest_data)
    
    return {"indexes": indexes_data, "last_updated": datetime.now().isoformat()}

@router.get(
    "/stocks/top",
    summary="Get Top Performing Stocks",
    description="Retrieve top performing stocks with real-time data from Polygon.io",
    response_model=Dict[str, Any],
    tags=["Market Data"]
)
async def top_stocks(limit: int = Query(5, ge=1, le=10, description="Number of stocks to return (1-10)")):
    """
    **Get Top Performing Stocks**
    
    Returns real-time data for popular stocks including:
    - Current price and daily change
    - Volume and market capitalization
    - Technical indicators
    
    **Data Source**: Polygon.io
    """
    polygon_service = await get_polygon_rest_service()
    stocks = await polygon_service.get_top_stocks(limit)
    
    # Get real-time updates from WebSocket service if available
    websocket_service = await get_polygon_service()
    for stock in stocks:
        latest_data = websocket_service.get_latest_data(stock["symbol"])
        if latest_data:
            stock.update(latest_data)
    
    return {"stocks": stocks, "count": len(stocks)}

@router.get(
    "/cryptos/top",
    summary="Get Top Cryptocurrencies",
    description="Retrieve top cryptocurrencies with real-time data from Polygon.io",
    response_model=Dict[str, Any],
    tags=["Market Data"]
)
async def top_cryptos(limit: int = Query(5, ge=1, le=10, description="Number of cryptocurrencies to return (1-10)")):
    """
    **Get Top Cryptocurrencies**
    
    Returns real-time data for popular cryptocurrencies including:
    - BTC, ETH, SOL, ADA, DOT
    - Current price and daily change
    - Volume and market cap data
    
    **Data Source**: Polygon.io
    """
    market_tool = RealMarketDataTool()
    
    # Get data for popular cryptocurrencies
    popular_cryptos = ["BTC", "ETH", "SOL", "ADA", "DOT"][:limit]
    cryptos = []
    
    for symbol in popular_cryptos:
        crypto_data = await market_tool.get_crypto_data(symbol)
        if "error" not in crypto_data:
            cryptos.append(crypto_data)
    
    return {"cryptos": cryptos, "count": len(cryptos)}

@router.get(
    "/stocks/search",
    summary="Search Stocks",
    description="Search for stocks by symbol or company name using Polygon.io API",
    response_model=Dict[str, Any],
    tags=["Market Data"]
)
async def search_stocks(query: str = Query(..., min_length=1, description="Stock symbol or company name to search for"), limit: int = Query(10, ge=1, le=50, description="Number of results to return")):
    """
    **Search Stocks**
    
    Search for stocks by:
    - Stock symbol (e.g., AAPL, GOOGL)
    - Company name (partial matches supported)
    
    Returns matching stocks with current price data from Polygon.io.
    """
    polygon_service = await get_polygon_rest_service()
    results = await polygon_service.search_stocks(query, limit)
    
    # Get real-time price data for search results
    websocket_service = await get_polygon_service()
    enhanced_results = []
    
    for stock in results:
        # Get current stock details
        stock_details = await polygon_service.get_stock_details(stock["symbol"])
        
        # Add real-time data if available
        latest_data = websocket_service.get_latest_data(stock["symbol"])
        if latest_data:
            stock_details.update(latest_data)
        
        enhanced_results.append({
            "symbol": stock_details["symbol"],
            "name": stock_details["name"],
            "price": stock_details.get("price", 0),
            "change": stock_details.get("change", 0),
            "change_percent": stock_details.get("change_percent", 0),
            "market": stock_details.get("market", "stocks"),
            "type": stock_details.get("type", ""),
            "active": stock.get("active", True)
        })
    
    return {"results": enhanced_results, "query": query, "count": len(enhanced_results)}

@router.get(
    "/stocks/{symbol}",
    summary="Get Stock Details",
    description="Get detailed information for a specific stock symbol using Polygon.io",
    response_model=Dict[str, Any],
    tags=["Market Data"]
)
async def get_stock_details(symbol: str):
    """
    **Get Detailed Stock Information**
    
    Returns comprehensive data for a specific stock including:
    - Real-time price and daily changes
    - Volume and market capitalization  
    - Company information and market data
    
    **Parameters**:
    - symbol: Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)
    
    **Data Source**: Polygon.io
    """
    polygon_service = await get_polygon_rest_service()
    stock_data = await polygon_service.get_stock_details(symbol.upper())
    
    if "error" in stock_data:
        raise HTTPException(status_code=404, detail=stock_data["error"])
    
    # Get real-time updates from WebSocket service if available
    websocket_service = await get_polygon_service()
    latest_data = websocket_service.get_latest_data(symbol.upper())
    if latest_data:
        stock_data.update(latest_data)
    
    return {"stock": stock_data}

@router.get("/cryptos/{symbol}")
async def get_crypto_details(symbol: str):
    """
    获取加密货币详细信息 - Uses real data from Polygon.io
    """
    market_tool = RealMarketDataTool()
    crypto_data = await market_tool.get_crypto_data(symbol.upper())
    
    if "error" in crypto_data:
        return {"error": crypto_data["error"]}
    
    return {"crypto": crypto_data}

@router.get(
    "/news/latest",
    summary="Get Latest Financial News",
    description="Retrieve latest financial and market news with sentiment analysis",
    response_model=Dict[str, Any],
    tags=["News & Analysis"]
)
async def get_latest_news(limit: int = Query(10, ge=1, le=50, description="Number of news articles to return (1-50)")):
    """
    **Get Latest Financial News**
    
    Returns recent financial news with:
    - Article title, summary, and content
    - Publication date and source
    - AI-powered sentiment analysis
    - Relevance scoring
    
    **Data Source**: NewsAPI
    """
    news_tool = RealNewsAnalysisTool()
    articles = await news_tool.get_market_news(limit=limit)
    
    news_items = []
    for i, article in enumerate(articles):
        news_items.append({
            "id": f"news_{i+1}",
            "title": article["title"],
            "summary": article["summary"],
            "content": article["content"],
            "published_at": article["published_at"],
            "source": article["source"],
            "author": article["author"],
            "url": article["url"],
            "sentiment": article["sentiment"]
        })
    
    return {"news": news_items, "count": len(news_items)}

@router.get(
    "/news/stock/{symbol}",
    summary="Get Stock-Specific News",
    description="Get news articles related to a specific stock symbol",
    response_model=Dict[str, Any],
    tags=["News & Analysis"]
)
async def get_stock_news(symbol: str, limit: int = Query(5, ge=1, le=20, description="Number of news articles to return (1-20)")):
    """
    **Get Stock-Specific News**
    
    Returns news articles specifically related to a stock including:
    - Company-specific news and announcements
    - Earnings reports and analyst updates
    - Market impact analysis
    - Sentiment scoring for each article
    
    **Parameters**:
    - symbol: Stock ticker symbol (e.g., AAPL, GOOGL)
    
    **Data Source**: NewsAPI
    """
    news_tool = RealNewsAnalysisTool()
    articles = await news_tool.get_news_for_symbol(symbol.upper(), limit=limit)
    
    news_items = []
    for i, article in enumerate(articles):
        news_items.append({
            "id": f"stock_news_{symbol}_{i+1}",
            "symbol": symbol.upper(),
            "title": article["title"],
            "summary": article["summary"],
            "content": article["content"],
            "published_at": article["published_at"],
            "source": article["source"],
            "author": article["author"],
            "url": article["url"],
            "sentiment": article["sentiment"],
            "relevance_score": round(0.9 - (i * 0.1), 2)  # Decreasing relevance
        })
    
    return {"news": news_items, "symbol": symbol.upper(), "count": len(news_items)}

@router.get("/stocks/{symbol}/history")
async def get_stock_history(
    symbol: str, 
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    interval: str = Query("1d", regex="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$")
):
    """
    获取股票历史数据
    """
    symbol = symbol.upper()
    if symbol not in MOCK_STOCK_DATA:
        return {"error": f"Stock {symbol} not found"}
    
    # Generate mock historical data
    import random
    current_price = MOCK_STOCK_DATA[symbol]["price"]
    
    # Determine number of data points based on period
    period_days = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
    days = period_days.get(period, 30)
    
    history = []
    base_price = current_price
    
    for i in range(days, 0, -1):
        # Generate realistic price movement
        price_change = random.uniform(-0.05, 0.05)  # +/- 5% max daily change
        price = base_price * (1 + price_change)
        
        history.append({
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "open": round(price * random.uniform(0.99, 1.01), 2),
            "high": round(price * random.uniform(1.01, 1.03), 2),
            "low": round(price * random.uniform(0.97, 0.99), 2),
            "close": round(price, 2),
            "volume": int(MOCK_STOCK_DATA[symbol]["volume"] * random.uniform(0.8, 1.2))
        })
        
        base_price = price * random.uniform(0.98, 1.02)  # Slight trend
    
    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "history": history,
        "count": len(history)
    }

@router.get(
    "/health",
    summary="API Health Check",
    description="Check the health status of the TradingAI API",
    response_model=Dict[str, Any],
    tags=["System"]
)
async def health_check():
    """
    **API Health Check**
    
    Returns the current health status of the API including:
    - API version and status
    - Data source information
    - Timestamp of last check
    
    Use this endpoint to verify the API is running correctly.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "data_source": "mock_data"
    }