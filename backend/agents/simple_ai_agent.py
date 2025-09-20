# Simple AI Trading Agent - OpenAI Direct Integration
# Temporary replacement for pydantic-ai due to Python 3.10 compatibility issues

import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from openai import AsyncOpenAI
from pydantic import BaseModel

# Import real data tools
from agents.real_data_tools import RealMarketDataTool, RealNewsAnalysisTool
from agents.tools import PortfolioTool, AnalysisTool, AlertTool, RecommendationTool

class UserContext(BaseModel):
    """User context for the AI agent"""
    user_id: str
    followed_symbols: List[str] = []
    risk_tolerance: str = "medium"
    investment_goals: List[str] = []
    portfolio_value: float = 0.0

class AIResponse(BaseModel):
    """AI agent response structure"""
    content: str
    tool_calls: List[Dict[str, Any]] = []
    context_used: Dict[str, Any] = {}
    timestamp: str = ""

class SimpleAITradingAgent:
    """
    Simple AI Trading Agent using OpenAI directly
    
    Features:
    - Market data analysis using real APIs
    - News sentiment analysis
    - Portfolio insights
    - Investment recommendations
    - Tool integration for enhanced responses
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Initialize tools
        self.market_tool = RealMarketDataTool()
        self.news_tool = RealNewsAnalysisTool()
        self.portfolio_tool = PortfolioTool()
        self.analysis_tool = AnalysisTool()
        self.alert_tool = AlertTool()
        self.recommendation_tool = RecommendationTool()
        
        # Tool registry
        self.tools = {
            "get_stock_data": self._get_stock_data,
            "get_crypto_data": self._get_crypto_data,
            "get_news_analysis": self._get_news_analysis,
            "get_market_news": self._get_market_news,
            "analyze_portfolio": self._analyze_portfolio,
            "get_technical_analysis": self._get_technical_analysis,
            "get_recommendation": self._get_recommendation,
            "check_alerts": self._check_alerts
        }
        
        # System prompt
        self.system_prompt = """You are TradingAI, an intelligent financial assistant specializing in stock market analysis, portfolio management, and investment guidance.

Key capabilities:
- Real-time stock and cryptocurrency analysis
- Financial news analysis with sentiment
- Portfolio performance evaluation
- Technical analysis and trading signals
- Personalized investment recommendations
- Market alerts and notifications

Guidelines:
- Always provide data-driven insights using real market data
- Include relevant financial metrics and technical indicators
- Consider user's risk tolerance and investment goals
- Explain complex financial concepts clearly
- Provide actionable recommendations with proper risk disclaimers
- Use emojis sparingly and only when appropriate

Available tools:
- get_stock_data(symbol): Get real-time stock data and technical indicators
- get_crypto_data(symbol): Get cryptocurrency data and analysis
- get_news_analysis(symbol): Get news sentiment for specific stocks
- get_market_news(): Get latest financial market news
- analyze_portfolio(portfolio_data): Analyze portfolio performance
- get_technical_analysis(symbol): Get detailed technical analysis
- get_recommendation(symbol, context): Get AI trading recommendations
- check_alerts(user_alerts): Check triggered price alerts

Remember to always include risk disclaimers and remind users that past performance doesn't guarantee future results."""
    
    async def process_message(self, message: str, user_context: UserContext) -> AIResponse:
        """Process user message and generate AI response with tool calls"""
        
        # Analyze message to determine which tools to use
        tool_calls = await self._determine_tools(message, user_context)
        
        # Execute tools and gather context
        tool_results = {}
        for tool_name, tool_args in tool_calls:
            try:
                result = await self.tools[tool_name](**tool_args)
                tool_results[tool_name] = result
            except Exception as e:
                tool_results[tool_name] = {"error": str(e)}
        
        # Generate AI response using OpenAI
        response_content = await self._generate_openai_response(
            message, user_context, tool_results
        )
        
        return AIResponse(
            content=response_content,
            tool_calls=[{"tool": name, "args": args, "result": tool_results.get(name)} 
                       for name, args in tool_calls],
            context_used={
                "user_context": user_context.model_dump(),
                "tools_used": list(tool_results.keys())
            },
            timestamp=datetime.now().isoformat()
        )
    
    async def _determine_tools(self, message: str, user_context: UserContext) -> List[tuple]:
        """Determine which tools to use based on message content"""
        message_lower = message.lower()
        tools_to_use = []
        
        # Extract symbols from message
        symbols = self._extract_symbols(message)
        
        # Stock data requests
        if any(word in message_lower for word in ["stock", "price", "quote", "performance"]):
            for symbol in symbols[:3]:  # Limit to 3 symbols
                tools_to_use.append(("get_stock_data", {"symbol": symbol}))
        
        # Crypto data requests
        if any(word in message_lower for word in ["crypto", "bitcoin", "ethereum", "btc", "eth"]):
            crypto_symbols = ["BTC", "ETH"] if not symbols else symbols[:2]
            for symbol in crypto_symbols:
                tools_to_use.append(("get_crypto_data", {"symbol": symbol}))
        
        # News analysis requests
        if any(word in message_lower for word in ["news", "sentiment", "analysis", "headlines"]):
            if symbols:
                tools_to_use.append(("get_news_analysis", {"symbol": symbols[0]}))
            else:
                tools_to_use.append(("get_market_news", {}))
        
        # Portfolio analysis requests
        if any(word in message_lower for word in ["portfolio", "holdings", "allocation"]):
            # Create mock portfolio data - in real app, this would come from user data
            mock_portfolio = {
                "total_value": user_context.portfolio_value,
                "positions": [
                    {"symbol": symbol, "quantity": 100, "current_value": 10000, "cost_basis": 9000, "return_percent": 11.1}
                    for symbol in user_context.followed_symbols[:3]
                ]
            }
            tools_to_use.append(("analyze_portfolio", {"portfolio_data": mock_portfolio}))
        
        # Technical analysis requests
        if any(word in message_lower for word in ["technical", "rsi", "macd", "moving average", "chart"]):
            for symbol in symbols[:2]:
                tools_to_use.append(("get_technical_analysis", {"symbol": symbol}))
        
        # Recommendation requests
        if any(word in message_lower for word in ["recommend", "should i buy", "investment advice", "trade"]):
            for symbol in symbols[:1]:  # One recommendation at a time
                tools_to_use.append(("get_recommendation", {
                    "symbol": symbol,
                    "user_context": user_context.model_dump()
                }))
        
        # Default: get market overview if no specific tools identified
        if not tools_to_use and not symbols:
            tools_to_use.append(("get_market_news", {}))
        
        return tools_to_use
    
    def _extract_symbols(self, message: str) -> List[str]:
        """Extract stock symbols from message"""
        # Common stock symbols
        known_symbols = [
            "AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMD", "META", "AMZN", 
            "NFLX", "CRM", "ORCL", "INTC", "IBM", "HPQ", "DELL",
            "BTC", "ETH", "SOL", "ADA", "DOT"
        ]
        
        message_upper = message.upper()
        found_symbols = []
        
        for symbol in known_symbols:
            if symbol in message_upper:
                found_symbols.append(symbol)
        
        return found_symbols
    
    async def _generate_openai_response(
        self, 
        message: str, 
        user_context: UserContext, 
        tool_results: Dict[str, Any]
    ) -> str:
        """Generate response using OpenAI with tool results as context"""
        
        # Build context from tool results
        context_info = []
        for tool_name, result in tool_results.items():
            if "error" not in result:
                context_info.append(f"Tool {tool_name} results: {json.dumps(result, default=str)}")
        
        context_str = "\n".join(context_info) if context_info else "No tool data available."
        
        # Build prompt
        user_prompt = f"""User Message: {message}

User Context:
- Followed symbols: {', '.join(user_context.followed_symbols)}
- Risk tolerance: {user_context.risk_tolerance}
- Portfolio value: ${user_context.portfolio_value:,.2f}

Available Data:
{context_str}

Please provide a comprehensive response based on the user's question and the available data. Include relevant insights, analysis, and actionable recommendations where appropriate."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I apologize, but I'm experiencing technical difficulties with AI processing. However, I can still provide you with the raw data: {context_str}"
    
    # Tool implementation methods
    async def _get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Get stock data using real market data tool"""
        return await self.market_tool.get_stock_data(symbol)
    
    async def _get_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Get crypto data using real market data tool"""
        return await self.market_tool.get_crypto_data(symbol)
    
    async def _get_news_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get news analysis for specific symbol"""
        articles = await self.news_tool.get_news_for_symbol(symbol, limit=5)
        summary = await self.news_tool.summarize_news(articles)
        return {
            "symbol": symbol,
            "articles": articles,
            "summary": summary,
            "article_count": len(articles)
        }
    
    async def _get_market_news(self) -> Dict[str, Any]:
        """Get general market news"""
        articles = await self.news_tool.get_market_news(limit=10)
        summary = await self.news_tool.summarize_news(articles)
        return {
            "articles": articles,
            "summary": summary,
            "article_count": len(articles)
        }
    
    async def _analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio performance"""
        return await self.portfolio_tool.analyze_portfolio_performance(portfolio_data)
    
    async def _get_technical_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get technical analysis for symbol"""
        # Get stock data first
        stock_data = await self.market_tool.get_stock_data(symbol)
        if "error" in stock_data:
            return stock_data
        
        # Perform technical analysis
        return await self.analysis_tool.perform_technical_analysis(symbol, stock_data)
    
    async def _get_recommendation(self, symbol: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get investment recommendation"""
        # Get stock data and user preferences
        stock_data = await self.market_tool.get_stock_data(symbol)
        if "error" in stock_data:
            return stock_data
        
        # Generate recommendation
        return await self.recommendation_tool.generate_recommendation(
            symbol, stock_data, {}, user_context
        )
    
    async def _check_alerts(self, user_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for triggered alerts"""
        # Get current prices for alert symbols
        current_prices = {}
        for alert in user_alerts:
            symbol = alert.get("symbol")
            if symbol and symbol not in current_prices:
                stock_data = await self.market_tool.get_stock_data(symbol)
                if "error" not in stock_data:
                    current_prices[symbol] = stock_data["price"]
        
        # Check alerts
        triggered_alerts = await self.alert_tool.check_price_alerts(user_alerts, current_prices)
        return {
            "triggered_alerts": triggered_alerts,
            "total_alerts": len(user_alerts),
            "triggered_count": len(triggered_alerts)
        }


# Factory function to create the agent
def create_simple_ai_trading_agent() -> SimpleAITradingAgent:
    """Create and return a simple AI trading agent instance"""
    try:
        return SimpleAITradingAgent()
    except Exception as e:
        print(f"Error creating AI agent: {e}")
        # Return a mock agent that provides basic responses
        return None


# Example usage
async def test_simple_agent():
    """Test the simple AI trading agent"""
    agent = create_simple_ai_trading_agent()
    if not agent:
        print("Failed to create agent")
        return
    
    # Test user context
    user_context = UserContext(
        user_id="test_user",
        followed_symbols=["AAPL", "GOOGL"],
        risk_tolerance="medium",
        portfolio_value=50000.0
    )
    
    # Test queries
    test_queries = [
        "How is Apple stock performing today?",
        "What's the latest news on GOOGL?",
        "Give me a market overview",
        "Should I buy Tesla stock?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        try:
            response = await agent.process_message(query, user_context)
            print(f"🤖 Response: {response.content[:200]}...")
            print(f"🔧 Tools used: {[tool['tool'] for tool in response.tool_calls]}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_simple_agent())