# Layer 3: User Data Filtering Service
# Filters cached data based on user's followings and portfolio for personalized dashboard and agent use

import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import json

from .data_collector import get_cached_data, get_cache_manager


class UserDataFilter:
    """Service for filtering global cached data for specific users - Layer 3 of 5-layer architecture"""
    
    def __init__(self):
        self.cache = get_cache_manager()
        # Mock user data for testing - in production this would come from database
        self.mock_user_data = self._initialize_mock_user_data()
    
    def _initialize_mock_user_data(self) -> Dict[str, Any]:
        """Initialize mock user data for testing"""
        return {
            "user1": {
                "username": "alex",
                "user_id": "user1", 
                "followings": ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "BTC", "ETH"],
                "portfolio": {
                    "AAPL": {"shares": 50, "avg_cost": 150.0, "purchase_date": "2024-01-15"},
                    "GOOGL": {"shares": 20, "avg_cost": 130.0, "purchase_date": "2024-02-01"},
                    "TSLA": {"shares": 15, "avg_cost": 200.0, "purchase_date": "2024-01-20"}
                },
                "preferences": {
                    "risk_tolerance": "moderate",
                    "investment_style": "growth",
                    "sectors_of_interest": ["Technology", "Clean Energy"],
                    "notification_preferences": {
                        "price_alerts": True,
                        "news_alerts": True,
                        "portfolio_updates": True
                    }
                }
            },
            "user2": {
                "username": "sarah",
                "user_id": "user2",
                "followings": ["AMZN", "META", "NFLX", "SHOP", "AMD", "ETH", "ADA"],
                "portfolio": {
                    "AMZN": {"shares": 10, "avg_cost": 140.0, "purchase_date": "2024-02-15"},
                    "META": {"shares": 25, "avg_cost": 300.0, "purchase_date": "2024-01-10"}
                },
                "preferences": {
                    "risk_tolerance": "aggressive", 
                    "investment_style": "value",
                    "sectors_of_interest": ["Technology", "Consumer Discretionary"],
                    "notification_preferences": {
                        "price_alerts": True,
                        "news_alerts": False,
                        "portfolio_updates": True
                    }
                }
            },
            "demo_user": {
                "username": "demo", 
                "user_id": "demo_user",
                "followings": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"],
                "portfolio": {
                    "AAPL": {"shares": 100, "avg_cost": 160.0, "purchase_date": "2024-01-01"},
                    "MSFT": {"shares": 50, "avg_cost": 400.0, "purchase_date": "2024-01-05"}
                },
                "preferences": {
                    "risk_tolerance": "conservative",
                    "investment_style": "balanced",
                    "sectors_of_interest": ["Technology"],
                    "notification_preferences": {
                        "price_alerts": True,
                        "news_alerts": True,
                        "portfolio_updates": True
                    }
                }
            }
        }
    
    async def get_user_filtered_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get filtered data for specific user - Main Layer 3 function
        This is the key function that Agent (Layer 4) will use
        """
        try:
            # Get user information
            user_data = self.mock_user_data.get(user_id)
            if not user_data:
                return {"error": f"User {user_id} not found"}
            
            print(f"🔍 Layer 3: Filtering data for user '{user_data['username']}' ({user_id})")
            
            # Get all cached data from Layer 1
            stocks_data = await get_cached_data("stocks")
            crypto_data = await get_cached_data("crypto") 
            news_data = await get_cached_data("news")
            market_summary = await get_cached_data("market_summary")
            
            if not stocks_data:
                return {"error": "No market data available"}
            
            # Filter data based on user's followings and portfolio
            filtered_data = {
                "user_id": user_id,
                "username": user_data["username"],
                "user_stocks": await self._filter_user_stocks(
                    stocks_data, user_data["followings"], user_data["portfolio"]
                ),
                "user_crypto": await self._filter_user_crypto(
                    crypto_data, user_data["followings"]
                ),
                "relevant_news": await self._filter_relevant_news(
                    news_data, user_data["followings"]
                ),
                "portfolio_summary": await self._calculate_portfolio_summary(
                    user_data["portfolio"], stocks_data
                ),
                "user_preferences": user_data["preferences"],
                "market_context": {
                    "market_summary": market_summary,
                    "user_sector_exposure": await self._calculate_sector_exposure(
                        user_data["portfolio"], stocks_data
                    )
                },
                "timestamp": datetime.now().isoformat(),
                "data_freshness": await self._get_data_freshness()
            }
            
            print(f"✅ Layer 3: Filtered data ready - {len(filtered_data['user_stocks'])} stocks, {len(filtered_data['relevant_news'])} news")
            return filtered_data
            
        except Exception as e:
            print(f"❌ Error filtering user data: {str(e)}")
            return {"error": str(e)}
    
    async def _filter_user_stocks(self, stocks_data: Dict, followings: List[str], portfolio: Dict) -> Dict[str, Any]:
        """Filter stocks data based on user's followings and portfolio"""
        user_stocks = {}
        
        # Include stocks user is following
        for symbol in followings:
            if symbol in stocks_data:
                stock_data = stocks_data[symbol].copy()
                
                # Add portfolio context if user owns this stock
                if symbol in portfolio:
                    position = portfolio[symbol]
                    current_price = stock_data["current_price"]
                    position_value = position["shares"] * current_price
                    position_cost = position["shares"] * position["avg_cost"]
                    
                    stock_data["user_position"] = {
                        "shares_owned": position["shares"],
                        "avg_cost": position["avg_cost"],
                        "current_value": position_value,
                        "unrealized_pnl": position_value - position_cost,
                        "unrealized_pnl_percent": ((position_value / position_cost) - 1) * 100 if position_cost > 0 else 0,
                        "purchase_date": position["purchase_date"]
                    }
                else:
                    stock_data["user_position"] = None
                
                user_stocks[symbol] = stock_data
        
        return user_stocks
    
    async def _filter_user_crypto(self, crypto_data: Optional[Dict], followings: List[str]) -> Dict[str, Any]:
        """Filter crypto data based on user's followings"""
        if not crypto_data:
            return {}
        
        user_crypto = {}
        for symbol in followings:
            if symbol in crypto_data:
                user_crypto[symbol] = crypto_data[symbol]
        
        return user_crypto
    
    async def _filter_relevant_news(self, news_data: Optional[Dict], followings: List[str]) -> List[Dict]:
        """Filter news that's relevant to user's followed stocks"""
        if not news_data or "general_news" not in news_data:
            return []
        
        relevant_news = []
        followings_set = set(followings)
        
        # Check general news for relevant articles
        for article in news_data["general_news"]:
            # Check if article mentions any of user's followed symbols
            related_symbols = set(article.get("related_symbols", []))
            if related_symbols.intersection(followings_set):
                article_copy = article.copy()
                article_copy["relevance_reason"] = "mentions_followed_stock"
                article_copy["relevant_symbols"] = list(related_symbols.intersection(followings_set))
                relevant_news.append(article_copy)
        
        # Add stock-specific news for followed symbols
        if "stock_specific_news" in news_data:
            for symbol in followings:
                if symbol in news_data["stock_specific_news"]:
                    for article in news_data["stock_specific_news"][symbol]:
                        article_copy = article.copy()
                        article_copy["relevance_reason"] = "specific_to_followed_stock"
                        article_copy["relevant_symbols"] = [symbol]
                        relevant_news.append(article_copy)
        
        # Sort by sentiment and datetime, limit to most relevant
        relevant_news.sort(key=lambda x: (abs(x["sentiment_score"]), x["datetime"]), reverse=True)
        return relevant_news[:20]  # Limit to top 20 most relevant articles
    
    async def _calculate_portfolio_summary(self, portfolio: Dict, stocks_data: Dict) -> Dict[str, Any]:
        """Calculate comprehensive portfolio summary"""
        if not portfolio:
            return {
                "total_market_value": 0,
                "total_cost_basis": 0,
                "total_unrealized_pnl": 0,
                "total_return_percent": 0,
                "holdings": [],
                "portfolio_diversity": 0,
                "largest_position_percent": 0
            }
        
        total_value = 0
        total_cost = 0
        holdings = []
        
        for symbol, position in portfolio.items():
            if symbol in stocks_data:
                current_price = stocks_data[symbol]["current_price"]
                position_value = position["shares"] * current_price
                position_cost = position["shares"] * position["avg_cost"]
                
                total_value += position_value
                total_cost += position_cost
                
                holdings.append({
                    "symbol": symbol,
                    "company_name": stocks_data[symbol]["company_name"],
                    "sector": stocks_data[symbol]["sector"],
                    "shares": position["shares"],
                    "avg_cost": position["avg_cost"],
                    "current_price": current_price,
                    "market_value": position_value,
                    "cost_basis": position_cost,
                    "unrealized_pnl": position_value - position_cost,
                    "unrealized_pnl_percent": ((position_value / position_cost) - 1) * 100 if position_cost > 0 else 0,
                    "weight_in_portfolio": (position_value / total_value) * 100 if total_value > 0 else 0,
                    "purchase_date": position["purchase_date"]
                })
        
        # Calculate portfolio diversity and concentration metrics
        portfolio_diversity = len(holdings)
        largest_position_percent = max((h["weight_in_portfolio"] for h in holdings), default=0)
        
        return {
            "total_market_value": total_value,
            "total_cost_basis": total_cost,
            "total_unrealized_pnl": total_value - total_cost,
            "total_return_percent": ((total_value / total_cost) - 1) * 100 if total_cost > 0 else 0,
            "holdings": holdings,
            "portfolio_diversity": portfolio_diversity,
            "largest_position_percent": largest_position_percent,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _calculate_sector_exposure(self, portfolio: Dict, stocks_data: Dict) -> Dict[str, float]:
        """Calculate user's sector exposure from portfolio"""
        sector_exposure = {}
        total_value = 0
        
        # Calculate total portfolio value first
        for symbol, position in portfolio.items():
            if symbol in stocks_data:
                position_value = position["shares"] * stocks_data[symbol]["current_price"]
                total_value += position_value
        
        # Calculate sector percentages
        for symbol, position in portfolio.items():
            if symbol in stocks_data:
                sector = stocks_data[symbol]["sector"]
                position_value = position["shares"] * stocks_data[symbol]["current_price"]
                
                if sector not in sector_exposure:
                    sector_exposure[sector] = 0
                
                sector_exposure[sector] += (position_value / total_value) * 100 if total_value > 0 else 0
        
        return sector_exposure
    
    async def _get_data_freshness(self) -> Dict[str, str]:
        """Get freshness information about cached data"""
        cache_stats = self.cache.get_cache_stats()
        return {
            "cache_status": "active",
            "total_cached_items": cache_stats["total_entries"],
            "active_items": cache_stats["active_entries"],
            "data_types_cached": cache_stats["cache_keys"]
        }
    
    async def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get specifically formatted data for dashboard display"""
        filtered_data = await self.get_user_filtered_data(user_id)
        
        if "error" in filtered_data:
            return filtered_data
        
        # Format for dashboard consumption
        dashboard_data = {
            "user_info": {
                "user_id": filtered_data["user_id"],
                "username": filtered_data["username"]
            },
            "followed_assets": self._format_followed_assets(filtered_data["user_stocks"], filtered_data["user_crypto"]),
            "portfolio": filtered_data["portfolio_summary"],
            "recent_news": filtered_data["relevant_news"][:10],  # Limit for dashboard
            "market_context": filtered_data["market_context"],
            "preferences": filtered_data["user_preferences"],
            "last_updated": filtered_data["timestamp"]
        }
        
        return dashboard_data
    
    def _format_followed_assets(self, user_stocks: Dict, user_crypto: Dict) -> List[Dict]:
        """Format followed assets for dashboard display"""
        followed_assets = []
        
        # Add stocks
        for symbol, data in user_stocks.items():
            asset = {
                "id": f"stock_{symbol}",
                "symbol": symbol,
                "name": data["company_name"],
                "type": "stock",
                "price": data["current_price"],
                "change": data["change"],
                "changePercent": f"{data['change_percent']:+.2f}%",
                "isPositive": data["change"] >= 0,
                "sector": data["sector"],
                "user_owns": data["user_position"] is not None
            }
            
            if data["user_position"]:
                asset["position"] = data["user_position"]
            
            followed_assets.append(asset)
        
        # Add crypto
        for symbol, data in user_crypto.items():
            followed_assets.append({
                "id": f"crypto_{symbol}",
                "symbol": symbol,
                "name": data["name"],
                "type": "crypto",
                "price": data["current_price"],
                "change": data["change"],
                "changePercent": f"{data['change_percent']:+.2f}%",
                "isPositive": data["change"] >= 0,
                "user_owns": False  # Crypto positions not tracked in this demo
            })
        
        return followed_assets
    
    def get_user_followings(self, user_id: str) -> List[str]:
        """Get user's followed symbols (for Agent tools)"""
        user_data = self.mock_user_data.get(user_id, {})
        return user_data.get("followings", [])
    
    def get_user_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get user's portfolio (for Agent tools)"""
        user_data = self.mock_user_data.get(user_id, {})
        return user_data.get("portfolio", {})


# Global service instance
_user_data_filter = UserDataFilter()


async def get_user_filtered_data(user_id: str) -> Dict[str, Any]:
    """Get filtered data for user - Main Layer 3 function"""
    return await _user_data_filter.get_user_filtered_data(user_id)


async def get_dashboard_data(user_id: str) -> Dict[str, Any]:
    """Get dashboard data for user"""
    return await _user_data_filter.get_dashboard_data(user_id)


def get_user_followings(user_id: str) -> List[str]:
    """Get user followings"""
    return _user_data_filter.get_user_followings(user_id)


def get_user_portfolio(user_id: str) -> Dict[str, Any]:
    """Get user portfolio"""
    return _user_data_filter.get_user_portfolio(user_id)


def get_user_data_filter() -> UserDataFilter:
    """Get the user data filter service instance"""
    return _user_data_filter


# Testing function
async def test_user_data_filter():
    """Test the user data filtering system"""
    print("🧪 Testing Layer 3: User Data Filter")
    print("=" * 50)
    
    # Ensure we have data in cache first
    from .data_collector import start_data_collection
    await start_data_collection()
    
    # Test filtering for different users
    test_users = ["user1", "user2", "demo_user"]
    
    for user_id in test_users:
        print(f"\n👤 Testing user: {user_id}")
        
        filtered_data = await get_user_filtered_data(user_id)
        
        if "error" not in filtered_data:
            print(f"✅ Filtered data for {filtered_data['username']}:")
            print(f"  - Followed stocks: {len(filtered_data['user_stocks'])}")
            print(f"  - Portfolio holdings: {len(filtered_data['portfolio_summary']['holdings'])}")
            print(f"  - Relevant news: {len(filtered_data['relevant_news'])}")
            print(f"  - Portfolio value: ${filtered_data['portfolio_summary']['total_market_value']:,.2f}")
            print(f"  - Total return: {filtered_data['portfolio_summary']['total_return_percent']:+.2f}%")
            
            # Test dashboard data formatting
            dashboard_data = await get_dashboard_data(user_id)
            print(f"  - Dashboard assets: {len(dashboard_data['followed_assets'])}")
        else:
            print(f"❌ Error: {filtered_data['error']}")


if __name__ == "__main__":
    print("🚀 Layer 3: User Data Filter - Testing Mode")
    asyncio.run(test_user_data_filter())