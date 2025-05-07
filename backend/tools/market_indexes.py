import asyncio
import yfinance as yf
import logging
from datetime import datetime
from .cache import cache_result

logger = logging.getLogger(__name__)

# 定义静态默认数据
DEFAULT_INDEX_DATA = {
    "^GSPC": {"name": "S&P 500", "price": 5000.0, "change": 0, "change_percent": 0},
    "^DJI": {"name": "道琼斯工业平均指数", "price": 38000.0, "change": 0, "change_percent": 0},
    "^IXIC": {"name": "纳斯达克综合指数", "price": 16000.0, "change": 0, "change_percent": 0},
    # 添加其他指数的默认数据...
}

async def _fetch(ticker):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1d", interval="5m")  # 当日 5 分钟线
        
        if hist.empty:
            logger.warning(f"⚠️ {ticker} 没有返回数据")
            raise ValueError(f"No data for {ticker}")
            
        # 处理数据并返回
        latest = hist.iloc[-1]
        first = hist.iloc[0]
        change = latest['Close'] - first['Open']
        change_percent = (change / first['Open']) * 100
        
        return {
            "symbol": ticker,
            "name": DEFAULT_INDEX_DATA.get(ticker, {}).get("name", ticker),
            "price": round(latest['Close'], 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "data": hist['Close'].tolist()[-12:],  # 最近12个数据点
            "fallback": False
        }
    except Exception as e:
        logger.error(f"❌ Error fetching {ticker}: {str(e)}")
        # 返回默认数据
        default_data = DEFAULT_INDEX_DATA.get(ticker, {"name": ticker, "price": 0, "change": 0, "change_percent": 0})
        return {
            "symbol": ticker,
            "name": default_data["name"],
            "price": default_data["price"],
            "change": default_data["change"],
            "change_percent": default_data["change_percent"],
            "data": [default_data["price"]] * 12,  # 12个相同的点
            "fallback": True
        }

@cache_result(expire_seconds=900)  # 缓存15分钟
async def get_market_indexes():
    indexes = ["^GSPC", "^DJI", "^IXIC"]  # S&P500, 道指, 纳指
    
    try:
        # 并行获取所有指数数据
        coros = [_fetch(ticker) for ticker in indexes]
        results = await asyncio.gather(*coros, return_exceptions=True)
        
        # 处理返回的结果，替换异常为默认数据
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                ticker = indexes[i]
                default_data = DEFAULT_INDEX_DATA.get(ticker, {"name": ticker, "price": 0, "change": 0, "change_percent": 0})
                valid_results.append({
                    "symbol": ticker,
                    "name": default_data["name"],
                    "price": default_data["price"],
                    "change": default_data["change"],
                    "change_percent": default_data["change_percent"],
                    "data": [default_data["price"]] * 12,  # 12个相同的点
                    "fallback": True
                })
            else:
                valid_results.append(result)
        
        return valid_results
        
    except Exception as e:
        logger.error(f"获取市场指数失败: {str(e)}")
        # 返回所有指数的默认数据
        return [
            {
                "symbol": ticker,
                "name": DEFAULT_INDEX_DATA.get(ticker, {}).get("name", ticker),
                "price": DEFAULT_INDEX_DATA.get(ticker, {}).get("price", 0),
                "change": DEFAULT_INDEX_DATA.get(ticker, {}).get("change", 0),
                "change_percent": DEFAULT_INDEX_DATA.get(ticker, {}).get("change_percent", 0),
                "data": [DEFAULT_INDEX_DATA.get(ticker, {}).get("price", 0)] * 12,
                "fallback": True
            }
            for ticker in indexes
        ]