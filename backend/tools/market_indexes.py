# backend/tools/market_indexes.py
"""
抓取美股主要指数 & 大宗商品点位 + 迷你 K 线数据
"""
import asyncio
import yfinance as yf
from typing import List, Dict

INDEXES = {
    "^GSPC": "S&P 500",
    "^DJI":  "Dow 30",
    "^IXIC": "Nasdaq",
    "^RUT":  "Russell 2000",
    "^VIX":  "VIX",
    "GC=F":  "Gold",          # 黄金期货
}

SPARK_POINTS = 30            # 1 日 30 个点

async def _fetch(symbol: str) -> Dict:
    """
    单个指数数据：点位 / 涨跌 / sparkline
    """
    tk = yf.Ticker(symbol)
    hist = tk.history(period="1d", interval="5m")  # 当日 5 分钟线
    if hist.empty:
        return {}

    close = hist["Close"]
    spark = close.tail(SPARK_POINTS).round(2).tolist()
    value = round(close.iloc[-1], 2)
    prev = close.iloc[0]
    change_abs = round(value - prev, 2)
    change_pct = round((value - prev) / prev * 100, 2)

    return {
        "symbol": symbol,
        "name": INDEXES[symbol],
        "value": value,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "spark": spark,
    }

async def get_market_indexes() -> List[Dict]:
    coros = [_fetch(sym) for sym in INDEXES]
    results = await asyncio.gather(*coros)
    # 过滤掉抓取失败的空 dict
    return [r for r in results if r]
