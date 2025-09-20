# TradingAI AI-Specific Database Models
# This module contains database models specifically designed for AI agent functionality
# These models complement the core models and provide comprehensive storage for:
# - Agent recommendations and trading insights
# - Chat session management and conversation tracking
# - Performance analytics and backtesting data
# - Advanced caching strategies for agent outputs

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import json

# ================================================================================
# ENUMS FOR AI AGENT FUNCTIONALITY
# ================================================================================

class RecommendationType(str, Enum):
    """
    Defines types of trading recommendations the AI agent can make
    - BUY: Recommend purchasing the asset
    - SELL: Recommend selling existing position
    - HOLD: Recommend maintaining current position
    - WATCH: Recommend monitoring without action
    - AVOID: Recommend avoiding the asset
    """
    BUY = "BUY"
    SELL = "SELL" 
    HOLD = "HOLD"
    WATCH = "WATCH"
    AVOID = "AVOID"

class RiskLevel(str, Enum):
    """
    Risk assessment levels for recommendations and insights
    - LOW: Conservative, stable investments
    - MEDIUM: Balanced risk-reward profile
    - HIGH: Aggressive, high volatility investments
    - EXTREME: Speculative, very high risk
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

class InsightType(str, Enum):
    """
    Categories of trading insights the AI can generate
    - PATTERN: Technical pattern recognition (head & shoulders, triangles, etc.)
    - CORRELATION: Cross-asset correlation analysis
    - ANOMALY: Unusual market behavior detection
    - SENTIMENT: News sentiment analysis impact
    - VOLUME: Volume spike or unusual trading activity
    - SEASONAL: Seasonal trading patterns
    """
    PATTERN = "PATTERN"
    CORRELATION = "CORRELATION"
    ANOMALY = "ANOMALY"
    SENTIMENT = "SENTIMENT"
    VOLUME = "VOLUME"
    SEASONAL = "SEASONAL"

class AnalysisTimeframe(str, Enum):
    """
    Timeframes for analysis and recommendations
    - INTRADAY: Same day trading signals
    - SHORT_TERM: 1-7 days outlook
    - MEDIUM_TERM: 1-4 weeks outlook
    - LONG_TERM: 1+ months outlook
    """
    INTRADAY = "INTRADAY"
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    LONG_TERM = "LONG_TERM"

# ================================================================================
# AI AGENT RECOMMENDATION SYSTEM
# ================================================================================

class AgentRecommendation(SQLModel, table=True):
    """
    Long-term storage for AI trading recommendations with comprehensive tracking
    
    This model stores AI-generated trading recommendations with:
    - Full reasoning and confidence scoring
    - Target prices and risk assessment
    - Expiration tracking for time-sensitive recommendations
    - Backtesting data for performance analysis
    
    Key features:
    - Links to user and tracks recommendation performance over time
    - Stores complete analysis data for later review and learning
    - Supports different timeframes (intraday to long-term)
    - Enables recommendation accuracy tracking and model improvement
    
    Use cases:
    - Store AI trading recommendations for user review
    - Track recommendation performance for backtesting
    - Analyze AI model accuracy over time
    - Provide historical context for future recommendations
    """
    __tablename__ = "agent_recommendations"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    symbol: str = Field(index=True)
    
    # Core recommendation data
    recommendation_type: RecommendationType
    confidence_score: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0 confidence level
    reasoning: str  # Human-readable explanation from AI
    
    # Price and target information
    price_at_recommendation: float  # Asset price when recommendation was made
    target_price: Optional[float] = None  # AI's target price prediction
    stop_loss_price: Optional[float] = None  # Suggested stop-loss level
    
    # Risk and timing
    risk_level: RiskLevel
    timeframe: AnalysisTimeframe
    expires_at: Optional[datetime] = None  # When recommendation becomes invalid
    
    # Detailed analysis data (JSON storage for flexibility)
    technical_analysis: str = Field(default="{}")  # Technical indicators, charts, patterns
    fundamental_analysis: str = Field(default="{}")  # Earnings, ratios, company analysis
    sentiment_analysis: str = Field(default="{}")  # News sentiment, social sentiment
    market_context: str = Field(default="{}")  # Overall market conditions
    
    # Performance tracking (updated after recommendation period)
    actual_performance: Optional[float] = None  # Actual price change %
    recommendation_accuracy: Optional[bool] = None  # Was the recommendation correct?
    user_action_taken: Optional[str] = None  # What action user actually took
    
    # Metadata
    agent_version: str = Field(default="1.0")  # AI agent version for tracking improvements
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Helper methods for JSON data handling
    def get_technical_analysis(self) -> Dict[str, Any]:
        """Parse technical analysis JSON data"""
        try:
            return json.loads(self.technical_analysis)
        except:
            return {}
    
    def set_technical_analysis(self, data: Dict[str, Any]):
        """Store technical analysis as JSON"""
        self.technical_analysis = json.dumps(data)
        
    def get_fundamental_analysis(self) -> Dict[str, Any]:
        """Parse fundamental analysis JSON data"""
        try:
            return json.loads(self.fundamental_analysis)
        except:
            return {}
    
    def set_fundamental_analysis(self, data: Dict[str, Any]):
        """Store fundamental analysis as JSON"""
        self.fundamental_analysis = json.dumps(data)
        
    def get_sentiment_analysis(self) -> Dict[str, Any]:
        """Parse sentiment analysis JSON data"""
        try:
            return json.loads(self.sentiment_analysis)
        except:
            return {}
    
    def set_sentiment_analysis(self, data: Dict[str, Any]):
        """Store sentiment analysis as JSON"""
        self.sentiment_analysis = json.dumps(data)
        
    def get_market_context(self) -> Dict[str, Any]:
        """Parse market context JSON data"""
        try:
            return json.loads(self.market_context)
        except:
            return {}
    
    def set_market_context(self, data: Dict[str, Any]):
        """Store market context as JSON"""
        self.market_context = json.dumps(data)
    
    def is_expired(self) -> bool:
        """Check if recommendation has expired"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def calculate_performance(self, current_price: float) -> float:
        """Calculate current performance vs recommendation price"""
        return ((current_price - self.price_at_recommendation) / self.price_at_recommendation) * 100

# ================================================================================
# TRADING INSIGHTS AND PATTERN RECOGNITION
# ================================================================================

class TradingInsight(SQLModel, table=True):
    """
    AI-generated trading insights and pattern recognition storage
    
    This model stores various types of market insights generated by the AI:
    - Technical pattern recognition
    - Cross-asset correlations
    - Market anomaly detection
    - Sentiment-driven insights
    
    Key features:
    - Tracks insight accuracy over time for AI improvement
    - Supports multiple asset correlation analysis
    - Stores confidence levels and historical performance
    - Enables insight categorization and filtering
    
    Use cases:
    - Store pattern recognition results
    - Track correlation analysis between assets
    - Alert users to market anomalies
    - Provide educational content about market patterns
    """
    __tablename__ = "trading_insights"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Core insight data
    insight_type: InsightType
    title: str = Field(max_length=200)  # Short, descriptive title
    description: str  # Detailed explanation of the insight
    
    # Asset information
    primary_symbol: str = Field(index=True)  # Main asset the insight is about
    symbols_involved: str = Field(default="[]")  # JSON array of all related symbols
    
    # Confidence and accuracy tracking
    confidence_level: float = Field(ge=0.0, le=1.0)  # AI confidence in this insight
    historical_accuracy: Optional[float] = None  # Historical accuracy for this insight type
    
    # Time relevance
    timeframe: AnalysisTimeframe
    valid_until: Optional[datetime] = None  # When insight becomes obsolete
    
    # Supporting data
    supporting_data: str = Field(default="{}")  # JSON data supporting the insight
    chart_data: Optional[str] = None  # Chart data for visualization
    
    # Performance tracking
    insight_outcome: Optional[str] = None  # What actually happened
    was_accurate: Optional[bool] = None  # Was the insight correct?
    user_acted_on_insight: bool = False  # Did user take action based on this insight?
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Helper methods
    def get_symbols_involved(self) -> List[str]:
        """Parse symbols JSON array"""
        try:
            return json.loads(self.symbols_involved)
        except:
            return []
    
    def set_symbols_involved(self, symbols: List[str]):
        """Store symbols as JSON array"""
        self.symbols_involved = json.dumps(symbols)
        
    def get_supporting_data(self) -> Dict[str, Any]:
        """Parse supporting data JSON"""
        try:
            return json.loads(self.supporting_data)
        except:
            return {}
    
    def set_supporting_data(self, data: Dict[str, Any]):
        """Store supporting data as JSON"""
        self.supporting_data = json.dumps(data)
    
    def is_valid(self) -> bool:
        """Check if insight is still valid"""
        if self.valid_until is None:
            return True
        return datetime.now(timezone.utc) < self.valid_until

# ================================================================================
# ENHANCED CHAT SESSION MANAGEMENT
# ================================================================================

class ChatSession(SQLModel, table=True):
    """
    Enhanced chat session management for organized conversation tracking
    
    This model provides better organization of chat conversations:
    - Groups related messages into sessions
    - Auto-generates session titles based on content
    - Tracks session metrics and context
    - Enables session-based context management
    
    Key features:
    - Automatic session title generation
    - Message count and timing tracking
    - Context summary for session continuity
    - User-defined session organization
    
    Use cases:
    - Organize conversations by topic or date
    - Provide session-based context to AI
    - Enable session search and retrieval
    - Track user engagement patterns
    """
    __tablename__ = "chat_sessions"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Session metadata
    title: str = Field(max_length=200)  # Auto-generated or user-defined session title
    description: Optional[str] = None  # Optional user description
    
    # Timing information
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None  # When session was explicitly ended
    
    # Session metrics
    message_count: int = 0
    user_message_count: int = 0
    agent_message_count: int = 0
    
    # Context and summary
    context_summary: Optional[str] = None  # AI-generated session summary
    primary_topics: str = Field(default="[]")  # JSON array of main discussion topics
    symbols_discussed: str = Field(default="[]")  # JSON array of symbols mentioned
    
    # Session settings
    is_active: bool = True  # Whether session is currently active
    is_pinned: bool = False  # User can pin important sessions
    
    # Helper methods
    def get_primary_topics(self) -> List[str]:
        """Parse primary topics JSON array"""
        try:
            return json.loads(self.primary_topics)
        except:
            return []
    
    def set_primary_topics(self, topics: List[str]):
        """Store primary topics as JSON array"""
        self.primary_topics = json.dumps(topics)
    
    def get_symbols_discussed(self) -> List[str]:
        """Parse symbols discussed JSON array"""
        try:
            return json.loads(self.symbols_discussed)
        except:
            return []
    
    def set_symbols_discussed(self, symbols: List[str]):
        """Store symbols discussed as JSON array"""
        self.symbols_discussed = json.dumps(symbols)
    
    def end_session(self):
        """Mark session as ended"""
        self.is_active = False
        self.ended_at = datetime.now(timezone.utc)
    
    def add_message(self, is_from_user: bool = True):
        """Increment message counters"""
        self.message_count += 1
        if is_from_user:
            self.user_message_count += 1
        else:
            self.agent_message_count += 1
        self.last_message_at = datetime.now(timezone.utc)

# ================================================================================
# PERFORMANCE ANALYTICS AND BACKTESTING
# ================================================================================

class PerformanceMetric(SQLModel, table=True):
    """
    AI agent performance tracking and analytics storage
    
    This model tracks the performance of AI recommendations and insights:
    - Recommendation accuracy over time
    - User engagement with AI suggestions
    - Portfolio performance attribution
    - AI model improvement metrics
    
    Key features:
    - Time-series performance tracking
    - Accuracy measurement by recommendation type
    - User behavior analysis
    - A/B testing support for AI improvements
    
    Use cases:
    - Track AI recommendation accuracy
    - Measure user engagement with AI features
    - Analyze portfolio performance attribution
    - Support AI model improvement efforts
    """
    __tablename__ = "performance_metrics"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Metric identification
    metric_type: str = Field(index=True)  # "recommendation_accuracy", "user_engagement", etc.
    metric_category: str  # "AI_PERFORMANCE", "USER_BEHAVIOR", "PORTFOLIO"
    
    # Time period
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
    calculation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Metric values
    metric_value: float  # Main metric value
    baseline_value: Optional[float] = None  # Comparison baseline
    target_value: Optional[float] = None  # Target or goal value
    
    # Additional context
    sample_size: Optional[int] = None  # Number of data points used
    confidence_interval: Optional[float] = None  # Statistical confidence
    metric_metadata: str = Field(default="{}")  # Additional metric context as JSON
    
    # Helper methods
    def get_metadata(self) -> Dict[str, Any]:
        """Parse metadata JSON"""
        try:
            return json.loads(self.metric_metadata)
        except:
            return {}
    
    def set_metadata(self, data: Dict[str, Any]):
        """Store metadata as JSON"""
        self.metric_metadata = json.dumps(data)
    
    def performance_vs_baseline(self) -> Optional[float]:
        """Calculate performance relative to baseline"""
        if self.baseline_value is None or self.baseline_value == 0:
            return None
        return ((self.metric_value - self.baseline_value) / self.baseline_value) * 100
    
    def progress_to_target(self) -> Optional[float]:
        """Calculate progress toward target as percentage"""
        if self.target_value is None or self.baseline_value is None:
            return None
        if self.target_value == self.baseline_value:
            return 100.0  # Already at target
        return ((self.metric_value - self.baseline_value) / (self.target_value - self.baseline_value)) * 100

# ================================================================================
# AGENT LEARNING AND IMPROVEMENT
# ================================================================================

class AgentLearningData(SQLModel, table=True):
    """
    Storage for AI agent learning and model improvement data
    
    This model collects data for improving the AI agent over time:
    - User feedback on recommendations
    - Successful/failed prediction patterns
    - Market condition correlations
    - Feature importance tracking
    
    Key features:
    - Stores user feedback for supervised learning
    - Tracks prediction accuracy by market conditions
    - Enables feature importance analysis
    - Supports model versioning and A/B testing
    
    Use cases:
    - Collect user feedback for model improvement
    - Analyze prediction patterns and failures
    - Track feature importance over time
    - Support continuous learning and adaptation
    """
    __tablename__ = "agent_learning_data"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Learning context
    learning_type: str = Field(index=True)  # "user_feedback", "prediction_outcome", "feature_importance"
    agent_version: str = Field(default="1.0")  # Version of AI that generated this data
    
    # Input/output data
    input_data: str  # JSON of input features/context
    prediction_data: str  # JSON of AI prediction/recommendation
    actual_outcome: Optional[str] = None  # JSON of what actually happened
    
    # User feedback
    user_rating: Optional[int] = None  # User rating (1-5) of AI recommendation
    user_feedback_text: Optional[str] = None  # User's written feedback
    user_action_taken: Optional[str] = None  # What action user took
    
    # Market context
    market_conditions: str = Field(default="{}")  # JSON of market conditions when prediction made
    symbol_context: Optional[str] = None  # Symbol this learning data is about
    
    # Outcome analysis
    prediction_accuracy: Optional[float] = None  # How accurate was the prediction (0-1)
    outcome_measured_at: Optional[datetime] = None  # When outcome was measured
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Helper methods
    def get_input_data(self) -> Dict[str, Any]:
        """Parse input data JSON"""
        try:
            return json.loads(self.input_data)
        except:
            return {}
    
    def set_input_data(self, data: Dict[str, Any]):
        """Store input data as JSON"""
        self.input_data = json.dumps(data)
    
    def get_prediction_data(self) -> Dict[str, Any]:
        """Parse prediction data JSON"""
        try:
            return json.loads(self.prediction_data)
        except:
            return {}
    
    def set_prediction_data(self, data: Dict[str, Any]):
        """Store prediction data as JSON"""
        self.prediction_data = json.dumps(data)
    
    def get_actual_outcome(self) -> Optional[Dict[str, Any]]:
        """Parse actual outcome JSON"""
        if self.actual_outcome is None:
            return None
        try:
            return json.loads(self.actual_outcome)
        except:
            return None
    
    def set_actual_outcome(self, data: Dict[str, Any]):
        """Store actual outcome as JSON"""
        self.actual_outcome = json.dumps(data)
    
    def get_market_conditions(self) -> Dict[str, Any]:
        """Parse market conditions JSON"""
        try:
            return json.loads(self.market_conditions)
        except:
            return {}
    
    def set_market_conditions(self, data: Dict[str, Any]):
        """Store market conditions as JSON"""
        self.market_conditions = json.dumps(data)

# ================================================================================
# DATABASE UTILITIES AND MIGRATION HELPERS
# ================================================================================

def get_ai_agent_models():
    """
    Return list of all AI agent models for migration purposes
    """
    return [
        AgentRecommendation,
        TradingInsight,
        ChatSession,
        PerformanceMetric,
        AgentLearningData
    ]

def create_ai_agent_tables(engine):
    """
    Create all AI agent database tables
    
    This function should be called during application initialization
    to create all required tables for AI agent functionality.
    """
    # Import the base models to ensure they exist first
    from .phase1_models import SQLModel
    
    # Create only the AI agent tables
    for model in get_ai_agent_models():
        model.__table__.create(engine, checkfirst=True)

# ================================================================================
# SAMPLE DATA FOR TESTING
# ================================================================================

def create_sample_recommendations(user_id: str):
    """
    Create sample AI recommendations for testing and development
    """
    sample_recommendations = [
        {
            "user_id": user_id,
            "symbol": "AAPL",
            "recommendation_type": RecommendationType.BUY,
            "confidence_score": 0.85,
            "reasoning": "Strong technical breakout above resistance with positive earnings momentum",
            "price_at_recommendation": 175.50,
            "target_price": 195.00,
            "risk_level": RiskLevel.MEDIUM,
            "timeframe": AnalysisTimeframe.SHORT_TERM
        },
        {
            "user_id": user_id,
            "symbol": "TSLA",
            "recommendation_type": RecommendationType.HOLD,
            "confidence_score": 0.65,
            "reasoning": "Mixed signals - strong fundamentals but overvalued on technical analysis",
            "price_at_recommendation": 210.25,
            "target_price": 220.00,
            "risk_level": RiskLevel.HIGH,
            "timeframe": AnalysisTimeframe.MEDIUM_TERM
        }
    ]
    return [AgentRecommendation(**data) for data in sample_recommendations]

def create_sample_insights(user_id: str):
    """
    Create sample trading insights for testing and development
    """
    sample_insights = [
        {
            "user_id": user_id,
            "insight_type": InsightType.PATTERN,
            "title": "Head and Shoulders Pattern Forming",
            "description": "AAPL is forming a potential head and shoulders reversal pattern",
            "primary_symbol": "AAPL",
            "confidence_level": 0.75,
            "timeframe": AnalysisTimeframe.SHORT_TERM
        },
        {
            "user_id": user_id,
            "insight_type": InsightType.CORRELATION,
            "title": "Tech Sector Correlation",
            "description": "Strong positive correlation between AAPL and MSFT movements",
            "primary_symbol": "AAPL",
            "confidence_level": 0.90,
            "timeframe": AnalysisTimeframe.MEDIUM_TERM
        }
    ]
    return [TradingInsight(**data) for data in sample_insights]