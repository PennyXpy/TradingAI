# backend/service/pages_routes.py

from fastapi import APIRouter
from tools.market_indexes import get_market_indexes  
from tools.stock_utils import get_top_traded_stocks
from tools.crypto_utils import get_top_cryptos
from tools.news_utils import get_latest_market_news


router = APIRouter()

@router.get("/market/indexes")
async def market_indexes():
    """
    返回主要指数及迷你 sparkline
    """
    return await get_market_indexes()

@router.get("/stocks/top")
async def top_stocks():
    return await get_top_traded_stocks(limit=5)

@router.get("/cryptos/top")
async def top_cryptos():
    return await get_top_cryptos(limit=5)

@router.get("/news/latest")
async def latest_news():
    return get_latest_market_news(limit=5)
