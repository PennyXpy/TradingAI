# NewsAPI Client for Financial News Collection
# Based on official NewsAPI documentation: https://newsapi.org/docs

import aiohttp
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """News article data from NewsAPI"""
    title: str
    description: str
    content: str
    url: str
    source_name: str
    author: Optional[str]
    published_at: datetime
    url_to_image: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "url": self.url,
            "source_name": self.source_name,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "url_to_image": self.url_to_image,
            "published_date": self.published_at.strftime("%Y-%m-%d") if self.published_at else None
        }

class NewsAPIClient:
    """
    Client for NewsAPI.org financial news collection
    
    Based on NewsAPI documentation:
    - Everything endpoint for comprehensive search
    - Top Headlines for breaking news
    - Supports financial keywords and filtering
    """
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={"X-API-Key": self.api_key},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to NewsAPI"""
        if not self.session:
            raise RuntimeError("NewsAPIClient must be used as async context manager")
            
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get("status") != "ok":
                    error_code = data.get("code", "unknown")
                    error_message = data.get("message", "Unknown error")
                    raise Exception(f"NewsAPI error {error_code}: {error_message}")
                    
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error making request to {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            raise
            
    def _parse_articles(self, articles_data: List[Dict[str, Any]]) -> List[NewsArticle]:
        """Parse articles from NewsAPI response"""
        articles = []
        
        for article_data in articles_data:
            try:
                # Parse published date
                published_at = None
                if article_data.get("publishedAt"):
                    published_at = datetime.fromisoformat(
                        article_data["publishedAt"].replace("Z", "+00:00")
                    )
                
                article = NewsArticle(
                    title=article_data.get("title", ""),
                    description=article_data.get("description", ""),
                    content=article_data.get("content", ""),
                    url=article_data.get("url", ""),
                    source_name=article_data.get("source", {}).get("name", ""),
                    author=article_data.get("author"),
                    published_at=published_at,
                    url_to_image=article_data.get("urlToImage")
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Error parsing article: {e}")
                continue
                
        return articles
        
    async def get_everything(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
        page: int = 1
    ) -> List[NewsArticle]:
        """
        Search for articles using the Everything endpoint
        
        Args:
            query: Keywords or phrases to search for
            sources: List of news sources or blogs (e.g., ['bbc-news', 'techcrunch'])
            domains: List of domains to restrict search to (e.g., ['bbc.co.uk'])
            exclude_domains: List of domains to exclude
            from_date: Oldest article date
            to_date: Newest article date  
            language: Language code (default: 'en')
            sort_by: Sort order ('relevancy', 'popularity', 'publishedAt')
            page_size: Number of articles per page (max 100)
            page: Page number for pagination
            
        Returns:
            List of NewsArticle objects
        """
        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100),
            "page": page
        }
        
        if sources:
            params["sources"] = ",".join(sources)
        if domains:
            params["domains"] = ",".join(domains)
        if exclude_domains:
            params["excludeDomains"] = ",".join(exclude_domains)
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
            
        data = await self._make_request("everything", params)
        articles = self._parse_articles(data.get("articles", []))
        
        logger.info(f"Retrieved {len(articles)} articles for query: {query}")
        return articles
        
    async def get_top_headlines(
        self,
        country: Optional[str] = None,
        category: Optional[str] = None,
        sources: Optional[List[str]] = None,
        query: Optional[str] = None,
        page_size: int = 20,
        page: int = 1
    ) -> List[NewsArticle]:
        """
        Get top headlines using the Top Headlines endpoint
        
        Args:
            country: Country code (e.g., 'us', 'gb')
            category: Category ('business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology')
            sources: List of news sources
            query: Keywords to search for in headlines
            page_size: Number of articles per page (max 100)
            page: Page number for pagination
            
        Returns:
            List of NewsArticle objects
        """
        params = {
            "pageSize": min(page_size, 100),
            "page": page
        }
        
        if country:
            params["country"] = country
        if category:
            params["category"] = category
        if sources:
            params["sources"] = ",".join(sources)
        if query:
            params["q"] = query
            
        data = await self._make_request("top-headlines", params)
        articles = self._parse_articles(data.get("articles", []))
        
        logger.info(f"Retrieved {len(articles)} top headlines")
        return articles
        
    async def get_financial_news(
        self,
        symbols: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 20,
        days_back: int = 7
    ) -> List[NewsArticle]:
        """
        Get financial news with stock-specific filtering
        
        Args:
            symbols: Stock symbols to search for (e.g., ['AAPL', 'GOOGL'])
            keywords: Additional financial keywords
            limit: Maximum number of articles to return
            days_back: Number of days to look back
            
        Returns:
            List of NewsArticle objects
        """
        # Build search query
        query_parts = []
        
        # Add stock symbols
        if symbols:
            symbol_query = " OR ".join([f'"{symbol}"' for symbol in symbols])
            query_parts.append(f"({symbol_query})")
            
        # Add financial keywords
        financial_keywords = keywords or [
            "stock market", "earnings", "financial", "trading", 
            "investment", "NYSE", "NASDAQ", "SEC", "Federal Reserve"
        ]
        
        if financial_keywords:
            keyword_query = " OR ".join([f'"{keyword}"' for keyword in financial_keywords])
            query_parts.append(f"({keyword_query})")
            
        # Combine query parts
        if query_parts:
            query = " AND ".join(query_parts)
        else:
            query = "financial OR stock OR market"
            
        # Set date range
        from_date = datetime.now() - timedelta(days=days_back)
        
        # Get articles using Everything endpoint
        articles = await self.get_everything(
            query=query,
            from_date=from_date,
            sort_by="publishedAt",
            page_size=limit,
            language="en"
        )
        
        return articles
        
    async def get_business_headlines(self, country: str = "us", limit: int = 20) -> List[NewsArticle]:
        """
        Get business category headlines
        
        Args:
            country: Country code for headlines
            limit: Maximum number of articles
            
        Returns:
            List of NewsArticle objects
        """
        articles = await self.get_top_headlines(
            country=country,
            category="business",
            page_size=limit
        )
        
        return articles
        
    async def get_company_news(
        self,
        company_name: str,
        symbol: Optional[str] = None,
        limit: int = 10,
        days_back: int = 30
    ) -> List[NewsArticle]:
        """
        Get news for a specific company
        
        Args:
            company_name: Company name to search for
            symbol: Stock symbol (optional)
            limit: Maximum number of articles
            days_back: Number of days to look back
            
        Returns:
            List of NewsArticle objects
        """
        # Build query for company
        query_parts = [f'"{company_name}"']
        if symbol:
            query_parts.append(f'"{symbol}"')
            
        query = " OR ".join(query_parts)
        
        from_date = datetime.now() - timedelta(days=days_back)
        
        articles = await self.get_everything(
            query=query,
            from_date=from_date,
            sort_by="relevancy",
            page_size=limit,
            language="en"
        )
        
        return articles
        
    async def get_market_news(self, limit: int = 15) -> List[NewsArticle]:
        """
        Get general market news
        
        Args:
            limit: Maximum number of articles
            
        Returns:
            List of NewsArticle objects
        """
        market_keywords = [
            "stock market", "market analysis", "market outlook",
            "trading", "S&P 500", "Dow Jones", "NASDAQ",
            "market volatility", "market trends"
        ]
        
        query = " OR ".join([f'"{keyword}"' for keyword in market_keywords])
        
        articles = await self.get_everything(
            query=query,
            sort_by="publishedAt",
            page_size=limit,
            language="en"
        )
        
        return articles


# Financial news sources (reputable financial news outlets)
FINANCIAL_NEWS_SOURCES = [
    "bloomberg",
    "financial-times", 
    "the-wall-street-journal",
    "cnbc",
    "marketwatch",
    "reuters",
    "associated-press",
    "cnn",
    "bbc-news"
]

# Example usage and testing
async def example_usage():
    """Example of how to use the NewsAPI client"""
    
    # Get API key from environment
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.error("NEWS_API_KEY not found in environment variables")
        return
        
    async with NewsAPIClient(api_key) as client:
        
        # Get financial news for specific stocks
        print("=== Financial News for AAPL and GOOGL ===")
        financial_news = await client.get_financial_news(
            symbols=["AAPL", "GOOGL"],
            limit=5
        )
        
        for article in financial_news[:3]:
            print(f"Title: {article.title}")
            print(f"Source: {article.source_name}")
            print(f"Published: {article.published_at}")
            print(f"URL: {article.url}")
            print("-" * 50)
            
        # Get business headlines
        print("\n=== Business Headlines ===")
        business_headlines = await client.get_business_headlines(limit=5)
        
        for article in business_headlines[:3]:
            print(f"Title: {article.title}")
            print(f"Source: {article.source_name}")
            print("-" * 50)
            
        # Get market news
        print("\n=== Market News ===")
        market_news = await client.get_market_news(limit=5)
        
        for article in market_news[:3]:
            print(f"Title: {article.title}")
            print(f"Source: {article.source_name}")
            print("-" * 50)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())