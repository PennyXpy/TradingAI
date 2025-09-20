"""
Mock Financial Data Generator
Generates realistic financial data for stocks, crypto, news, and market analysis
This data will be used by the agent tools and stored in the database
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# ================================================================================
# STOCK SYMBOLS AND BASIC DATA
# ================================================================================

STOCK_SYMBOLS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", 
    "AMD", "INTC", "CRM", "UBER", "PYPL", "SHOP", "SPOT", "ZM",
    "SPY", "QQQ", "IWM", "VTI"  # ETFs
]

COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
    "NFLX": "Netflix Inc.",
    "AMD": "Advanced Micro Devices Inc.",
    "INTC": "Intel Corporation",
    "CRM": "Salesforce Inc.",
    "UBER": "Uber Technologies Inc.",
    "PYPL": "PayPal Holdings Inc.",
    "SHOP": "Shopify Inc.",
    "SPOT": "Spotify Technology S.A.",
    "ZM": "Zoom Video Communications Inc.",
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust",
    "IWM": "iShares Russell 2000 ETF",
    "VTI": "Vanguard Total Stock Market ETF"
}

SECTORS = {
    "AAPL": "Technology",
    "GOOGL": "Technology", 
    "MSFT": "Technology",
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "META": "Technology",
    "NVDA": "Technology",
    "NFLX": "Communication Services",
    "AMD": "Technology",
    "INTC": "Technology",
    "CRM": "Technology",
    "UBER": "Technology",
    "PYPL": "Financial Services",
    "SHOP": "Technology",
    "SPOT": "Communication Services",
    "ZM": "Technology",
    "SPY": "Diversified",
    "QQQ": "Technology ETF",
    "IWM": "Small Cap ETF",
    "VTI": "Broad Market ETF"
}

# ================================================================================
# PRICE DATA GENERATION
# ================================================================================

def generate_stock_price(symbol: str, base_price: Optional[float] = None) -> Dict[str, Any]:
    """Generate realistic stock price data"""
    
    # Base prices for major stocks
    base_prices = {
        "AAPL": 175.0, "GOOGL": 140.0, "MSFT": 420.0, "AMZN": 145.0,
        "TSLA": 210.0, "META": 320.0, "NVDA": 450.0, "NFLX": 450.0,
        "AMD": 110.0, "INTC": 45.0, "CRM": 220.0, "UBER": 65.0,
        "PYPL": 60.0, "SHOP": 75.0, "SPOT": 180.0, "ZM": 70.0,
        "SPY": 450.0, "QQQ": 380.0, "IWM": 200.0, "VTI": 240.0
    }
    
    if base_price is None:
        base_price = base_prices.get(symbol, 100.0)
    
    # Add some randomness to the price
    price_variation = random.uniform(-0.05, 0.05)  # ±5%
    current_price = base_price * (1 + price_variation)
    
    # Calculate daily change
    daily_change = random.uniform(-0.03, 0.03)  # ±3% daily change
    previous_close = current_price / (1 + daily_change)
    change = current_price - previous_close
    change_percent = (change / previous_close) * 100
    
    # Volume varies by stock size
    base_volume = 1000000 if symbol in ["AAPL", "MSFT", "GOOGL"] else 500000
    volume = int(base_volume * random.uniform(0.5, 2.0))
    
    return {
        "symbol": symbol,
        "name": COMPANY_NAMES.get(symbol, f"{symbol} Corp"),
        "current_price": round(current_price, 2),
        "previous_close": round(previous_close, 2),
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "volume": volume,
        "market_cap": calculate_market_cap(current_price, symbol),
        "sector": SECTORS.get(symbol, "Technology"),
        "last_updated": datetime.now().isoformat()
    }

def calculate_market_cap(price: float, symbol: str) -> str:
    """Calculate mock market cap"""
    shares_outstanding = {
        "AAPL": 15.7e9, "GOOGL": 12.6e9, "MSFT": 7.4e9, "AMZN": 10.5e9,
        "TSLA": 3.2e9, "META": 2.7e9, "NVDA": 2.5e9, "NFLX": 440e6
    }
    
    shares = shares_outstanding.get(symbol, 1e9)  # Default 1B shares
    market_cap = price * shares
    
    if market_cap >= 1e12:
        return f"${market_cap/1e12:.1f}T"
    elif market_cap >= 1e9:
        return f"${market_cap/1e9:.1f}B"
    else:
        return f"${market_cap/1e6:.1f}M"

def generate_historical_prices(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
    """Generate historical price data"""
    base_price = generate_stock_price(symbol)["current_price"]
    historical_data = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        
        # Random walk for historical prices
        price_change = random.uniform(-0.02, 0.02)  # ±2% daily
        if i == 0:
            price = base_price * random.uniform(0.95, 1.05)
        else:
            price = historical_data[-1]["close"] * (1 + price_change)
        
        # OHLC data
        high = price * random.uniform(1.0, 1.03)
        low = price * random.uniform(0.97, 1.0)
        volume = int(random.uniform(500000, 2000000))
        
        historical_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(price * random.uniform(0.995, 1.005), 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(price, 2),
            "volume": volume
        })
    
    return historical_data

# ================================================================================
# NEWS DATA GENERATION
# ================================================================================

NEWS_TEMPLATES = [
    "{company} reports {metric} earnings, beating analyst expectations by {percent}%",
    "{company} announces new {product} technology, shares rise {percent}%",
    "Analyst upgrades {company} to {rating}, cites strong {sector} fundamentals",
    "{company} CEO discusses {topic} strategy in quarterly earnings call",
    "Market volatility affects {company} as {sector} sector faces headwinds",
    "{company} partners with major tech firm for {initiative} project",
    "Regulatory concerns impact {company} following {event} announcement",
    "{company} stock rallies on positive {metric} guidance for next quarter"
]

def generate_news_article(symbol: str) -> Dict[str, Any]:
    """Generate realistic news article"""
    company = COMPANY_NAMES.get(symbol, f"{symbol} Corp")
    template = random.choice(NEWS_TEMPLATES)
    
    # News sentiment affects stock direction
    sentiment_score = random.uniform(-0.8, 0.8)
    
    # Fill in template variables
    metrics = ["Q3", "quarterly", "annual", "monthly"]
    products = ["AI", "cloud", "mobile", "software", "hardware"]
    ratings = ["Buy", "Strong Buy", "Outperform", "Hold"]
    topics = ["growth", "expansion", "innovation", "sustainability"]
    events = ["merger", "acquisition", "partnership", "policy"]
    initiatives = ["AI development", "cloud migration", "sustainability", "digital transformation"]
    
    headline = template.format(
        company=company,
        metric=random.choice(metrics),
        percent=random.randint(5, 25),
        product=random.choice(products),
        rating=random.choice(ratings),
        sector=SECTORS.get(symbol, "technology"),
        topic=random.choice(topics),
        event=random.choice(events),
        initiative=random.choice(initiatives)
    )
    
    return {
        "id": str(uuid.uuid4()),
        "headline": headline,
        "summary": f"Latest developments regarding {company} and its market position...",
        "source": random.choice(["Reuters", "Bloomberg", "Yahoo Finance", "MarketWatch", "CNBC"]),
        "published_at": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
        "sentiment_score": round(sentiment_score, 2),
        "sentiment_label": "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral",
        "symbols": [symbol],
        "url": f"https://example-news.com/article/{uuid.uuid4()}",
        "relevance_score": random.uniform(0.6, 1.0)
    }

def generate_multiple_news(symbols: List[str], articles_per_symbol: int = 3) -> List[Dict[str, Any]]:
    """Generate multiple news articles for multiple symbols"""
    all_news = []
    for symbol in symbols:
        for _ in range(articles_per_symbol):
            all_news.append(generate_news_article(symbol))
    
    # Sort by published time (most recent first)
    all_news.sort(key=lambda x: x["published_at"], reverse=True)
    return all_news

# ================================================================================
# TECHNICAL ANALYSIS DATA
# ================================================================================

def generate_technical_indicators(symbol: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate technical analysis indicators"""
    
    # Get recent prices for calculations
    prices = [float(d["close"]) for d in historical_data[-20:]]  # Last 20 days
    current_price = prices[-1]
    
    # Moving averages
    ma_10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else current_price
    ma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
    
    # RSI (simplified)
    rsi = random.uniform(25, 75)  # Mock RSI
    
    # Support and resistance
    recent_highs = [float(d["high"]) for d in historical_data[-10:]]
    recent_lows = [float(d["low"]) for d in historical_data[-10:]]
    resistance = max(recent_highs) * random.uniform(1.01, 1.05)
    support = min(recent_lows) * random.uniform(0.95, 0.99)
    
    return {
        "symbol": symbol,
        "current_price": current_price,
        "moving_averages": {
            "ma_10": round(ma_10, 2),
            "ma_20": round(ma_20, 2),
            "ma_50": round(current_price * random.uniform(0.95, 1.05), 2),
            "ma_200": round(current_price * random.uniform(0.90, 1.10), 2)
        },
        "technical_indicators": {
            "rsi": round(rsi, 2),
            "macd": round(random.uniform(-2, 2), 2),
            "bollinger_upper": round(current_price * 1.05, 2),
            "bollinger_lower": round(current_price * 0.95, 2),
            "volume_sma": random.randint(800000, 1200000)
        },
        "levels": {
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "pivot": round((resistance + support) / 2, 2)
        },
        "signals": {
            "trend": random.choice(["Bullish", "Bearish", "Neutral"]),
            "momentum": random.choice(["Strong", "Weak", "Moderate"]),
            "volatility": random.choice(["High", "Medium", "Low"])
        }
    }

# ================================================================================
# CRYPTOCURRENCY DATA
# ================================================================================

CRYPTO_SYMBOLS = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "MATIC", "ATOM"]

CRYPTO_NAMES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum", 
    "ADA": "Cardano",
    "DOT": "Polkadot",
    "LINK": "Chainlink",
    "UNI": "Uniswap",
    "MATIC": "Polygon",
    "ATOM": "Cosmos"
}

def generate_crypto_price(symbol: str) -> Dict[str, Any]:
    """Generate cryptocurrency price data"""
    base_prices = {
        "BTC": 43000, "ETH": 2500, "ADA": 0.45, "DOT": 7.2,
        "LINK": 14.5, "UNI": 6.8, "MATIC": 0.85, "ATOM": 9.5
    }
    
    base_price = base_prices.get(symbol, 100.0)
    
    # Crypto is more volatile
    price_variation = random.uniform(-0.08, 0.08)  # ±8%
    current_price = base_price * (1 + price_variation)
    
    daily_change = random.uniform(-0.06, 0.06)  # ±6% daily change
    previous_close = current_price / (1 + daily_change)
    change = current_price - previous_close
    change_percent = (change / previous_close) * 100
    
    return {
        "symbol": symbol,
        "name": CRYPTO_NAMES.get(symbol, f"{symbol} Token"),
        "current_price": round(current_price, 6 if current_price < 1 else 2),
        "previous_close": round(previous_close, 6 if previous_close < 1 else 2),
        "change": round(change, 6 if abs(change) < 1 else 2),
        "change_percent": round(change_percent, 2),
        "volume_24h": random.randint(100000000, 1000000000),  # 24h volume in USD
        "market_cap": f"${random.randint(10, 800)}B",
        "rank": CRYPTO_SYMBOLS.index(symbol) + 1 if symbol in CRYPTO_SYMBOLS else 999
    }

# ================================================================================
# MARKET INDEXES DATA
# ================================================================================

INDEX_SYMBOLS = ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"]

def generate_market_index(symbol: str) -> Dict[str, Any]:
    """Generate market index data"""
    base_values = {
        "^GSPC": 4500,  # S&P 500
        "^DJI": 35000,  # Dow Jones
        "^IXIC": 14000, # NASDAQ
        "^RUT": 2000,   # Russell 2000
        "^VIX": 18      # VIX
    }
    
    names = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones Industrial Average", 
        "^IXIC": "NASDAQ Composite",
        "^RUT": "Russell 2000",
        "^VIX": "CBOE Volatility Index"
    }
    
    base_value = base_values.get(symbol, 1000)
    
    # Market indexes are less volatile than individual stocks
    variation = random.uniform(-0.02, 0.02)  # ±2%
    current_value = base_value * (1 + variation)
    
    daily_change = random.uniform(-0.015, 0.015)  # ±1.5%
    previous_close = current_value / (1 + daily_change)
    change = current_value - previous_close
    change_percent = (change / previous_close) * 100
    
    return {
        "symbol": symbol,
        "name": names.get(symbol, "Market Index"),
        "current_value": round(current_value, 2),
        "previous_close": round(previous_close, 2),
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "last_updated": datetime.now().isoformat()
    }

# ================================================================================
# COMPREHENSIVE DATA GENERATION FUNCTIONS
# ================================================================================

def generate_dashboard_data() -> Dict[str, Any]:
    """Generate comprehensive dashboard data"""
    
    # Top stocks data
    top_stocks = []
    for symbol in STOCK_SYMBOLS[:10]:  # Top 10 stocks
        stock_data = generate_stock_price(symbol)
        top_stocks.append(stock_data)
    
    # Crypto data
    crypto_data = []
    for symbol in CRYPTO_SYMBOLS[:5]:  # Top 5 crypto
        crypto_data.append(generate_crypto_price(symbol))
    
    # Market indexes
    indexes = []
    for symbol in INDEX_SYMBOLS:
        indexes.append(generate_market_index(symbol))
    
    # Recent news
    news = generate_multiple_news(STOCK_SYMBOLS[:5], 2)  # 2 articles per top 5 stocks
    
    return {
        "stocks": top_stocks,
        "crypto": crypto_data,
        "indexes": indexes,
        "news": news[:10],  # Latest 10 news articles
        "generated_at": datetime.now().isoformat()
    }

def generate_portfolio_data(user_id: str) -> Dict[str, Any]:
    """Generate mock portfolio data for a user"""
    
    # Random portfolio positions
    portfolio_symbols = random.sample(STOCK_SYMBOLS, random.randint(3, 8))
    positions = []
    total_value = 0
    total_cost = 0
    
    for symbol in portfolio_symbols:
        price_data = generate_stock_price(symbol)
        shares = random.randint(10, 500)
        cost_per_share = price_data["current_price"] * random.uniform(0.8, 1.2)  # Bought at different price
        
        current_value = shares * price_data["current_price"]
        cost_basis = shares * cost_per_share
        unrealized_gain_loss = current_value - cost_basis
        
        positions.append({
            "symbol": symbol,
            "name": price_data["name"],
            "shares": shares,
            "current_price": price_data["current_price"],
            "cost_per_share": round(cost_per_share, 2),
            "current_value": round(current_value, 2),
            "cost_basis": round(cost_basis, 2),
            "unrealized_gain_loss": round(unrealized_gain_loss, 2),
            "unrealized_gain_loss_percent": round((unrealized_gain_loss / cost_basis) * 100, 2),
            "sector": price_data["sector"]
        })
        
        total_value += current_value
        total_cost += cost_basis
    
    total_gain_loss = total_value - total_cost
    
    return {
        "user_id": user_id,
        "positions": positions,
        "summary": {
            "total_market_value": round(total_value, 2),
            "total_cost_basis": round(total_cost, 2),
            "total_unrealized_gain_loss": round(total_gain_loss, 2),
            "total_unrealized_gain_loss_percent": round((total_gain_loss / total_cost) * 100, 2),
            "position_count": len(positions),
            "day_change": round(random.uniform(-500, 500), 2),
            "day_change_percent": round(random.uniform(-2, 2), 2)
        },
        "allocation": calculate_portfolio_allocation(positions),
        "generated_at": datetime.now().isoformat()
    }

def calculate_portfolio_allocation(positions: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate portfolio allocation by sector"""
    sector_values = {}
    total_value = sum(pos["current_value"] for pos in positions)
    
    for position in positions:
        sector = position["sector"]
        value = position["current_value"]
        sector_values[sector] = sector_values.get(sector, 0) + value
    
    # Convert to percentages
    allocation = {sector: round((value / total_value) * 100, 1) 
                 for sector, value in sector_values.items()}
    
    return allocation

# ================================================================================
# UTILITY FUNCTIONS
# ================================================================================

def get_random_symbols(count: int = 5) -> List[str]:
    """Get random stock symbols"""
    return random.sample(STOCK_SYMBOLS, min(count, len(STOCK_SYMBOLS)))

def generate_market_summary() -> Dict[str, Any]:
    """Generate overall market summary"""
    return {
        "market_status": random.choice(["Open", "Closed", "Pre-market", "After-hours"]),
        "market_sentiment": random.choice(["Bullish", "Bearish", "Neutral"]),
        "volatility_index": round(random.uniform(15, 35), 2),
        "trending_sectors": random.sample(list(set(SECTORS.values())), 3),
        "market_movers": {
            "gainers": get_random_symbols(3),
            "losers": get_random_symbols(3),
            "most_active": get_random_symbols(3)
        },
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Test the data generation
    print("🧪 Testing Mock Data Generation")
    
    # Test stock data
    stock = generate_stock_price("AAPL")
    print(f"✅ Stock Data: {stock['symbol']} at ${stock['current_price']}")
    
    # Test news
    news = generate_news_article("AAPL")
    print(f"✅ News: {news['headline'][:60]}...")
    
    # Test portfolio
    portfolio = generate_portfolio_data("test_user")
    print(f"✅ Portfolio: {portfolio['summary']['position_count']} positions, ${portfolio['summary']['total_market_value']}")
    
    # Test dashboard
    dashboard = generate_dashboard_data()
    print(f"✅ Dashboard: {len(dashboard['stocks'])} stocks, {len(dashboard['news'])} news articles")
    
    print("\n🎉 All mock data generators working!")