# backend/tools/crypto_utils.py

import yfinance as yf
import asyncio

# ✅增加更多主流币，保证一定能返回有效数据
CRYPTO_TICKERS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD",
    "ADA-USD", "DOGE-USD", "AVAX-USD", "DOT-USD", "MATIC-USD",
    "SHIB-USD", "LTC-USD", "TRX-USD", "LINK-USD", "UNI1-USD",
    "XLM-USD", "ETC-USD", "FIL-USD", "APT-USD", "ATOM-USD"
]

async def fetch_crypto_info(ticker, semaphore: asyncio.Semaphore):
    """
    异步抓取单个加密货币的数据
    """
    async with semaphore:
        try:
            data = yf.Ticker(ticker).history(period="5d")
            if data.empty or len(data) < 2:
                return None

            latest = data.iloc[-1]
            previous = data.iloc[-2]
            price = latest["Close"]
            volume = latest["Volume"]
            change_percent = ((latest["Close"] - previous["Close"]) / previous["Close"]) * 100
            spark = data['Close'].tail(30).round(2).tolist()
            
            return {
                "ticker": ticker,
                "price": round(price, 2),
                "volume": int(volume),
                "change_percent": round(change_percent, 2),
                "spark": spark,
            }
        except Exception as e:
            print(f"⚠️ Warning: Skipping {ticker} due to error: {e}")
            return None

async def get_top_cryptos(limit=5):
    """
    抓取热门加密货币，按成交量排序，返回前N个
    """
    sem = asyncio.Semaphore(5) 
    tasks = [fetch_crypto_info(ticker, sem) for ticker in CRYPTO_TICKERS]
    results = await asyncio.gather(*tasks)

    valid_results = [r for r in results if r and r["volume"] > 0]
    if not valid_results:
        print("❌ No valid crypto data fetched.")
        return []

    sorted_cryptos = sorted(valid_results, key=lambda x: x["volume"], reverse=True)[:limit]
    return sorted_cryptos
