# backend/tools/news_search_summary_pipeline.py

import os
import requests
from urllib.parse import unquote
from firecrawl import FirecrawlApp
from llm_client import summarize_content_with_deepseek
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY") # Google Search API

# 初始化 Firecrawl
firecrawl_client = FirecrawlApp(api_key=FIRECRAWL_API_KEY)


# 快速搜索函数
def search_news_online(query):
    print(f"🔍 Searching for: {query}")
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google",
        "num": "3"
    }
    search_url = "https://serpapi.com/search"
    response = requests.get(search_url, params=params)
    data = response.json()

    if "organic_results" not in data or not data["organic_results"]:
        print("❌ No search results found.")
        return None

    top_result_url = data["organic_results"][0]["link"]
    print(f"🔗 Top Result URL: {top_result_url}")
    return top_result_url

def fetch_page_content(url):
    print(f"🌐 Fetching page: {url}")
    page_content = firecrawl_client.scrape_url(
        url
    #     param={
    #         'limit': 1,
    #         'scrapeOptions': {
	# 'formats': [ 'markdown' ],
    #         }
    # }
    )
    # print(page)
    return page_content

def summarize_and_save(news_title):
    # 1. 搜索新闻
    top_url = search_news_online(news_title)
    if not top_url:
        return None

    # 2. 抓取页面正文
    page_text = fetch_page_content(top_url)
    if not page_text:
        print("⚠️ No text extracted.")
        return None

    # 3. 使用 DeepSeek 总结
    summary = summarize_content_with_deepseek(page_text)

    # 4. 打印结果
    result = {
        "news_title": news_title,
        "source_url": top_url,
        "summary": summary
    }
    print("\n📢 Final Result:")
    print(result)
    return result

if __name__ == "__main__":
    test_news = "The Five Answers Tesla Investors Need During Earnings"
    summarize_and_save(test_news)
