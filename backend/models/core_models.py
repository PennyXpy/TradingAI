# TradingAI Core Database Models
# This module contains the core database schema for the TradingAI application
# Includes user management, financial instruments, portfolios, news storage, and agent context

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import json

# ================================================================================
# ENUMS FOR TYPE SAFETY
# ================================================================================

class InstrumentType(str, Enum):
    """
    Defines the types of financial instruments supported in the system
    - STOCK: Individual company stocks (e.g., AAPL, GOOGL)
    - ETF: Exchange-Traded Funds (e.g., SPY, QQQ)
    - CRYPTO: Cryptocurrencies (future expansion)
    """
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"

class AlertType(str, Enum):
    """
    Defines different types of alerts that can be triggered
    - PRICE: Price movement alerts (up/down thresholds)
    - NEWS: News-based alerts for followed instruments
    - EARNINGS: Earnings report notifications
    - VOLUME: Unusual volume activity alerts
    """
    PRICE = "price"
    NEWS = "news"  
    EARNINGS = "earnings"
    VOLUME = "volume"

class DataType(str, Enum):
    """
    Defines types of data stored in market cache
    - PRICE: Current and historical price data
    - VOLUME: Trading volume information
    - TECHNICAL: Technical indicators (RSI, MA, etc.)
    - FUNDAMENTALS: Company fundamentals (P/E, market cap, etc.)
    """
    PRICE = "price"
    VOLUME = "volume"
    TECHNICAL = "technical"
    FUNDAMENTALS = "fundamentals"

# ================================================================================
# ENHANCED USER & AUTHENTICATION MODELS
# ================================================================================

class User(SQLModel, table=True):
    """
    Enhanced User model for Phase 1 with tracking and preferences
    
    This model extends the basic user functionality to include:
    - Login tracking for user activity analysis
    - User preferences for personalized experience
    - Relationships to followings, investments, agent contexts, and alerts
    
    Key improvements from original:
    - Added last_login tracking for user engagement metrics
    - Added preferences JSON field for user customization
    - Enhanced relationship mapping for new Phase 1 models
    """
    __tablename__ = "users"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True
    
    # Phase 1 enhancements
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    preferences: Optional[str] = Field(default="{}")  # JSON string for user preferences
    
    # Relationships to other models
    user_sessions: List["UserSession"] = Relationship(back_populates="user")
    user_followings: List["UserFollowing"] = Relationship(back_populates="user")
    agent_contexts: List["AgentContext"] = Relationship(back_populates="user")
    alerts: List["Alert"] = Relationship(back_populates="user")

    def get_preferences(self) -> Dict[str, Any]:
        """Helper method to parse preferences JSON"""
        try:
            return json.loads(self.preferences or "{}")
        except:
            return {}
    
    def set_preferences(self, prefs: Dict[str, Any]):
        """Helper method to set preferences as JSON"""
        self.preferences = json.dumps(prefs)

class UserSession(SQLModel, table=True):
    """
    Enhanced session management for user authentication tracking
    
    This model replaces the basic token model with:
    - Proper session management with expiration
    - User relationship for session tracking
    - Support for multiple concurrent sessions
    
    Use cases:
    - JWT token storage and validation
    - Session expiration management
    - User activity tracking
    - Multi-device session support
    """
    __tablename__ = "user_sessions"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationship
    user: User = Relationship(back_populates="user_sessions")

# ================================================================================
# FINANCIAL INSTRUMENTS & FOLLOWING SYSTEM
# ================================================================================

class Instrument(SQLModel, table=True):
    """
    Centralized financial instrument registry for stocks and ETFs
    
    This model serves as a master registry of all financial instruments:
    - Stocks: Individual company securities
    - ETFs: Exchange-traded funds
    - Future support for crypto and other instrument types
    
    Key features:
    - Normalized instrument data to avoid duplication
    - Sector classification for analysis
    - Market cap tracking for large/mid/small cap analysis
    - Automatic data refresh tracking
    
    This replaces the scattered symbol references in the original models
    """
    __tablename__ = "instruments"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    symbol: str = Field(unique=True, index=True)  # Stock/ETF ticker symbol
    name: str  # Full company/fund name
    type: InstrumentType  # stock/etf/crypto
    sector: Optional[str] = None  # Business sector (Technology, Healthcare, etc.)
    market_cap: Optional[float] = None  # Market capitalization in USD
    exchange: Optional[str] = None  # Exchange where traded (NYSE, NASDAQ, etc.)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user_followings: List["UserFollowing"] = Relationship(back_populates="instrument")
    market_cache: List["MarketCache"] = Relationship(back_populates="instrument")
    news_cache: List["NewsCache"] = Relationship(back_populates="instrument")

class UserFollowing(SQLModel, table=True):
    """
    Enhanced user following system with alert preferences
    
    This model tracks which instruments users follow with:
    - Alert enablement per instrument
    - Follow date tracking for analytics
    - Relationship to both user and instrument models
    
    Improvements from original FollowedAsset:
    - Links to normalized Instrument model instead of raw symbols
    - Alert configuration per following
    - Better relationship structure for complex queries
    """
    __tablename__ = "user_followings"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    instrument_id: str = Field(foreign_key="instruments.id", index=True)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    alert_enabled: bool = True  # Whether user wants alerts for this instrument
    
    # Relationships
    user: User = Relationship(back_populates="user_followings")
    instrument: Instrument = Relationship(back_populates="user_followings")
    
    # Composite unique constraint to prevent duplicate followings
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

# ================================================================================
# NEWS & INFORMATION STORAGE
# ================================================================================

class NewsArticle(SQLModel, table=True):
    """
    Centralized news article storage with sentiment analysis
    
    This model stores financial news articles with:
    - AI-powered sentiment scoring
    - Multi-symbol relevance tracking
    - Source attribution and deduplication
    
    Key features:
    - Sentiment score for AI analysis (-1.0 to 1.0)
    - Symbol array for multi-stock relevance
    - Content storage for full-text analysis
    - Publisher tracking for source credibility
    """
    __tablename__ = "news_articles"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    headline: str = Field(index=True)
    content: Optional[str] = None  # Full article content
    source: str  # News source (Reuters, Bloomberg, etc.)
    author: Optional[str] = None
    published_at: datetime = Field(index=True)
    sentiment_score: Optional[float] = None  # AI sentiment analysis (-1.0 to 1.0)
    symbols: str = Field(default="[]")  # JSON array of relevant symbols
    url: Optional[str] = None  # Original article URL
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    news_cache: List["NewsCache"] = Relationship(back_populates="article")
    
    def get_symbols(self) -> List[str]:
        """Helper method to parse symbols JSON array"""
        try:
            return json.loads(self.symbols)
        except:
            return []
    
    def set_symbols(self, symbols: List[str]):
        """Helper method to set symbols as JSON array"""
        self.symbols = json.dumps(symbols)

class NewsCache(SQLModel, table=True):
    """
    Optimized news-to-instrument mapping with relevance scoring
    
    This model creates efficient mappings between news articles and instruments:
    - Relevance scoring for ranking news by importance
    - Cached relationships for fast queries
    - Automatic cache expiration
    
    Use cases:
    - Fast retrieval of news for specific instruments
    - Relevance-based news ranking
    - Cache invalidation for fresh content
    """
    __tablename__ = "news_cache"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    instrument_id: str = Field(foreign_key="instruments.id", index=True)
    article_id: str = Field(foreign_key="news_articles.id", index=True)
    relevance_score: float = Field(default=1.0)  # 0.0 to 1.0 relevance ranking
    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    instrument: Instrument = Relationship(back_populates="news_cache")
    article: NewsArticle = Relationship(back_populates="news_cache")

class EarningReport(SQLModel, table=True):
    """
    Earnings report storage with price impact analysis
    
    This model stores quarterly earnings data with:
    - Financial summary information
    - Price impact correlation analysis
    - Historical earnings tracking
    
    Key features:
    - Quarter/year tracking for historical analysis
    - Price impact measurement for trading insights
    - Summary field for AI analysis
    - Symbol-based organization
    """
    __tablename__ = "earning_reports"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    symbol: str = Field(index=True)  # Stock symbol for the earnings
    quarter: int  # Quarter number (1-4)
    year: int  # Year of the earnings report
    summary: Optional[str] = None  # AI-generated earnings summary
    price_impact: Optional[float] = None  # Price change % after earnings
    eps_actual: Optional[float] = None  # Actual earnings per share
    eps_estimate: Optional[float] = None  # Estimated earnings per share
    revenue_actual: Optional[float] = None  # Actual revenue
    revenue_estimate: Optional[float] = None  # Estimated revenue
    report_date: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ================================================================================
# AGENT & CACHING INFRASTRUCTURE
# ================================================================================

class AgentContext(SQLModel, table=True):
    """
    AI Agent conversation context and analysis storage
    
    This model stores persistent agent state for each user:
    - Conversation history for context continuity
    - Last analysis results for quick reference
    - User-specific agent preferences
    
    Key features:
    - JSON conversation history storage
    - Analysis result caching
    - User-agent relationship tracking
    - Context versioning for updates
    """
    __tablename__ = "agent_contexts"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    conversation_history: str = Field(default="[]")  # JSON array of conversation
    last_analysis: Optional[str] = None  # JSON of last analysis results
    agent_version: str = Field(default="1.0")  # Agent version for compatibility
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationship
    user: User = Relationship(back_populates="agent_contexts")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Helper method to parse conversation history JSON"""
        try:
            return json.loads(self.conversation_history)
        except:
            return []
    
    def set_conversation_history(self, history: List[Dict[str, Any]]):
        """Helper method to set conversation history as JSON"""
        self.conversation_history = json.dumps(history)
    
    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Helper method to parse last analysis JSON"""
        try:
            return json.loads(self.last_analysis) if self.last_analysis else None
        except:
            return None
    
    def set_last_analysis(self, analysis: Dict[str, Any]):
        """Helper method to set last analysis as JSON"""
        self.last_analysis = json.dumps(analysis)

class MarketCache(SQLModel, table=True):
    """
    High-performance market data caching system
    
    This model caches various types of market data:
    - Price data (current, historical)
    - Volume information
    - Technical indicators
    - Fundamental data
    
    Key features:
    - Type-based data organization
    - Automatic expiration management
    - JSON storage for flexible data structures
    - Symbol-based indexing for fast retrieval
    """
    __tablename__ = "market_cache"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    instrument_id: str = Field(foreign_key="instruments.id", index=True)
    data_type: DataType  # price/volume/technical/fundamentals
    data_json: str  # JSON string containing the cached data
    expires_at: datetime = Field(index=True)  # Cache expiration time
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationship
    instrument: Instrument = Relationship(back_populates="market_cache")
    
    def get_data(self) -> Dict[str, Any]:
        """Helper method to parse cached data JSON"""
        try:
            return json.loads(self.data_json)
        except:
            return {}
    
    def set_data(self, data: Dict[str, Any]):
        """Helper method to set data as JSON"""
        self.data_json = json.dumps(data)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now(timezone.utc) > self.expires_at

class Alert(SQLModel, table=True):
    """
    User alert system for real-time notifications
    
    This model manages alerts for users based on:
    - Price movements
    - News events
    - Earnings announcements
    - Volume spikes
    
    Key features:
    - Type-based alert categorization
    - Acknowledgment tracking
    - Symbol-specific alerts
    - Message templating for notifications
    """
    __tablename__ = "alerts"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    symbol: str = Field(index=True)  # Symbol this alert is for
    alert_type: AlertType  # price/news/earnings/volume
    message: str  # Alert message to display
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False  # Whether user has seen this alert
    acknowledged_at: Optional[datetime] = None
    
    # Alert configuration (JSON for flexibility)
    alert_config: str = Field(default="{}")  # JSON config for alert conditions
    
    # Relationship
    user: User = Relationship(back_populates="alerts")
    
    def get_alert_config(self) -> Dict[str, Any]:
        """Helper method to parse alert config JSON"""
        try:
            return json.loads(self.alert_config)
        except:
            return {}
    
    def set_alert_config(self, config: Dict[str, Any]):
        """Helper method to set alert config as JSON"""
        self.alert_config = json.dumps(config)
    
    def acknowledge(self):
        """Mark alert as acknowledged"""
        self.acknowledged = True
        self.acknowledged_at = datetime.now(timezone.utc)


# ================================================================================
# DATABASE INITIALIZATION AND MIGRATION HELPERS
# ================================================================================

def create_all_tables(engine):
    """
    Create all Phase 1 database tables
    
    This function should be called during application initialization
    to create all required tables for Phase 1 functionality.
    """
    SQLModel.metadata.create_all(engine)

def get_phase1_models():
    """
    Return list of all Phase 1 models for migration purposes
    """
    return [
        User,
        UserSession, 
        Instrument,
        UserFollowing,
        NewsArticle,
        NewsCache,
        EarningReport,
        AgentContext,
        MarketCache,
        Alert
    ]

# ================================================================================
# SAMPLE DATA AND TESTING UTILITIES
# ================================================================================

def create_sample_instruments():
    """
    Create sample instruments for testing and development
    """
    sample_instruments = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "type": InstrumentType.STOCK,
            "sector": "Technology",
            "exchange": "NASDAQ"
        },
        {
            "symbol": "SPY", 
            "name": "SPDR S&P 500 ETF Trust",
            "type": InstrumentType.ETF,
            "sector": "Diversified",
            "exchange": "NYSE"
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "type": InstrumentType.STOCK,
            "sector": "Technology",
            "exchange": "NASDAQ"
        }
    ]
    return [Instrument(**data) for data in sample_instruments]