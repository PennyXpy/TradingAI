# Agent Tools Module - Simplified for Mocked Data
# This module provides tool classes that use mocked data for the 5-layer architecture

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import json

# Mock data for consistent responses
MOCK_STOCK_DATA = {
    "AAPL": {"name": "Apple Inc.", "price": 175.50, "change": 2.30, "change_percent": 1.33, "volume": 45623000, "market_cap": 2.8e12},
    "GOOGL": {"name": "Alphabet Inc.", "price": 150.25, "change": -1.50, "change_percent": -0.99, "volume": 25431000, "market_cap": 1.9e12},
    "MSFT": {"name": "Microsoft Corporation", "price": 350.75, "change": 5.25, "change_percent": 1.52, "volume": 32156000, "market_cap": 2.6e12},
    "TSLA": {"name": "Tesla, Inc.", "price": 240.80, "change": -8.20, "change_percent": -3.29, "volume": 89234000, "market_cap": 7.6e11},
    "NVDA": {"name": "NVIDIA Corporation", "price": 800.15, "change": 15.75, "change_percent": 2.01, "volume": 42567000, "market_cap": 2.0e12},
    "AMD": {"name": "Advanced Micro Devices", "price": 120.30, "change": 3.10, "change_percent": 2.64, "volume": 38492000, "market_cap": 1.9e11},
    "META": {"name": "Meta Platforms, Inc.", "price": 340.60, "change": -2.40, "change_percent": -0.70, "volume": 18754000, "market_cap": 8.6e11}
}

MOCK_CRYPTO_DATA = {
    "BTC": {"name": "Bitcoin", "price": 42500.50, "change": 1250.25, "change_percent": 3.03, "volume": 15.2e9, "market_cap": 8.3e11},
    "ETH": {"name": "Ethereum", "price": 2650.75, "change": -45.30, "change_percent": -1.68, "volume": 8.7e9, "market_cap": 3.2e11},
    "SOL": {"name": "Solana", "price": 98.45, "change": 5.67, "change_percent": 6.11, "volume": 2.1e9, "market_cap": 4.5e10},
    "ADA": {"name": "Cardano", "price": 0.45, "change": 0.02, "change_percent": 4.65, "volume": 3.2e8, "market_cap": 1.6e10}
}

MOCK_NEWS_DATA = [
    {"title": "Tech Stocks Rally on Strong Earnings", "summary": "Major tech companies report better than expected quarterly results", "sentiment": 0.8},
    {"title": "Federal Reserve Hints at Rate Changes", "summary": "Central bank signals potential monetary policy adjustments", "sentiment": 0.2},
    {"title": "AI Sector Continues Growth Trajectory", "summary": "Artificial intelligence companies see continued investor interest", "sentiment": 0.7},
    {"title": "Market Volatility Expected This Week", "summary": "Economic indicators suggest increased market movements", "sentiment": 0.4}
]


class MarketDataTool:
    """Tool for retrieving mocked market data"""
    
    async def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Get mocked stock data for a symbol"""
        symbol = symbol.upper()
        if symbol in MOCK_STOCK_DATA:
            base_data = MOCK_STOCK_DATA[symbol].copy()
            # Add some realistic technical indicators
            base_data.update({
                "technical_indicators": {
                    "rsi": random.uniform(30, 70),
                    "macd": random.uniform(-2, 2),
                    "sma_20": base_data["price"] * random.uniform(0.98, 1.02),
                    "sma_50": base_data["price"] * random.uniform(0.95, 1.05)
                },
                "timestamp": datetime.now().isoformat()
            })
            return base_data
        return {"error": f"Stock data not available for {symbol}"}
    
    async def get_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Get mocked cryptocurrency data"""
        symbol = symbol.upper()
        if symbol in MOCK_CRYPTO_DATA:
            base_data = MOCK_CRYPTO_DATA[symbol].copy()
            base_data["timestamp"] = datetime.now().isoformat()
            return base_data
        return {"error": f"Crypto data not available for {symbol}"}


class NewsAnalysisTool:
    """Tool for mocked news analysis"""
    
    async def get_news_for_symbol(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get mocked news for a specific symbol"""
        # Return relevant mock news with symbol context
        symbol_news = []
        for i, news in enumerate(MOCK_NEWS_DATA[:limit]):
            news_copy = news.copy()
            news_copy["symbol"] = symbol
            news_copy["published_at"] = (datetime.now() - timedelta(hours=i*2)).isoformat()
            symbol_news.append(news_copy)
        return symbol_news
    
    async def summarize_news(self, news_articles: List[Dict[str, Any]]) -> str:
        """Provide mocked news summary"""
        if not news_articles:
            return "No news articles to summarize."
        
        positive_count = sum(1 for article in news_articles if article.get("sentiment", 0.5) > 0.6)
        negative_count = sum(1 for article in news_articles if article.get("sentiment", 0.5) < 0.4)
        
        if positive_count > negative_count:
            return f"Recent news sentiment is generally positive with {positive_count} bullish articles. Key themes include tech earnings and AI sector growth."
        elif negative_count > positive_count:
            return f"Recent news sentiment is cautious with {negative_count} concerning articles. Market volatility and policy uncertainty are key factors."
        else:
            return "News sentiment is mixed with balanced coverage of market developments and economic indicators."


class PortfolioTool:
    """Tool for mocked portfolio analysis"""
    
    async def analyze_portfolio_performance(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mocked portfolio performance"""
        try:
            positions = portfolio_data.get("positions", [])
            total_value = sum(pos.get("current_value", 0) for pos in positions)
            total_cost = sum(pos.get("cost_basis", 0) for pos in positions)
            
            total_return = total_value - total_cost if total_cost > 0 else 0
            total_return_percent = (total_return / total_cost * 100) if total_cost > 0 else 0
            
            # Find best and worst performers
            best_performer = max(positions, key=lambda x: x.get("return_percent", 0)) if positions else None
            worst_performer = min(positions, key=lambda x: x.get("return_percent", 0)) if positions else None
            
            return {
                "total_value": total_value,
                "total_return": total_return,
                "total_return_percent": round(total_return_percent, 2),
                "position_count": len(positions),
                "best_performer": best_performer,
                "worst_performer": worst_performer,
                "analysis_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to analyze portfolio: {str(e)}"}
    
    async def get_asset_allocation(self, portfolio_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate mocked asset allocation"""
        positions = portfolio_data.get("positions", [])
        total_value = sum(pos.get("current_value", 0) for pos in positions)
        
        allocation = {}
        for position in positions:
            asset_type = position.get("asset_type", "unknown")
            current_value = position.get("current_value", 0)
            
            if asset_type not in allocation:
                allocation[asset_type] = 0
            allocation[asset_type] += current_value
        
        # Convert to percentages
        if total_value > 0:
            for asset_type in allocation:
                allocation[asset_type] = round((allocation[asset_type] / total_value) * 100, 2)
        
        return allocation


class AlertTool:
    """Tool for mocked alert management"""
    
    async def check_price_alerts(self, user_alerts: List[Dict[str, Any]], current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check mocked price alerts"""
        triggered_alerts = []
        
        for alert in user_alerts:
            symbol = alert.get("symbol", "")
            target_price = alert.get("target_price", 0)
            condition = alert.get("condition", "above")
            
            # Use mock data for current price
            if symbol in MOCK_STOCK_DATA:
                current_price = MOCK_STOCK_DATA[symbol]["price"]
            elif symbol in MOCK_CRYPTO_DATA:
                current_price = MOCK_CRYPTO_DATA[symbol]["price"]
            else:
                continue
            
            if condition == "above" and current_price >= target_price:
                triggered_alerts.append({
                    "symbol": symbol,
                    "message": f"{symbol} reached ${current_price:.2f} (target: ${target_price:.2f})",
                    "triggered_at": datetime.now().isoformat()
                })
            elif condition == "below" and current_price <= target_price:
                triggered_alerts.append({
                    "symbol": symbol,
                    "message": f"{symbol} dropped to ${current_price:.2f} (target: ${target_price:.2f})",
                    "triggered_at": datetime.now().isoformat()
                })
        
        return triggered_alerts


class AnalysisTool:
    """Tool for mocked technical analysis"""
    
    async def perform_technical_analysis(self, symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform mocked technical analysis"""
        current_price = price_data.get("price", 0)
        
        # Generate realistic mock technical indicators
        rsi = random.uniform(30, 70)
        macd = random.uniform(-2, 2)
        
        analysis = {
            "symbol": symbol,
            "current_price": current_price,
            "rsi": round(rsi, 2),
            "macd": round(macd, 3),
            "sma_20": round(current_price * random.uniform(0.98, 1.02), 2),
            "sma_50": round(current_price * random.uniform(0.95, 1.05), 2),
            "volume": price_data.get("volume", 0),
            "analysis_summary": "Technical analysis based on mock indicators",
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine signal based on RSI
        if rsi > 70:
            analysis["signal"] = "OVERBOUGHT"
        elif rsi < 30:
            analysis["signal"] = "OVERSOLD"
        else:
            analysis["signal"] = "NEUTRAL"
        
        return analysis


class RecommendationTool:
    """Tool for generating mocked recommendations"""
    
    async def generate_recommendation(self, 
                                    symbol: str, 
                                    market_data: Dict[str, Any],
                                    portfolio_context: Dict[str, Any],
                                    user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mocked trading recommendation"""
        current_price = market_data.get("price", 0)
        risk_tolerance = user_preferences.get("risk_tolerance", "medium")
        
        # Mock recommendation logic
        actions = ["BUY", "SELL", "HOLD", "WATCH"]
        confidence_base = random.uniform(0.4, 0.8)
        
        # Adjust based on risk tolerance
        if risk_tolerance == "high":
            confidence = min(confidence_base + 0.2, 1.0)
            action = random.choice(["BUY", "SELL", "HOLD"])
        elif risk_tolerance == "low":
            confidence = max(confidence_base - 0.2, 0.1)
            action = random.choice(["HOLD", "WATCH"])
        else:
            confidence = confidence_base
            action = random.choice(actions)
        
        recommendation = {
            "symbol": symbol,
            "current_price": current_price,
            "action": action,
            "confidence": round(confidence, 2),
            "target_price": round(current_price * random.uniform(1.05, 1.15), 2),
            "stop_loss": round(current_price * random.uniform(0.85, 0.95), 2),
            "reasoning": f"Based on technical analysis and {risk_tolerance} risk profile",
            "risk_level": risk_tolerance.upper(),
            "timestamp": datetime.now().isoformat()
        }
        
        return recommendation