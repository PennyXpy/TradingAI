# TradingAI Core Database Models
# This module exports all core database models for the TradingAI application

# Import all core models
from .core_models import (
    # Enums
    InstrumentType,
    AlertType, 
    DataType,
    
    # User & Authentication
    User,
    UserSession,
    
    # Financial Instruments
    Instrument,
    UserFollowing,
    
    # News & Information
    NewsArticle,
    NewsCache,
    EarningReport,
    
    # Agent & Caching
    AgentContext,
    MarketCache,
    Alert,
    
    # Utility functions
    create_all_tables,
    get_phase1_models,
    create_sample_instruments
)

# Import AI-specific models
from .ai_models import (
    ChatSession,
    AgentRecommendation,
    TradingInsight,
    PerformanceMetric,
    AgentLearningData
)

# Note: Database initialization utilities removed (phase1_init.py)
# Database will be initialized at runtime via data.py

# Export all models for backward compatibility and easy imports
__all__ = [
    # Enums
    "InstrumentType",
    "AlertType",
    "DataType",
    
    # Models
    "User",
    "UserSession", 
    "Instrument",
    "UserFollowing",
    "NewsArticle",
    "NewsCache",
    "EarningReport",
    "AgentContext",
    "MarketCache",
    "Alert",
    
    # Utilities
    "create_all_tables",
    "get_phase1_models", 
    "create_sample_instruments",
    
    # AI Models
    "ChatSession",
    "AgentRecommendation", 
    "TradingInsight",
    "PerformanceMetric",
    "AgentLearningData"
]

# Backward compatibility aliases for existing code
UserToken = UserSession  # Old UserToken maps to new UserSession
Followed = UserFollowing  # Old Followed maps to new UserFollowing
FollowedAsset = UserFollowing  # Old FollowedAsset maps to new UserFollowing