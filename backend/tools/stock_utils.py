# backend/tools/stock_utils.py

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from asyncio import Semaphore

load_dotenv()

# FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
# FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
# MAX_CONCURRENT_REQUESTS = 10  # 每次最多发10个请求，防止429

# semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)

# async def fetch_symbol_quote(session, ticker):
#     """
#     异步获取单个股票的最新价格和成交量，加限流保护
#     """
#     try:
#         async with semaphore:  # 控制并发数量
#             url = f"{FINNHUB_BASE_URL}/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
#             async with session.get(url) as response:
#                 if response.status == 429:
#                     print(f"❌ 429 Too Many Requests for {ticker}. Skipping...")
#                     return None
#                 data = await response.json()
#                 return {
#                     "ticker": ticker,
#                     "price": data.get("c", 0),
#                     "volume": data.get("v", 0),
#                     "change_percent": data.get("dp", 0)
#                 }
#     except Exception as e:
#         print(f"❌ Error fetching quote for {ticker}: {e}")
#         return None

# async def get_top_traded_stocks(limit=10):
#     """
#     获取交易量最大的股票列表（加速+限流版）
#     """
#     try:
#         async with aiohttp.ClientSession() as session:
#             symbols_url = f"{FINNHUB_BASE_URL}/stock/symbol?exchange=US&token={FINNHUB_API_KEY}"
#             async with session.get(symbols_url) as response:
#                 symbols = await response.json()

#             if not isinstance(symbols, list):
#                 print("❌ Unexpected data format for symbols:", symbols)
#                 return []

#             tickers = [symbol['symbol'] for symbol in symbols if symbol.get('symbol')]

#             tasks = [fetch_symbol_quote(session, ticker) for ticker in tickers[:200]]  # 只取前200个symbol防止压力太大
#             all_quotes = await asyncio.gather(*tasks)

#             valid_quotes = [quote for quote in all_quotes if quote and quote["volume"] > 0]
#             sorted_quotes = sorted(valid_quotes, key=lambda x: x["volume"], reverse=True)

#             return sorted_quotes[:limit]

#     except Exception as e:
#         print(f"❌ Error fetching top traded stocks: {e}")
#         return []


import yfinance as yf

PRESET_TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "NVDA", "TSLA", "AMD", "NFLX", "BRK-B",
    "JPM", "V", "DIS", "BA", "PYPL",
    "BABA", "INTC", "XOM", "WMT", "PFE",
    "COIN", "CRM", "SHOP", "NKE", "UBER",
    "SQ", "PLTR", "SOFI", "CVX", "TSM",
    "ABNB", "SNOW", "SPOT", "ADBE", "MRNA"
]

MAX_CONCURRENT_REQUESTS = 5  # 控制并发，防止被ban

async def fetch_ticker_data(ticker: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="2d")  # 注意用2d，因为要取前一天收盘价

            if data.empty or len(data) < 1:
                return None

            latest = data.iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) > 1 else latest['Close']
            change_percent = ((latest['Close'] - prev_close) / prev_close) * 100 if prev_close else 0
            spark = data['Close'].tail(30).round(2).tolist()
            
            return {
                "ticker": ticker,
                "price": round(latest['Close'], 2),
                "volume": int(latest['Volume']),  # 加入成交量
                "change_percent": round(change_percent, 2),
                "spark": spark,
            }
        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")
            return None

async def get_top_traded_stocks(limit: int = 10):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [fetch_ticker_data(ticker, semaphore) for ticker in PRESET_TICKERS]
    results = await asyncio.gather(*tasks)

    # 过滤掉无效数据
    valid_stocks = [stock for stock in results if stock is not None]

    # 按成交量倒序排列（最大交易量靠前）
    sorted_stocks = sorted(valid_stocks, key=lambda x: x['volume'], reverse=True)

    return sorted_stocks[:limit]