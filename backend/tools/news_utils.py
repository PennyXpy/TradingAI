import os
import logging
import requests
import asyncio
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import humanize
from dateutil import parser
from .cache import cache_result

logger = logging.getLogger(__name__)

# 读取 API Key
EODHD_API_KEY = os.getenv("EODHD_API_KEY")
BASE_URL = "https://eodhd.com/api"

# ====================== 时间工具函数 ======================

def convert_utc_to_et(utc_time_str: str) -> str:
    """将 ISO 格式的 UTC 时间字符串，转换成美国东部时间（ET）"""
    utc_dt = parser.isoparse(utc_time_str)
    et_tz = pytz.timezone('US/Eastern')
    et_dt = utc_dt.astimezone(et_tz)
    return et_dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def get_time_ago(utc_time_str: str) -> str:
    """将 UTC 时间字符串转换为 '多久前' 的自然语言描述"""
    utc_dt = parser.isoparse(utc_time_str)
    now = datetime.now(pytz.utc)
    return humanize.naturaltime(now - utc_dt)

# ====================== EODHD API 实现 ======================

def get_eodhd_market_news(limit=10):
    """
    从 EODHD API 获取最新的金融新闻列表
    
    注意：此函数使用EODHD API，需要API密钥
    """
    if not EODHD_API_KEY:
        logger.warning("EODHD API密钥未设置，无法获取EODHD新闻")
        return []
        
    news_url = f"{BASE_URL}/news?offset=0&limit={limit}&api_token={EODHD_API_KEY}&fmt=json"
    try:
        response = requests.get(news_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"获取EODHD新闻失败: {e}")
        return []

    news_items = response.json()

    if not isinstance(news_items, list):
        logger.error(f"意外的EODHD新闻格式: {news_items}")
        return []

    news_list = []
    for item in news_items:
        published_raw = item.get("date", "")
        if not published_raw:
            continue  # 跳过没有发布日期的新闻

        news_list.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "published_at": convert_utc_to_et(published_raw),
            "time_ago": get_time_ago(published_raw),
            "source": item.get("source", ""),
            "sentiment": item.get("sentiment", {}),  # 可能是空字典
            "description": item.get("summary", "")
        })

    return news_list
# --------------------------------------------------------------

@cache_result(expire_seconds=1800)  # 缓存30分钟
async def get_stock_related_news_EODHO(symbol, limit=10):
    """
    从 EODHD API 获取最新的金融新闻列表
    
    注意：此函数使用EODHD API，需要API密钥
    """
    if not EODHD_API_KEY:
        logger.warning("EODHD API密钥未设置，无法获取EODHD新闻")
        return []
        
    news_url = f"{BASE_URL}/news?s={symbol}&offset=0&limit={limit}&api_token={EODHD_API_KEY}&fmt=json"
    try:
        response = requests.get(news_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"获取EODHD新闻失败: {e}")
        return []

    news_items = response.json()

    if not isinstance(news_items, list):
        logger.error(f"意外的EODHD新闻格式: {news_items}")
        return []

    news_list = []
    for item in news_items:
        published_raw = item.get("date", "")
        if not published_raw:
            continue  # 跳过没有发布日期的新闻

        news_list.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "published_at": convert_utc_to_et(published_raw),
            "time_ago": get_time_ago(published_raw),
            "source": item.get("source", ""),
            "sentiment": item.get("sentiment", {}),  # 可能是空字典
            "description": item.get("summary", "")
        })

    return news_list

# ====================== YFinance API 实现 ======================

@cache_result(expire_seconds=1800)  # 缓存30分钟
async def get_stock_related_news(symbol, limit=5, tab='news'):
    """
    使用yfinance API获取与特定股票相关的新闻
    
    参数:
        symbol: 股票代码
        limit: 返回新闻数量
        tab: 新闻类型，可以是'news'(普通新闻)或'press releases'(新闻发布)
    """
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.get_news(count=limit, tab=tab)
        
        # 处理返回的新闻数据
        formatted_news = []
        for item in news:
            # 提取来源信息
            source = item.get('publisher', '')
            if isinstance(source, dict):
                source = source.get('name', '')
            
            # 格式化时间
            publish_time = datetime.fromtimestamp(item.get('providerPublishTime', 0))
            
            formatted_news.append({
                "title": item.get('title', ''),
                "description": item.get('summary', ''),
                "url": item.get('link', ''),
                "source": source,
                "publishedAt": publish_time.isoformat(),
                "thumbnail": item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '')
            })
        
        return formatted_news
    except Exception as e:
        logger.error(f"获取股票相关新闻失败 {symbol}: {str(e)}")
        return []

# ---------------------------------------------------------------------- 上面这个function可能吊用没有

@cache_result(expire_seconds=1800)  # 缓存30分钟
async def get_latest_market_news(limit=5):
    """
    获取最新市场新闻
    
    优先使用EODHD API，若失败则回退到yfinance API
    """
    try:
        # 首先尝试使用EODHD API
        if EODHD_API_KEY:
            eodhd_news = get_eodhd_market_news(limit)
            if eodhd_news and len(eodhd_news) > 0:
                return eodhd_news
        
        # 如果EODHD API失败或未配置，使用yfinance API
        # 使用市场ETF获取大盘新闻
        market_symbols = ["SPY", "QQQ", "DIA", "IWM"]  # S&P500, 纳指, 道指, 罗素2000
        
        all_news = []
        for symbol in market_symbols:
            try:
                ticker = yf.Ticker(symbol)
                news = ticker.get_news(count=int(limit/len(market_symbols)) + 1)
                
                for item in news:
                    # 提取来源信息
                    source = item.get('publisher', '')
                    if isinstance(source, dict):
                        source = source.get('name', '')
                    
                    # 格式化时间
                    publish_time = datetime.fromtimestamp(item.get('providerPublishTime', 0))
                    
                    all_news.append({
                        "title": item.get('title', ''),
                        "description": item.get('summary', ''),
                        "url": item.get('link', ''),
                        "source": source,
                        "publishedAt": publish_time.isoformat(),
                        "relatedSymbol": symbol,
                        "thumbnail": item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '')
                    })
            except Exception as e:
                logger.warning(f"获取{symbol}新闻失败: {str(e)}")
                continue
        
        # 去重 - 根据新闻标题去重
        unique_titles = set()
        unique_news = []
        
        for item in all_news:
            if item['title'] not in unique_titles:
                unique_titles.add(item['title'])
                unique_news.append(item)
        
        # 按发布时间排序
        unique_news.sort(key=lambda x: x["publishedAt"], reverse=True)
        
        return unique_news[:limit]
    except Exception as e:
        logger.error(f"获取市场新闻失败: {str(e)}")
        return []

@cache_result(expire_seconds=3600)  # 缓存1小时
async def get_portfolio_news(symbols, limit=10):
    """
    获取投资组合相关新闻 - 适用于用户的关注和投资列表
    
    参数:
        symbols: 股票代码列表
        limit: 返回新闻总数量
    """
    if not symbols or len(symbols) == 0:
        return []
        
    try:
        # 计算每个股票应获取的新闻数量
        news_per_symbol = max(1, round(limit / len(symbols)))
        
        all_news = []
        tasks = []
        
        # 创建异步任务获取每个股票的新闻
        for symbol in symbols:
            tasks.append(get_stock_related_news(symbol, news_per_symbol))
            #get_eodhd_market_news
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"获取{symbols[i]}新闻失败: {str(result)}")
                continue
                
            # 添加股票标识
            for news_item in result:
                news_item["relatedSymbol"] = symbols[i]
            
            all_news.extend(result)
        
        # 去重 - 根据新闻标题去重
        unique_titles = set()
        unique_news = []
        
        for item in all_news:
            if item['title'] not in unique_titles:
                unique_titles.add(item['title'])
                unique_news.append(item)
        
        # 按发布时间排序
        unique_news.sort(key=lambda x: x["publishedAt"], reverse=True)
        
        return unique_news[:limit]
    except Exception as e:
        logger.error(f"获取投资组合新闻失败: {str(e)}")
        return []