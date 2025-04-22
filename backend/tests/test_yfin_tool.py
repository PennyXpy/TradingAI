# backend/tools/test_yfin_tool.py

from backend.tools.yfin_tool import (
    fetch_top_stocks_by_volume,
    fetch_top_cryptos_by_volume,
    fetch_news_for_ticker,
    get_top_market_movers_and_news,
)

def test_fetch_top_stocks():
    print("📈 Testing fetch_top_stocks_by_volume()...")
    stocks = fetch_top_stocks_by_volume()
    for stock in stocks:
        print(stock)
    print(f"Total stocks fetched: {len(stocks)}\n")

def test_fetch_top_cryptos():
    print("🪙 Testing fetch_top_cryptos_by_volume()...")
    cryptos = fetch_top_cryptos_by_volume()
    for crypto in cryptos:
        print(crypto)
    print(f"Total cryptos fetched: {len(cryptos)}\n")

def test_fetch_news_for_ticker():
    print("📰 Testing fetch_news_for_ticker('AAPL')...")
    news = fetch_news_for_ticker("AAPL")
    for n in news:
        print(n)
    print(f"Total news articles fetched: {len(news)}\n")

def test_get_top_market_movers_and_news():
    print("🔥 Testing get_top_market_movers_and_news()...")
    result = get_top_market_movers_and_news()
    print("Stocks news:")
    for news in result['stocks']:
        print(news)
    print("\nCryptos news:")
    for news in result['cryptos']:
        print(news)
    print(f"Total stocks news: {len(result['stocks'])}")
    print(f"Total cryptos news: {len(result['cryptos'])}\n")

if __name__ == "__main__":
    test_fetch_top_stocks()
    test_fetch_top_cryptos()
    test_fetch_news_for_ticker()
    test_get_top_market_movers_and_news()
