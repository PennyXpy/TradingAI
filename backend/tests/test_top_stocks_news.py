# backend/tests/test_top_stocks_news.py

import asyncio
from backend.tools.stock_utils import get_top_traded_stocks
from backend.tools.news_utils import get_latest_market_news
from backend.tools.crypto_utils import get_top_cryptos

def test_top_stocks():
    print("\n📈 Testing top traded stocks...")

    stocks = asyncio.run(get_top_traded_stocks(limit=5))

    for stock in stocks:
        print(f"Ticker: {stock['ticker']}, Price: {stock['price']}, Volume: {stock['volume']}, Change: {stock['change_percent']}%")

def test_top_cryptos():
    print("\n🪙 Testing top traded cryptos...")
    
    cryptos = asyncio.run(get_top_cryptos(limit=5))
    
    for crypto in cryptos:
        print(f"Crypto: {crypto['ticker']}, Price: {crypto['price']}, Volume: {crypto['volume']}, Change: {crypto['change_percent']}%")
        
def test_latest_news():
    print("\n📰 Testing latest financial news...")

    news_list = get_latest_market_news(limit=5)

    for news in news_list:
        print(f"Title: {news['title']}\nET Time: {news['published_at']} ({news['time_ago']})\nURL: {news['link']}\nScores: {news['scores']}\n")

if __name__ == "__main__":
    test_top_stocks()
    test_top_cryptos()
    test_latest_news()
