import yfinance as yf
import logging
import asyncio
from .cache import cache_result

logger = logging.getLogger(__name__)

# 常用股票默认数据
DEFAULT_STOCK_DATA = {
    "AAPL": {"name": "Apple Inc.", "price": 175.0, "change": 0, "change_percent": 0},
    "MSFT": {"name": "Microsoft Corporation", "price": 350.0, "change": 0, "change_percent": 0},
    "AMZN": {"name": "Amazon.com, Inc.", "price": 130.0, "change": 0, "change_percent": 0},
    "GOOGL": {"name": "Alphabet Inc.", "price": 150.0, "change": 0, "change_percent": 0},
    "META": {"name": "Meta Platforms, Inc.", "price": 340.0, "change": 0, "change_percent": 0},
    "TSLA": {"name": "Tesla, Inc.", "price": 240.0, "change": 0, "change_percent": 0},
    "NVDA": {"name": "NVIDIA Corporation", "price": 800.0, "change": 0, "change_percent": 0},
    # 可以添加更多默认数据
}

async def _fetch_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        
        if hist.empty:
            logger.warning(f"⚠️ {symbol} 没有返回数据")
            raise ValueError(f"No data for {symbol}")
            
        # 获取公司信息
        try:
            info = ticker.info
            name = info.get('shortName', symbol)
        except:
            name = DEFAULT_STOCK_DATA.get(symbol, {}).get("name", symbol)
        
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
        logger.error(f"❌ Error fetching {symbol}: {str(e)}")
        default_data = DEFAULT_STOCK_DATA.get(symbol, {"name": symbol, "price": 0, "change": 0, "change_percent": 0})
        return {
            "symbol": symbol,
            "name": default_data["name"],
            "price": default_data["price"],
            "change": default_data["change"],
            "change_percent": default_data["change_percent"],
            "fallback": True
        }

@cache_result(expire_seconds=900)  # 缓存15分钟
async def get_top_traded_stocks(limit=5):
    # 热门科技股列表
    symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"][:limit]
    
    try:
        # 并行获取所有股票数据
        coros = [_fetch_stock(symbol) for symbol in symbols]
        results = await asyncio.gather(*coros, return_exceptions=True)
        
        # 处理返回的结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                symbol = symbols[i]
                default_data = DEFAULT_STOCK_DATA.get(symbol, {"name": symbol, "price": 0, "change": 0, "change_percent": 0})
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
        
        return valid_results
        
    except Exception as e:
        logger.error(f"获取热门股票失败: {str(e)}")
        # 返回默认数据
        return [
            {
                "symbol": symbol,
                "name": DEFAULT_STOCK_DATA.get(symbol, {}).get("name", symbol),
                "price": DEFAULT_STOCK_DATA.get(symbol, {}).get("price", 0),
                "change": DEFAULT_STOCK_DATA.get(symbol, {}).get("change", 0),
                "change_percent": DEFAULT_STOCK_DATA.get(symbol, {}).get("change_percent", 0),
                "fallback": True
            }
            for symbol in symbols
        ]
        
# ------------------------------------------------------------------
# 新增常见股票列表 - 用于搜索功能
COMMON_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
    "JPM", "V", "JNJ", "WMT", "PG", "NFLX", "DIS", "BAC", 
    "INTC", "CSCO", "XOM", "CMCSA", "PFE", "T", "VZ", "KO"
]

# 新增函数 - 股票搜索
@cache_result(expire_seconds=600)  # 缓存10分钟
async def search_stocks(query):
    """
    搜索股票，根据查询字符串匹配股票代码或公司名称
    """
    if not query or len(query) < 1:
        return []

    query = query.upper()
    results = []
    
    try:
        # 直接匹配
        if query in COMMON_STOCKS:
            stock = await get_stock_details(query)
            if stock:
                return [stock]
        
        # 部分匹配
        matched_symbols = [s for s in COMMON_STOCKS if query in s]
        
        # 并行获取匹配的股票详情
        coroutines = [get_stock_details(symbol) for symbol in matched_symbols[:10]]
        results = await asyncio.gather(*coroutines)
        
        # 过滤掉None值
        results = [r for r in results if r]
        
        # 如果没有结果，尝试使用yfinance的ticker查询
        if not results and len(query) >= 2:
            try:
                ticker = yf.Ticker(query)
                info = ticker.info
                if 'symbol' in info:
                    stock = await get_stock_details(query)
                    if stock:
                        results.append(stock)
            except Exception as e:
                logger.warning(f"yfinance搜索失败: {str(e)}")
        
        return results
    except Exception as e:
        logger.error(f"搜索股票失败: {str(e)}")
        return []

# 新增函数 - 获取股票详情
@cache_result(expire_seconds=300)  # 缓存5分钟
async def get_stock_details(symbol):
    """
    获取单个股票的详细信息，包括价格、变化等
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # 获取当日股票数据
        hist = ticker.history(period="1d")
        if hist.empty:
            logger.warning(f"{symbol} 没有返回数据")
            return use_default_stock_data(symbol)
            
        # 获取公司信息
        info = {}
        try:
            info = ticker.info
        except Exception as e:
            logger.warning(f"无法获取{symbol}的信息: {str(e)}")
            
        # 提取基本信息
        name = info.get('shortName', info.get('longName', symbol))
        sector = info.get('sector', '')
        industry = info.get('industry', '')
        
        # 计算价格变化
        latest_price = hist['Close'].iloc[-1]
        prev_close = hist['Open'].iloc[0]
        change = latest_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
        
        # 额外市场数据
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 0)
        dividend_yield = info.get('dividendYield', 0)
        
        return {
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "industry": industry,
            "price": round(latest_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "dividend_yield": dividend_yield * 100 if dividend_yield else 0,
            "volume": int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0,
            "fallback": False
        }
    except Exception as e:
        logger.error(f"获取股票详情失败 {symbol}: {str(e)}")
        return use_default_stock_data(symbol)

def use_default_stock_data(symbol):
    """当API调用失败时返回默认数据"""
    if symbol in DEFAULT_STOCK_DATA:
        data = DEFAULT_STOCK_DATA[symbol].copy()
        data["symbol"] = symbol
        data["fallback"] = True
        return data
    return {
        "symbol": symbol,
        "name": f"{symbol} Inc.",
        "sector": "",
        "industry": "",
        "price": 0,
        "change": 0,
        "change_percent": 0,
        "market_cap": 0,
        "pe_ratio": 0,
        "dividend_yield": 0,
        "volume": 0,
        "fallback": True
    }

# 新增函数 - 获取股票历史数据
@cache_result(expire_seconds=3600)  # 缓存1小时
async def get_stock_historical_data(symbol, period="1mo", interval="1d"):
    """
    获取股票历史数据，用于图表显示
    
    参数:
        symbol: 股票代码
        period: 时间范围 (1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max)
        interval: 时间间隔 (1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo)
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return {"error": "无数据"}
        
        # 将数据转换为前端友好的格式
        data = []
        for index, row in hist.iterrows():
            data.append({
                "date": index.strftime('%Y-%m-%d %H:%M:%S'),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })
        
        return data
    except Exception as e:
        logger.error(f"获取股票历史数据失败 {symbol}: {str(e)}")
        return {"error": str(e)}