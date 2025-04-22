# backend/tools/yfin_tool.py

import yfinance as yf
from datetime import datetime
import pytz
from typing import List, Dict

# -------------------
# Top Stocks by Volume
# -------------------

def fetch_top_stocks_by_volume(limit: int = 5) -> List[Dict]:
    """
    Dynamically fetch top U.S. stocks based on today's trading volume.

    Returns:
        A list of dictionaries containing ticker, volume, price.
    """
    stock_list = [
        "AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "META", "GOOGL", "NFLX",
        "AMD", "INTC", "BA", "PYPL", "QCOM", "SHOP", "CRM"
    ]

    stock_volume = []

    for ticker in stock_list:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            volume = data['Volume'].iloc[-1]
            price = data['Close'].iloc[-1]
            stock_volume.append({
                "ticker": ticker,
                "volume": volume,
                "price": price
            })

    stock_volume.sort(key=lambda x: x['volume'], reverse=True)

    return stock_volume[:limit]

# -------------------
# Top Cryptos by Volume
# -------------------

def fetch_top_cryptos_by_volume(limit: int = 5) -> List[Dict]:
    """
    Dynamically fetch top cryptocurrencies based on today's trading volume.

    Returns:
        A list of dictionaries containing crypto ticker, volume, price.
    """
    crypto_list = [
        "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "DOGE-USD", "ADA-USD", "XRP-USD", "AVAX-USD"
    ]

    crypto_volume = []

    for crypto in crypto_list:
        coin = yf.Ticker(crypto)
        data = coin.history(period="1d")
        if not data.empty:
            volume = data['Volume'].iloc[-1]
            price = data['Close'].iloc[-1]
            crypto_volume.append({
                "crypto": crypto,
                "volume": volume,
                "price": price
            })

    crypto_volume.sort(key=lambda x: x['volume'], reverse=True)

    return crypto_volume[:limit]

# -------------------
# News Fetching and Extraction
# -------------------

def utc_to_est(publish_time_utc: datetime) -> str:
    """
    Convert UTC time to U.S. Eastern Time (EST or EDT).
    """
    eastern = pytz.timezone("US/Eastern")
    local_time = publish_time_utc.astimezone(eastern)
    return local_time.strftime("%Y-%m-%d %H:%M %Z")  # e.g., '2025-04-17 12:04 EDT'

def time_ago(publish_time_utc: datetime) -> str:
    """
    Calculate how long ago the news was published based on user's local time.
    """
    now_local = datetime.now().astimezone()
    delta = now_local - publish_time_utc.astimezone(now_local.tzinfo)

    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} min ago"
    else:
        return "just now"

def fetch_news_for_ticker(ticker: str, count: int = 5) -> List[Dict]:
    """
    Fetch recent news headlines for a specific ticker (stock or crypto) using get_news().
    
    Returns:
        A list of dictionaries containing cleaned news details.
    """
    news_data = []
    stock = yf.Ticker(ticker)

    try:
        news_items = stock.get_news(count=count, tab="news")
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        news_items = []

    for item in news_items:
        try:
            content = item.get("content", {})
            pub_date_raw = content.get("pubDate", "1970-01-01T00:00:00Z")
            pub_date_dt = datetime.fromisoformat(pub_date_raw.replace("Z", "+00:00"))  # Standard UTC datetime

            # Formatting
            pub_date_est = utc_to_est(pub_date_dt)  # 转成美国东部时间
            pub_time_ago = time_ago(pub_date_dt)    # 本地时间感知多久前

            news_entry = {
                "ticker": ticker,
                "title": content.get("title", "Unknown Title"),
                "publisher": content.get("provider", {}).get("displayName", "Unknown Publisher"),
                "published_at_utc": pub_date_dt.strftime("%Y-%m-%d %H:%M UTC"),  # 保留UTC格式
                "published_at_est": pub_date_est,    # 转成EST/EDT显示
                "time_ago": pub_time_ago,            # 本地感知
                "link": content.get("provider", {}).get("url", ""),
            }
            news_data.append(news_entry)
        except Exception as e:
            print(f"Error parsing news item for {ticker}: {e}")
            continue

    return news_data


# -------------------
# Combined Utility Functions
# -------------------

def get_top_market_movers_and_news() -> Dict[str, List[Dict]]:
    """
    Fetch today's top stocks and cryptos along with their latest news.

    Returns:
        Dictionary with keys 'stocks' and 'cryptos', each containing a list of records.
    """
    top_stocks = fetch_top_stocks_by_volume()
    top_cryptos = fetch_top_cryptos_by_volume()

    stocks_news = []
    for stock in top_stocks:
        news = fetch_news_for_ticker(stock['ticker'])
        stocks_news.extend(news)

    cryptos_news = []
    for crypto in top_cryptos:
        news = fetch_news_for_ticker(crypto['crypto'])
        cryptos_news.extend(news)

    return {
        "stocks": stocks_news,
        "cryptos": cryptos_news
    }
