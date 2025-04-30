# backend/tools/news_utils.py

import os
import requests
from datetime import datetime
import pytz
import humanize
from dateutil import parser

# 读取 API Key
EODHD_API_KEY = os.getenv("EODHD_API_KEY")
BASE_URL = "https://eodhd.com/api"

def convert_utc_to_et(utc_time_str: str) -> str:
    """
    将 ISO 格式的 UTC 时间字符串，转换成美国东部时间（ET）
    """
    utc_dt = parser.isoparse(utc_time_str)
    et_tz = pytz.timezone('US/Eastern')
    et_dt = utc_dt.astimezone(et_tz)
    return et_dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def get_time_ago(utc_time_str: str) -> str:
    """
    将 UTC 时间字符串转换为 '多久前' 的自然语言描述
    """
    utc_dt = parser.isoparse(utc_time_str)
    now = datetime.now(pytz.utc)
    return humanize.naturaltime(now - utc_dt)

def get_latest_market_news(limit=10):
    """
    从 EODHD API 获取最新的金融新闻列表
    返回的数据结构包括标题、链接、发布时间(ET)、多久前、情绪得分
    """
    news_url = f"{BASE_URL}/news?offset=0&limit={limit}&api_token={EODHD_API_KEY}&fmt=json"
    try:
        response = requests.get(news_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching latest news: {e}")
        return []

    news_items = response.json()

    if not isinstance(news_items, list):
        print(f"❌ Unexpected news format: {news_items}")
        return []

    news_list = []
    for item in news_items:
        published_raw = item.get("date", "")
        if not published_raw:
            continue  # Skip items without publish date

        news_list.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "published_at": convert_utc_to_et(published_raw),
            "time_ago": get_time_ago(published_raw),
            "scores": item.get("sentiment", {})  # 可能是空字典
        })

    return news_list
