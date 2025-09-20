# AI Trading Agent - Main Intelligent Trading Assistant
# Uses 5-layer architecture with pre-filtered data and optimized token usage
# Agent tools use filtered data from Layer 3 and store interactions to Layer 5

import asyncio
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Pydantic AI imports
try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    print("Warning: pydantic-ai not installed. Using mock implementation.")
    class Agent:
        def __init__(self, *args, **kwargs): pass
        def tool(self, func): return func
    class RunContext:
        def __init__(self, deps): self.deps = deps
    PYDANTIC_AI_AVAILABLE = False

# Import 5-layer services
from services.user_data_filter import get_user_filtered_data
from services.user_history_manager import store_interaction, store_conversation, get_user_stock_history, get_user_investment_patterns


class UserContext(BaseModel):
    """User context containing filtered data from Layer 3"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    user_id: str
    username: str
    filtered_data: Dict[str, Any]
    
    @property
    def user_stocks(self) -> Dict[str, Any]:
        return self.filtered_data.get("user_stocks", {})
    
    @property 
    def portfolio_summary(self) -> Dict[str, Any]:
        return self.filtered_data.get("portfolio_summary", {})
    
    @property
    def relevant_news(self) -> List[Dict]:
        return self.filtered_data.get("relevant_news", [])
    
    @property
    def user_crypto(self) -> Dict[str, Any]:
        return self.filtered_data.get("user_crypto", {})
    
    @property
    def user_preferences(self) -> Dict[str, Any]:
        return self.filtered_data.get("user_preferences", {})


class AITradingAgent:
    """
    AI Trading Agent using 5-Layer Architecture
    
    This agent:
    - Uses pre-filtered data from Layer 3 (User Data Filter) 
    - All tools decorated with @agent.tool
    - Stores all interactions to Layer 5 (User History Manager)
    - Provides personalized analysis based on user history
    - Optimized for token usage (only relevant data)
    """
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        
        # Create agent with 5-layer system prompt
        system_prompt = self._create_five_layer_system_prompt()
        
        try:
            if PYDANTIC_AI_AVAILABLE:
                api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
                
                if api_key:
                    model = OpenAIChatModel(model_name, provider=OpenAIProvider(api_key=api_key))
                    self.agent = Agent(
                        model=model,
                        deps_type=UserContext,
                        system_prompt=system_prompt
                    )
                    self._register_five_layer_tools()
                    print(f"✅ 5-Layer Trading Agent initialized with {model_name}")
                else:
                    print("Warning: No OpenAI API key found")
                    self.agent = None
            else:
                print("Warning: pydantic-ai not available")
                self.agent = None
                
        except Exception as e:
            print(f"Warning: Could not initialize agent: {e}")
            self.agent = None
    
    def _create_five_layer_system_prompt(self) -> str:
        """Create system prompt optimized for 5-layer architecture"""
        return """
        You are an expert AI trading assistant with access to personalized, filtered market data.
        
        Key features of your data access:
        - You receive ONLY data relevant to the user's followed stocks and portfolio
        - All data has been pre-filtered based on user preferences and history
        - You have access to the user's historical investment patterns and behavior
        - Your recommendations should be personalized based on user's risk tolerance and investment style
        
        Your capabilities:
        - Analyze user's portfolio performance and provide insights
        - Provide stock analysis for followed securities only
        - Analyze news sentiment for relevant holdings
        - Assess risk based on user's historical patterns
        - Give personalized recommendations considering user's investment personality
        
        Guidelines:
        1. Always consider the user's historical investment behavior and preferences
        2. Reference their portfolio context when providing advice
        3. Only analyze stocks the user is following or owns
        4. Provide actionable insights based on filtered, relevant data
        5. Be transparent about your analysis being based on their specific interests
        6. Include risk warnings appropriate to their historical risk tolerance
        
        Remember: You work with pre-filtered, personalized data - not general market data.
        This allows for more relevant, targeted advice with lower token usage.
        """
    
    def _register_five_layer_tools(self):
        """Register all tools using 5-layer architecture with @agent.tool decorators"""
        
        @self.agent.tool
        async def get_user_portfolio_analysis(ctx: RunContext[UserContext]) -> Dict[str, Any]:
            """
            Get personalized portfolio analysis using filtered data from Layer 3
            Stores interaction to Layer 5 for future personalization
            """
            try:
                portfolio = ctx.deps.portfolio_summary
                user_id = ctx.deps.user_id
                
                # Store interaction to Layer 5
                await store_interaction(user_id, {
                    "action": "portfolio_analysis",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"portfolio_value": portfolio.get("total_market_value", 0)}
                })
                
                if not portfolio.get("holdings"):
                    return {
                        "message": "You don't have any portfolio holdings to analyze.",
                        "suggestion": "Consider adding some investments to start building your portfolio."
                    }
                
                # Enhance with personalized insights
                total_value = portfolio.get("total_market_value", 0)
                total_return = portfolio.get("total_return_percent", 0)
                holdings = portfolio.get("holdings", [])
                
                # Get historical patterns for personalized insights
                investment_patterns = await get_user_investment_patterns(user_id)
                
                analysis = {
                    "portfolio_overview": {
                        "total_value": f"${total_value:,.2f}",
                        "total_return": f"{total_return:+.2f}%",
                        "num_holdings": len(holdings),
                        "largest_position": max(holdings, key=lambda x: x["weight_in_portfolio"], default={}).get("symbol", "N/A"),
                        "portfolio_diversity": portfolio.get("portfolio_diversity", 0)
                    },
                    "performance_insights": [
                        f"Your portfolio is {'outperforming' if total_return > 0 else 'underperforming'} with a {total_return:+.2f}% return",
                        f"You have {len(holdings)} holdings with diversification across {len(set(h['sector'] for h in holdings))} sectors"
                    ],
                    "personalized_insights": self._generate_personalized_portfolio_insights(
                        portfolio, investment_patterns
                    ),
                    "top_performers": sorted(holdings, key=lambda x: x["unrealized_pnl_percent"], reverse=True)[:3],
                    "bottom_performers": sorted(holdings, key=lambda x: x["unrealized_pnl_percent"])[:3]
                }
                
                return analysis
                
            except Exception as e:
                return {"error": f"Portfolio analysis failed: {str(e)}"}
        
        @self.agent.tool
        async def analyze_user_stock(ctx: RunContext[UserContext], symbol: str) -> Dict[str, Any]:
            """
            Analyze a stock from user's followed list with personalized insights
            Uses only filtered data and stores interaction history
            """
            try:
                user_stocks = ctx.deps.user_stocks
                user_id = ctx.deps.user_id
                
                symbol = symbol.upper()
                
                if symbol not in user_stocks:
                    return {
                        "error": f"{symbol} is not in your followed stocks list.",
                        "suggestion": "You can only analyze stocks you're following. Add it to your watchlist first."
                    }
                
                stock_data = user_stocks[symbol]
                
                # Get user's historical interaction with this stock
                stock_history = await get_user_stock_history(user_id, symbol)
                
                # Store this analysis interaction
                await store_interaction(user_id, {
                    "action": "stock_analysis",
                    "symbol": symbol,
                    "data": {
                        "current_price": stock_data["current_price"],
                        "change_percent": stock_data["change_percent"]
                    }
                })
                
                # Build personalized analysis
                analysis = {
                    "stock_overview": {
                        "symbol": symbol,
                        "company_name": stock_data["company_name"],
                        "current_price": f"${stock_data['current_price']:.2f}",
                        "daily_change": f"{stock_data['change_percent']:+.2f}%",
                        "sector": stock_data["sector"],
                        "market_cap": f"${stock_data['market_cap']:,.0f}"
                    },
                    "technical_analysis": stock_data.get("technical_indicators", {}),
                    "user_context": self._add_user_context(stock_data, stock_history),
                    "historical_interaction": {
                        "times_analyzed": stock_history.get("interaction_count", 0),
                        "sentiment_trend": stock_history.get("sentiment_trend", "neutral"),
                        "last_interaction": stock_history.get("last_interaction")
                    }
                }
                
                # Add position info if user owns this stock
                if stock_data.get("user_position"):
                    position = stock_data["user_position"]
                    analysis["your_position"] = {
                        "shares_owned": position["shares_owned"],
                        "avg_cost": f"${position['avg_cost']:.2f}",
                        "current_value": f"${position['current_value']:,.2f}",
                        "unrealized_pnl": f"${position['unrealized_pnl']:+,.2f}",
                        "return_percent": f"{position['unrealized_pnl_percent']:+.2f}%"
                    }
                
                return analysis
                
            except Exception as e:
                return {"error": f"Stock analysis failed: {str(e)}"}
        
        @self.agent.tool
        async def get_personalized_news_analysis(ctx: RunContext[UserContext]) -> Dict[str, Any]:
            """
            Get news analysis filtered for user's interests
            Only includes news relevant to followed stocks
            """
            try:
                relevant_news = ctx.deps.relevant_news
                user_id = ctx.deps.user_id
                
                # Store interaction
                await store_interaction(user_id, {
                    "action": "news_analysis",
                    "data": {"articles_analyzed": len(relevant_news)}
                })
                
                if not relevant_news:
                    return {
                        "message": "No recent news found for your followed stocks.",
                        "suggestion": "News analysis is based on your watchlist. Consider adding more stocks to get broader coverage."
                    }
                
                # Analyze sentiment for user's interests
                positive_articles = [n for n in relevant_news if n.get("sentiment_score", 0) > 0.2]
                negative_articles = [n for n in relevant_news if n.get("sentiment_score", 0) < -0.2]
                
                # Group by relevant symbols
                symbol_news = {}
                for article in relevant_news:
                    for symbol in article.get("relevant_symbols", []):
                        if symbol not in symbol_news:
                            symbol_news[symbol] = []
                        symbol_news[symbol].append(article)
                
                analysis = {
                    "news_overview": {
                        "total_articles": len(relevant_news),
                        "positive_sentiment": len(positive_articles),
                        "negative_sentiment": len(negative_articles),
                        "neutral_sentiment": len(relevant_news) - len(positive_articles) - len(negative_articles)
                    },
                    "sentiment_summary": self._generate_sentiment_summary(relevant_news),
                    "top_headlines": [
                        {
                            "title": article["headline"],
                            "sentiment": article["sentiment_label"],
                            "relevant_to": article.get("relevant_symbols", [])
                        }
                        for article in relevant_news[:5]
                    ],
                    "symbol_specific_news": {
                        symbol: len(articles) for symbol, articles in symbol_news.items()
                    }
                }
                
                return analysis
                
            except Exception as e:
                return {"error": f"News analysis failed: {str(e)}"}
        
        @self.agent.tool
        async def get_personalized_risk_assessment(ctx: RunContext[UserContext]) -> Dict[str, Any]:
            """
            Provide risk assessment based on user's portfolio and historical patterns
            Uses investment personality from Layer 5
            """
            try:
                user_id = ctx.deps.user_id
                portfolio = ctx.deps.portfolio_summary
                user_preferences = ctx.deps.user_preferences
                
                # Get user's investment patterns from Layer 5
                investment_patterns = await get_user_investment_patterns(user_id)
                
                # Store interaction
                await store_interaction(user_id, {
                    "action": "risk_assessment",
                    "data": {
                        "portfolio_value": portfolio.get("total_market_value", 0),
                        "num_holdings": len(portfolio.get("holdings", []))
                    }
                })
                
                # Calculate personalized risk metrics
                risk_assessment = {
                    "portfolio_risk_level": self._assess_portfolio_risk(portfolio),
                    "diversification_analysis": self._analyze_diversification(portfolio),
                    "historical_risk_behavior": investment_patterns.get("investment_personality", {}),
                    "user_risk_profile": {
                        "stated_tolerance": user_preferences.get("risk_tolerance", "moderate"),
                        "investment_style": user_preferences.get("investment_style", "balanced"),
                        "behavioral_risk_level": investment_patterns.get("investment_personality", {}).get("risk_tolerance", "moderate")
                    },
                    "recommendations": self._generate_risk_recommendations(
                        portfolio, user_preferences, investment_patterns
                    ),
                    "risk_metrics": {
                        "concentration_risk": portfolio.get("largest_position_percent", 0),
                        "sector_concentration": self._calculate_sector_concentration(portfolio),
                        "portfolio_volatility": "Calculated based on holdings"
                    }
                }
                
                return risk_assessment
                
            except Exception as e:
                return {"error": f"Risk assessment failed: {str(e)}"}
        
        @self.agent.tool
        async def get_user_crypto_analysis(ctx: RunContext[UserContext]) -> Dict[str, Any]:
            """
            Analyze user's followed cryptocurrencies
            Only shows crypto assets user is tracking
            """
            try:
                user_crypto = ctx.deps.user_crypto
                user_id = ctx.deps.user_id
                
                # Store interaction
                await store_interaction(user_id, {
                    "action": "crypto_analysis",
                    "data": {"crypto_symbols": list(user_crypto.keys())}
                })
                
                if not user_crypto:
                    return {
                        "message": "You're not following any cryptocurrencies.",
                        "suggestion": "Add some crypto assets to your watchlist to get personalized analysis."
                    }
                
                crypto_analysis = {
                    "crypto_overview": {
                        "followed_cryptos": len(user_crypto),
                        "total_market_cap": sum(crypto.get("market_cap", 0) for crypto in user_crypto.values())
                    },
                    "performance_summary": [
                        {
                            "symbol": symbol,
                            "name": data["name"],
                            "price": f"${data['current_price']:,.2f}",
                            "change_24h": f"{data['change_percent']:+.2f}%",
                            "is_positive": data["change"] >= 0
                        }
                        for symbol, data in user_crypto.items()
                    ],
                    "market_insights": self._generate_crypto_insights(user_crypto)
                }
                
                return crypto_analysis
                
            except Exception as e:
                return {"error": f"Crypto analysis failed: {str(e)}"}
        
        @self.agent.tool
        async def get_investment_recommendations(ctx: RunContext[UserContext]) -> Dict[str, Any]:
            """
            Generate personalized investment recommendations
            Based on user's portfolio, preferences, and historical patterns
            """
            try:
                user_id = ctx.deps.user_id
                user_stocks = ctx.deps.user_stocks
                portfolio = ctx.deps.portfolio_summary
                user_preferences = ctx.deps.user_preferences
                
                # Get investment patterns for personalization
                investment_patterns = await get_user_investment_patterns(user_id)
                
                # Store interaction
                await store_interaction(user_id, {
                    "action": "investment_recommendations",
                    "data": {"request_time": datetime.now().isoformat()}
                })
                
                recommendations = {
                    "portfolio_recommendations": self._generate_portfolio_recommendations(
                        portfolio, user_preferences, investment_patterns
                    ),
                    "rebalancing_suggestions": self._suggest_rebalancing(portfolio),
                    "diversification_opportunities": self._find_diversification_opportunities(
                        user_stocks, portfolio, user_preferences
                    ),
                    "risk_adjustments": self._suggest_risk_adjustments(
                        portfolio, user_preferences, investment_patterns
                    ),
                    "personalized_insights": [
                        f"Based on your {user_preferences.get('investment_style', 'balanced')} investment style",
                        f"Considering your {user_preferences.get('risk_tolerance', 'moderate')} risk tolerance",
                        f"Your portfolio shows {investment_patterns.get('investment_personality', {}).get('trading_frequency', 'moderate')} trading frequency"
                    ]
                }
                
                return recommendations
                
            except Exception as e:
                return {"error": f"Recommendation generation failed: {str(e)}"}
        
        print("✅ Registered 6 personalized agent tools with @agent.tool decorators")
    
    # Helper methods for analysis
    def _generate_personalized_portfolio_insights(self, portfolio: Dict, patterns: Dict) -> List[str]:
        """Generate personalized insights based on user patterns"""
        insights = []
        
        if patterns.get("investment_personality", {}).get("risk_tolerance") == "conservative":
            insights.append("Your conservative approach shows good risk management")
        elif patterns.get("investment_personality", {}).get("risk_tolerance") == "aggressive":
            insights.append("Your aggressive strategy shows high growth potential but monitor risks")
            
        diversity = portfolio.get("portfolio_diversity", 0)
        if diversity < 5:
            insights.append("Consider diversifying across more holdings to reduce concentration risk")
        elif diversity > 10:
            insights.append("Good diversification - you're spreading risk across multiple investments")
            
        return insights
    
    def _add_user_context(self, stock_data: Dict, stock_history: Dict) -> Dict[str, Any]:
        """Add user-specific context to stock analysis"""
        context = {}
        
        if stock_history.get("interaction_count", 0) > 5:
            context["user_interest"] = "High - You frequently analyze this stock"
        elif stock_history.get("interaction_count", 0) > 0:
            context["user_interest"] = "Moderate - You've looked at this stock before"
        else:
            context["user_interest"] = "New - First time analyzing this stock"
            
        context["sentiment_history"] = stock_history.get("sentiment_trend", "neutral")
        return context
    
    def _generate_sentiment_summary(self, news: List[Dict]) -> str:
        """Generate overall sentiment summary"""
        if not news:
            return "No news data available"
            
        avg_sentiment = sum(article.get("sentiment_score", 0) for article in news) / len(news)
        
        if avg_sentiment > 0.2:
            return "Overall positive sentiment in news about your followed stocks"
        elif avg_sentiment < -0.2:
            return "Overall negative sentiment in news about your followed stocks"
        else:
            return "Mixed or neutral sentiment in recent news"
    
    def _assess_portfolio_risk(self, portfolio: Dict) -> str:
        """Assess portfolio risk level"""
        concentration = portfolio.get("largest_position_percent", 0)
        
        if concentration > 50:
            return "High - Portfolio is heavily concentrated"
        elif concentration > 30:
            return "Moderate-High - Some concentration risk"
        elif concentration > 20:
            return "Moderate - Reasonable concentration"
        else:
            return "Low - Well diversified portfolio"
    
    def _analyze_diversification(self, portfolio: Dict) -> Dict[str, Any]:
        """Analyze portfolio diversification"""
        holdings = portfolio.get("holdings", [])
        
        if not holdings:
            return {"level": "None", "recommendation": "Build a diversified portfolio"}
        
        sectors = set(holding["sector"] for holding in holdings)
        
        return {
            "num_sectors": len(sectors),
            "num_holdings": len(holdings),
            "level": "Good" if len(sectors) >= 3 else "Limited",
            "sectors": list(sectors)
        }
    
    def _calculate_sector_concentration(self, portfolio: Dict) -> float:
        """Calculate sector concentration risk"""
        holdings = portfolio.get("holdings", [])
        if not holdings:
            return 0.0
            
        sector_weights = {}
        for holding in holdings:
            sector = holding["sector"]
            weight = holding.get("weight_in_portfolio", 0)
            sector_weights[sector] = sector_weights.get(sector, 0) + weight
        
        return max(sector_weights.values()) if sector_weights else 0.0
    
    def _generate_risk_recommendations(self, portfolio: Dict, preferences: Dict, patterns: Dict) -> List[str]:
        """Generate personalized risk recommendations"""
        recommendations = []
        
        risk_tolerance = preferences.get("risk_tolerance", "moderate")
        concentration = portfolio.get("largest_position_percent", 0)
        
        if concentration > 40 and risk_tolerance == "conservative":
            recommendations.append("Consider reducing your largest position to lower concentration risk")
        
        if len(portfolio.get("holdings", [])) < 5:
            recommendations.append("Add more holdings to improve diversification")
            
        return recommendations
    
    def _generate_crypto_insights(self, crypto_data: Dict) -> List[str]:
        """Generate insights about crypto holdings"""
        insights = []
        
        if not crypto_data:
            return ["No cryptocurrency data available"]
        
        avg_change = sum(data["change_percent"] for data in crypto_data.values()) / len(crypto_data)
        
        if avg_change > 5:
            insights.append("Your crypto watchlist is showing strong positive momentum")
        elif avg_change < -5:
            insights.append("Your crypto watchlist is experiencing significant declines")
        else:
            insights.append("Mixed performance across your crypto watchlist")
            
        return insights
    
    def _generate_portfolio_recommendations(self, portfolio: Dict, preferences: Dict, patterns: Dict) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []
        
        total_return = portfolio.get("total_return_percent", 0)
        
        if total_return < 0:
            recommendations.append("Consider reviewing underperforming positions")
        elif total_return > 20:
            recommendations.append("Strong performance - consider taking some profits")
        
        return recommendations
    
    def _suggest_rebalancing(self, portfolio: Dict) -> List[str]:
        """Suggest portfolio rebalancing"""
        suggestions = []
        
        largest_weight = portfolio.get("largest_position_percent", 0)
        if largest_weight > 40:
            suggestions.append("Consider reducing your largest position to improve balance")
            
        return suggestions
    
    def _find_diversification_opportunities(self, stocks: Dict, portfolio: Dict, preferences: Dict) -> List[str]:
        """Find diversification opportunities"""
        opportunities = []
        
        current_sectors = set(holding["sector"] for holding in portfolio.get("holdings", []))
        
        if len(current_sectors) < 3:
            opportunities.append("Consider adding holdings from different sectors")
            
        return opportunities
    
    def _suggest_risk_adjustments(self, portfolio: Dict, preferences: Dict, patterns: Dict) -> List[str]:
        """Suggest risk level adjustments"""
        adjustments = []
        
        stated_risk = preferences.get("risk_tolerance", "moderate")
        behavioral_risk = patterns.get("investment_personality", {}).get("risk_tolerance", "moderate")
        
        if stated_risk != behavioral_risk:
            adjustments.append(f"Your behavior suggests {behavioral_risk} risk tolerance, but you stated {stated_risk}")
            
        return adjustments
    
    async def chat(self, user_id: str, message: str) -> str:
        """
        Chat interface using 5-layer architecture
        Gets filtered data for user and processes with personalized context
        """
        try:
            # Get filtered data from Layer 3
            filtered_data = await get_user_filtered_data(user_id)
            
            if "error" in filtered_data:
                return f"Sorry, I couldn't access your data: {filtered_data['error']}"
            
            # Create user context
            user_context = UserContext(
                user_id=user_id,
                username=filtered_data["username"],
                filtered_data=filtered_data
            )
            
            if self.agent:
                # Process with Pydantic AI agent
                result = await self.agent.run(message, deps=user_context)
                response = result.data
                
                # Store conversation in Layer 5
                await store_conversation(user_id, message, response)
                
                return response
            else:
                return "AI agent not available. Please check configuration."
                
        except Exception as e:
            print(f"❌ Chat error: {str(e)}")
            return f"I encountered an error processing your request: {str(e)}"


# Factory function
def create_ai_trading_agent(model_name: str = "gpt-4o") -> AITradingAgent:
    """Create an AI trading agent instance"""
    return AITradingAgent(model_name)


# Testing function
async def test_ai_trading_agent():
    """Test the 5-layer trading agent"""
    print("🧪 Testing Layer 4: 5-Layer Trading Agent")
    print("=" * 60)
    
    # Ensure data is collected first
    from services.data_collector import start_data_collection
    await start_data_collection()
    
    # Create agent
    agent = create_ai_trading_agent()
    
    if not agent.agent:
        print("❌ Agent not available - check OpenAI API key")
        return
    
    # Test with different users
    test_users = ["user1", "demo_user"] 
    test_queries = [
        "Analyze my portfolio performance",
        "What's the current status of AAPL?", 
        "Give me a risk assessment",
        "What's the latest news about my stocks?",
        "Should I rebalance my portfolio?"
    ]
    
    for user_id in test_users:
        print(f"\n👤 Testing with {user_id}:")
        print("-" * 40)
        
        for query in test_queries[:3]:  # Test first 3 queries
            try:
                print(f"\n📝 Query: {query}")
                response = await agent.chat(user_id, query)
                print(f"🤖 Response: {response[:200]}..." if len(response) > 200 else f"🤖 Response: {response}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")


# Interactive chat for testing
async def interactive_ai_chat():
    """Interactive chat using 5-layer architecture"""
    print("🚀 5-Layer Trading AI - Interactive Chat")
    print("=" * 50)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Start data collection
    print("🔄 Starting data collection...")
    from services.data_collector import start_data_collection
    await start_data_collection()
    
    # Create agent
    agent = create_ai_trading_agent()
    
    if not agent.agent:
        print("❌ Failed to create agent. Please check your OpenAI API key.")
        return
    
    print("✅ 5-Layer Trading AI ready!")
    print("📊 Using personalized, filtered data based on your portfolio and interests")
    print("💡 Available test users: user1 (alex), user2 (sarah), demo_user")
    print("💬 Type 'quit' to exit\n")
    
    # Default user for testing
    current_user = "demo_user"
    print(f"🎭 Currently chatting as: {current_user}")
    print("💡 Type 'switch user1' or 'switch user2' to change users\n")
    
    while True:
        try:
            user_input = input(f"🤔 You ({current_user}): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for using 5-Layer Trading AI!")
                break
            
            if user_input.startswith('switch '):
                new_user = user_input[7:].strip()
                if new_user in ['user1', 'user2', 'demo_user']:
                    current_user = new_user
                    print(f"🎭 Switched to user: {current_user}")
                else:
                    print("❌ Invalid user. Available: user1, user2, demo_user")
                continue
            
            if not user_input:
                continue
            
            print("🤖 TradingAI: Analyzing your personalized data...")
            response = await agent.chat(current_user, user_input)
            print(f"🤖 TradingAI: {response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 5-Layer Trading Agent - Standalone Mode")
    
    # Choose between test mode and interactive chat
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_ai_trading_agent())
    else:
        asyncio.run(interactive_ai_chat())