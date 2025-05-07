import yfinance as yf
import logging
import asyncio
from .cache import cache_result

logger = logging.getLogger(__name__)

# 加密货币默认数据
DEFAULT_CRYPTO_DATA = {
    "BTC-USD": {"name": "Bitcoin", "price": 60000.0, "change": 0, "change_percent": 0},
    "ETH-USD": {"name": "Ethereum", "price": 3500.0, "change": 0, "change_percent": 0},
    "SOL-USD": {"name": "Solana", "price": 150.0, "change": 0, "change_percent": 0},
    "XRP-USD": {"name": "Ripple", "price": 0.5, "change": 0, "change_percent": 0},
    "BNB-USD": {"name": "Binance Coin", "price": 400.0, "change": 0, "change_percent": 0},
    "ADA-USD": {"name": "Cardano", "price": 0.5, "change": 0, "change_percent": 0},
    "DOGE-USD": {"name": "Dogecoin", "price": 0.1, "change": 0, "change_percent": 0},
    # 添加更多加密货币默认数据
}

async def _fetch_crypto(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        
        if hist.empty:
            logger.warning(f"⚠️ Warning: Skipping {symbol} due to empty data")
            raise ValueError(f"No data for {symbol}")
            
        # 加密货币没有shortName，直接从默认数据获取名称
        name = DEFAULT_CRYPTO_DATA.get(symbol, {}).get("name", symbol)
        
        # 计算价格变化
        latest_price = hist['Close'].iloc[-1]
        prev_close = hist['Open'].iloc[0]
        change = latest_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
        
        return {
            "symbol": symbol,
            "name": name,
            "price": round(latest_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "fallback": False
        }
    except Exception as e:
        logger.warning(f"⚠️ Warning: Skipping {symbol} due to error: {str(e)}")
        default_data = DEFAULT_CRYPTO_DATA.get(symbol, {"name": symbol, "price": 0, "change": 0, "change_percent": 0})
        return {
            "symbol": symbol,
            "name": default_data["name"],
            "price": default_data["price"],
            "change": default_data["change"],
            "change_percent": default_data["change_percent"],
            "fallback": True
        }

@cache_result(expire_seconds=900)  # 缓存15分钟
async def get_top_cryptos(limit=5):
    # 热门加密货币列表
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "ADA-USD", "DOGE-USD"][:limit]
    
    try:
        # 并行获取所有加密货币数据
        coros = [_fetch_crypto(symbol) for symbol in symbols]
        results = await asyncio.gather(*coros, return_exceptions=True)
        
        # 处理返回的结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                symbol = symbols[i]
                default_data = DEFAULT_CRYPTO_DATA.get(symbol, {"name": symbol, "price": 0, "change": 0, "change_percent": 0})
                valid_results.append({
                    "symbol": symbol,
                    "name": default_data["name"],
                    "price": default_data["price"],
                    "change": default_data["change"],
                    "change_percent": default_data["change_percent"],
                    "fallback": True
                })
            else:
                valid_results.append(result)
        
        if not valid_results:
            logger.error("❌ No valid crypto data fetched.")
            # 如果所有数据都获取失败，返回默认数据
            return [
                {
                    "symbol": symbol,
                    "name": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("name", symbol),
                    "price": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("price", 0),
                    "change": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("change", 0),
                    "change_percent": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("change_percent", 0),
                    "fallback": True
                }
                for symbol in symbols
            ]
        
        return valid_results
        
    except Exception as e:
        logger.error(f"获取加密货币失败: {str(e)}")
        # 返回默认数据
        return [
            {
                "symbol": symbol,
                "name": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("name", symbol),
                "price": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("price", 0),
                "change": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("change", 0),
                "change_percent": DEFAULT_CRYPTO_DATA.get(symbol, {}).get("change_percent", 0),
                "fallback": True
            }
            for symbol in symbols
        ]

# ------------------------------------------------------------------------------------
COMMON_CRYPTOS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "ADA-USD", "DOGE-USD",
    "DOT-USD", "AVAX-USD", "MATIC-USD", "LINK-USD", "LTC-USD", "SHIB-USD", "UNI-USD"
]

@cache_result(expire_seconds=600)  # 缓存10分钟
async def search_cryptos(query):
    """
    搜索加密货币
    """
    if not query or len(query) < 1:
        return []

    query = query.upper()
    results = []
    
    try:
        # 尝试匹配常见加密货币
        matched_symbols = []
        
        # 直接匹配
        for symbol in COMMON_CRYPTOS:
            clean_symbol = symbol.replace("-USD", "")
            if query == clean_symbol or query == symbol:
                matched_symbols.append(symbol)
                break
                
        # 部分匹配
        if not matched_symbols:
            matched_symbols = [s for s in COMMON_CRYPTOS if query in s.replace("-USD", "")]
        
        # 获取匹配的加密货币详情
        for symbol in matched_symbols[:5]:
            crypto = await get_crypto_details(symbol)
            if crypto:
                results.append(crypto)
        
        return results
    except Exception as e:
        logger.error(f"搜索加密货币失败: {str(e)}")
        return []

@cache_result(expire_seconds=300)  # 缓存5分钟
async def get_crypto_details(symbol):
    """
    获取单个加密货币的详细信息
    """
    # 确保符号格式正确
    if not symbol.endswith("-USD"):
        symbol = f"{symbol}-USD"
        
    try:
        return await _fetch_crypto(symbol)
    except Exception as e:
        logger.error(f"获取加密货币详情失败 {symbol}: {str(e)}")
        default_data = DEFAULT_CRYPTO_DATA.get(symbol, {"name": symbol, "price": 0, "change": 0, "change_percent": 0})
        return {
            "symbol": symbol,
            "name": default_data["name"],
            "price": default_data["price"],
            "change": default_data["change"],
            "change_percent": default_data["change_percent"],
            "fallback": True
        }