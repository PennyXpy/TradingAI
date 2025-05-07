from fastapi import APIRouter, Query
from typing import Optional, List
from tools.market_indexes import get_market_indexes  
from tools.stock_utils import get_top_traded_stocks, search_stocks, get_stock_details, get_stock_historical_data
from tools.crypto_utils import get_top_cryptos, search_cryptos, get_crypto_details
from tools.news_utils import get_latest_market_news, get_stock_related_news, get_portfolio_news


router = APIRouter()

@router.get("/market/indexes")
async def market_indexes():
    """
    返回主要指数及迷你图表数据
    """
    return await get_market_indexes()

@router.get("/stocks/top")
async def top_stocks(limit: int = Query(5, ge=1, le=10)):
    """
    获取热门股票列表
    """
    return await get_top_traded_stocks(limit=limit)

@router.get("/cryptos/top")
async def top_cryptos(limit: int = Query(5, ge=1, le=10)):
    """
    获取热门加密货币列表
    """
    return await get_top_cryptos(limit=limit)

@router.get("/news/latest")
async def latest_news(limit: int = Query(5, ge=1, le=10)):
    """
    获取最新市场新闻
    """
    return await get_latest_market_news(limit=limit)

@router.get("/stocks/search")
async def stocks_search(query: str, limit: int = Query(10, ge=1, le=20)):
    """
    搜索股票
    """
    results = await search_stocks(query)
    return results[:limit]

@router.get("/stocks/details")
async def stock_details(symbol: str):
    """
    获取单个股票的详细信息
    """
    result = await get_stock_details(symbol)
    if not result:
        return {"error": "无法获取股票详情"}
    return result

@router.get("/cryptos/search")
async def cryptos_search(query: str, limit: int = Query(10, ge=1, le=20)):
    """
    搜索加密货币
    """
    results = await search_cryptos(query)
    return results[:limit]

@router.get("/cryptos/details")
async def crypto_details(symbol: str):
    """
    获取单个加密货币的详细信息
    """
    result = await get_crypto_details(symbol)
    if not result:
        return {"error": "无法获取加密货币详情"}
    return result

@router.get("/news/related")
async def related_news(symbol: str, limit: int = Query(5, ge=1, le=10), tab: str = Query('news')):
    """
    获取与特定股票相关的新闻
    
    参数:
        symbol: 股票代码
        limit: 返回新闻数量
        tab: 新闻类型, 'news'(普通新闻) 或 'press releases'(新闻发布)
    """
    return await get_stock_related_news(symbol, limit, tab)

@router.get("/news/portfolio")
async def portfolio_news(symbols: str, limit: int = Query(10, ge=1, le=20)):
    """
    获取与多个股票相关的新闻
    
    参数:
        symbols: 逗号分隔的股票代码列表, 例如 "AAPL,MSFT,GOOGL"
        limit: 返回新闻总数量
    """
    symbol_list = symbols.split(',')
    # 去重并移除空字符串
    symbol_list = list(set([s.strip() for s in symbol_list if s.strip()]))
    
    return await get_portfolio_news(symbol_list, limit)

@router.get("/stocks/history")
async def stock_history(
    symbol: str, 
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    interval: str = Query("1d", regex="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$")
):
    """
    获取股票历史数据，用于图表
    """
    return await get_stock_historical_data(symbol, period, interval)