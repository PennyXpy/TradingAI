# AI Chat API Routes
# This module provides FastAPI endpoints for AI chat functionality
# Following the new architecture: API-first, then @agent.tool integration
#
# Key features:
# - API endpoints for UI display (main page, dashboard)
# - Data storage/caching for agent reuse
# - Shared utility functions that can be used as @agent.tool
# - Performance optimization through intelligent caching

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from sqlmodel import Session
import json

# Import database and models
from models.core_models import User, UserFollowing, Instrument, NewsArticle, MarketCache
from models.ai_models import ChatSession, AgentRecommendation, TradingInsight
from data import get_session

# Import agent system
from agents.ai_trading_agent import AITradingAgent, create_ai_trading_agent
from agents.context import AgentContextManager, extract_user_id_from_token

# ================================================================================
# PYDANTIC MODELS FOR API REQUESTS/RESPONSES
# ================================================================================

class ChatMessage(BaseModel):
    """Chat message from user"""
    message: str
    session_id: Optional[str] = None
    symbols: List[str] = []

class ChatResponse(BaseModel):
    """AI chat response"""
    id: str
    content: str
    response_type: str
    data: Optional[Dict[str, Any]] = None
    suggested_actions: List[str] = []
    related_symbols: List[str] = []
    confidence: float
    timestamp: datetime
    session_id: Optional[str] = None

class MarketDataResponse(BaseModel):
    """Market data for main page/dashboard"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    is_positive: bool
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    last_updated: datetime

class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary for dashboard"""
    total_value: float
    total_cost: float
    total_return: float
    total_return_percent: float
    day_change: float
    day_change_percent: float
    position_count: int
    followed_count: int
    top_holdings: List[str]
    asset_breakdown: Dict[str, int]
    last_updated: datetime

class NewsResponse(BaseModel):
    """News data for main page"""
    id: str
    headline: str
    summary: Optional[str] = None
    category: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    sentiment_score: Optional[float] = None
    symbols: List[str] = []

# ================================================================================
# SHARED UTILITY FUNCTIONS (Used by both APIs and @agent.tool)
# ================================================================================

def get_top_stocks_data(limit: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Get top stocks data - shared between main page API and agent tool
    
    Args:
        limit: Number of stocks to return
        use_cache: Whether to use cached data
        
    Returns:
        List of stock data dictionaries
    """
    # This function will be used by both:
    # 1. GET /api/stocks/top (for main page display)
    # 2. @agent.tool get_top_stocks (for agent access)
    
    # Mock data for now - replace with actual market data
    top_stocks = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "price": 175.50,
            "change": 2.5,
            "change_percent": 1.44,
            "is_positive": True,
            "volume": 45000000,
            "market_cap": 2800000000000
        },
        {
            "symbol": "MSFT", 
            "name": "Microsoft Corporation",
            "price": 420.25,
            "change": -1.75,
            "change_percent": -0.41,
            "is_positive": False,
            "volume": 25000000,
            "market_cap": 3100000000000
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "price": 142.80,
            "change": 3.20,
            "change_percent": 2.29,
            "is_positive": True,
            "volume": 22000000,
            "market_cap": 1800000000000
        },
        {
            "symbol": "AMZN",
            "name": "Amazon.com Inc.",
            "price": 155.75,
            "change": 0.95,
            "change_percent": 0.61,
            "is_positive": True,
            "volume": 35000000,
            "market_cap": 1600000000000
        },
        {
            "symbol": "TSLA",
            "name": "Tesla Inc.",
            "price": 248.50,
            "change": -4.25,
            "change_percent": -1.68,
            "is_positive": False,
            "volume": 55000000,
            "market_cap": 790000000000
        }
    ]
    
    return top_stocks[:limit]

def get_portfolio_summary_data(user_id: str, db: Session, use_cache: bool = True) -> Dict[str, Any]:
    """
    Get portfolio summary - shared between dashboard API and agent tool
    
    Args:
        user_id: User ID
        db: Database session
        use_cache: Whether to use cached data
        
    Returns:
        Portfolio summary dictionary
    """
    # This function will be used by both:
    # 1. GET /api/portfolio/summary (for dashboard display)
    # 2. @agent.tool analyze_portfolio (for agent access)
    
    # Mock portfolio data for now - replace with actual portfolio calculations
    portfolio_summary = {
        "total_value": 25750.50,
        "total_cost": 23000.00,
        "total_return": 2750.50,
        "total_return_percent": 11.96,
        "day_change": 125.75,
        "day_change_percent": 0.49,
        "position_count": 8,
        "followed_count": 12,
        "top_holdings": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        "asset_breakdown": {"stocks": 6, "etfs": 2, "crypto": 0},
        "last_updated": datetime.now()
    }
    
    return portfolio_summary

def get_latest_news_data(limit: int = 6, category: str = "all", use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Get latest financial news - shared between main page API and agent tool
    
    Args:
        limit: Number of articles to return
        category: News category filter
        use_cache: Whether to use cached data
        
    Returns:
        List of news article dictionaries
    """
    # This function will be used by both:
    # 1. GET /api/news/latest (for main page display)
    # 2. @agent.tool get_market_news (for agent access)
    
    # Mock news data for now - replace with actual news fetching
    news_articles = [
        {
            "id": "news_1",
            "headline": "Tech Stocks Rally on Strong Earnings",
            "summary": "Major technology companies report better-than-expected quarterly results, driving sector gains.",
            "category": "Market Update",
            "source": "Financial Times",
            "published_at": datetime.now(),
            "url": "https://example.com/news/1",
            "sentiment_score": 0.75,
            "symbols": ["AAPL", "MSFT", "GOOGL"]
        },
        {
            "id": "news_2", 
            "headline": "Federal Reserve Signals Pause in Rate Hikes",
            "summary": "Fed officials indicate they may hold rates steady in upcoming meetings amid cooling inflation.",
            "category": "Economic Policy",
            "source": "Reuters",
            "published_at": datetime.now(),
            "url": "https://example.com/news/2",
            "sentiment_score": 0.45,
            "symbols": ["SPY", "QQQ", "DIA"]
        },
        {
            "id": "news_3",
            "headline": "Electric Vehicle Sales Show Strong Growth",
            "summary": "EV manufacturers report record quarterly sales, boosting investor confidence in the sector.",
            "category": "Industry News",
            "source": "Bloomberg",
            "published_at": datetime.now(),
            "url": "https://example.com/news/3", 
            "sentiment_score": 0.65,
            "symbols": ["TSLA", "RIVN", "LCID"]
        },
        {
            "id": "news_4",
            "headline": "Healthcare Sector Faces Regulatory Challenges",
            "summary": "New regulatory proposals could impact pharmaceutical and biotech companies.",
            "category": "Healthcare",
            "source": "Wall Street Journal",
            "published_at": datetime.now(),
            "url": "https://example.com/news/4",
            "sentiment_score": -0.25,
            "symbols": ["JNJ", "PFE", "ABBV"]
        },
        {
            "id": "news_5",
            "headline": "Oil Prices Stabilize After Recent Volatility",
            "summary": "Energy markets show signs of stabilization following weeks of price fluctuations.",
            "category": "Energy",
            "source": "CNBC",
            "published_at": datetime.now(),
            "url": "https://example.com/news/5",
            "sentiment_score": 0.15,
            "symbols": ["XOM", "CVX", "COP"]
        },
        {
            "id": "news_6",
            "headline": "Banking Sector Prepares for Stress Tests",
            "summary": "Major banks gear up for annual regulatory stress testing amid economic uncertainty.",
            "category": "Financial Services",
            "source": "MarketWatch",
            "published_at": datetime.now(),
            "url": "https://example.com/news/6",
            "sentiment_score": -0.05,
            "symbols": ["JPM", "BAC", "WFC"]
        }
    ]
    
    return news_articles[:limit]

def get_stock_price_data(symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Get individual stock price - shared between APIs and agent tools
    
    Args:
        symbol: Stock symbol
        use_cache: Whether to use cached data
        
    Returns:
        Stock price data dictionary or None
    """
    # Mock price data - replace with actual market data fetching
    mock_prices = {
        "AAPL": {"price": 175.50, "change": 2.5, "change_percent": 1.44},
        "MSFT": {"price": 420.25, "change": -1.75, "change_percent": -0.41},
        "GOOGL": {"price": 142.80, "change": 3.20, "change_percent": 2.29},
        "AMZN": {"price": 155.75, "change": 0.95, "change_percent": 0.61},
        "TSLA": {"price": 248.50, "change": -4.25, "change_percent": -1.68},
    }
    
    if symbol.upper() in mock_prices:
        data = mock_prices[symbol.upper()]
        return {
            "symbol": symbol.upper(),
            "name": f"{symbol.upper()} Company",
            "price": data["price"],
            "change": data["change"],
            "change_percent": data["change_percent"],
            "is_positive": data["change"] > 0,
            "volume": 1000000,
            "market_cap": 1000000000,
            "last_updated": datetime.now()
        }
    
    return None

# ================================================================================
# AUTHENTICATION HELPER
# ================================================================================

def get_current_user_id(authorization: str = Header(None), db: Session = Depends(get_session)) -> str:
    """Extract user ID from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token from "Bearer <token>"
    try:
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = extract_user_id_from_token(token, db)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user_id
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

# ================================================================================
# FASTAPI ROUTER SETUP
# ================================================================================

router = APIRouter(prefix="/api", tags=["ai-chat"])

# Global agent instance (will be initialized with API key)
_global_agent: Optional[AITradingAgent] = None

def get_agent() -> AITradingAgent:
    """Get or create global trading agent instance"""
    global _global_agent
    if _global_agent is None:
        _global_agent = create_ai_trading_agent()
    return _global_agent

# ================================================================================
# API ENDPOINTS FOR UI DISPLAY (Main Page & Dashboard)
# ================================================================================

@router.get("/stocks/top", response_model=List[MarketDataResponse])
async def get_top_stocks(limit: int = 10):
    """Get top performing stocks for main page display"""
    try:
        stocks_data = get_top_stocks_data(limit=limit)
        
        # Convert to response model
        response = []
        for stock in stocks_data:
            response.append(MarketDataResponse(
                symbol=stock["symbol"],
                name=stock["name"],
                price=stock["price"],
                change=stock["change"],
                change_percent=stock["change_percent"],
                is_positive=stock["is_positive"],
                volume=stock.get("volume"),
                market_cap=stock.get("market_cap"),
                last_updated=datetime.now()
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top stocks: {str(e)}")

@router.get("/stocks/{symbol}/price", response_model=MarketDataResponse)
async def get_stock_price(symbol: str):
    """Get individual stock price"""
    try:
        price_data = get_stock_price_data(symbol)
        
        if not price_data:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        return MarketDataResponse(**price_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock price: {str(e)}")

@router.get("/portfolio/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """Get portfolio summary for dashboard display"""
    try:
        portfolio_data = get_portfolio_summary_data(user_id, db)
        
        return PortfolioSummaryResponse(**portfolio_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")

@router.get("/news/latest", response_model=List[NewsResponse])
async def get_latest_news(limit: int = 6, category: str = "all"):
    """Get latest financial news for main page display"""
    try:
        news_data = get_latest_news_data(limit=limit, category=category)
        
        # Convert to response model
        response = []
        for article in news_data:
            response.append(NewsResponse(**article))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

# ================================================================================
# AI CHAT ENDPOINTS
# ================================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    message: ChatMessage,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """Main AI chat endpoint"""
    try:
        # Create context manager for user
        context_manager = AgentContextManager(db, user_id)
        
        # Get agent instance
        agent = get_agent()
        
        # Create agent query
        from agents.trading_agent import AgentQuery
        agent_query = AgentQuery(
            message=message.message,
            session_id=message.session_id,
            context_symbols=message.symbols
        )
        
        # Process query with agent
        response = await agent.process_query(agent_query, context_manager)
        
        # Convert to API response format
        chat_response = ChatResponse(
            id=f"chat_{datetime.now().timestamp()}",
            content=response.content,
            response_type=response.response_type,
            data=response.data,
            suggested_actions=response.suggested_actions,
            related_symbols=response.related_symbols,
            confidence=response.confidence,
            timestamp=response.timestamp,
            session_id=message.session_id
        )
        
        return chat_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.get("/chat/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """Get chat history for a user"""
    try:
        # This would retrieve actual chat history from database
        # For now, return empty list
        return {"history": [], "total": 0}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@router.delete("/chat/history")
async def clear_chat_history(
    session_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_session)
):
    """Clear chat history for a user"""
    try:
        # This would clear actual chat history from database
        return {"message": "Chat history cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")

# ================================================================================
# AGENT TOOLS (Using @agent.tool decorator with shared functions)
# ================================================================================

def register_agent_tools(agent: AITradingAgent):
    """
    Register tools with the agent using the shared utility functions
    This demonstrates the new architecture where tools use the same data as APIs
    """
    if not agent.agent:
        return
    
    @agent.agent.tool
    async def get_top_stocks(ctx, limit: int = 10) -> Dict[str, Any]:
        """Get top performing stocks data"""
        try:
            stocks_data = get_top_stocks_data(limit=limit, use_cache=True)
            return {
                "success": True,
                "data": stocks_data,
                "tool_name": "get_top_stocks"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": "get_top_stocks"
            }
    
    @agent.agent.tool
    async def get_stock_price(ctx, symbol: str) -> Dict[str, Any]:
        """Get current stock price"""
        try:
            price_data = get_stock_price_data(symbol, use_cache=True)
            return {
                "success": True,
                "data": price_data,
                "tool_name": "get_stock_price"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": "get_stock_price"
            }
    
    @agent.agent.tool
    async def analyze_user_portfolio(ctx) -> Dict[str, Any]:
        """Analyze user's portfolio performance"""
        try:
            # Get database session from context (would need to be passed in)
            # For now, use mock data
            portfolio_data = get_portfolio_summary_data(ctx.deps.user_id, None, use_cache=True)
            return {
                "success": True,
                "data": portfolio_data,
                "tool_name": "analyze_user_portfolio"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": "analyze_user_portfolio"
            }
    
    @agent.agent.tool
    async def get_market_news(ctx, limit: int = 10, category: str = "all") -> Dict[str, Any]:
        """Get latest market news"""
        try:
            news_data = get_latest_news_data(limit=limit, category=category, use_cache=True)
            return {
                "success": True,
                "data": news_data,
                "tool_name": "get_market_news"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": "get_market_news"
            }

# Initialize agent tools when module is imported
def initialize_agent_tools():
    """Initialize agent tools with shared functions"""
    agent = get_agent()
    register_agent_tools(agent)

# Call initialization
try:
    initialize_agent_tools()
except Exception as e:
    print(f"Warning: Could not initialize agent tools: {e}")

# ================================================================================
# TESTING ENDPOINTS (Development only)
# ================================================================================

@router.get("/test/agent-status")
async def test_agent_status():
    """Test endpoint to check agent status"""
    agent = get_agent()
    return {
        "agent_available": agent.agent is not None,
        "model_name": agent.model_name,
        "api_key_configured": agent.api_key is not None,
        "timestamp": datetime.now()
    }