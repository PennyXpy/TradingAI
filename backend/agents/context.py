# User Context and Dependency Injection for Pydantic AI Agent
# This module provides user context and dependency injection for the trading agent
# It manages user-specific data, preferences, and state for personalized AI interactions
# 
# Key features:
# - User authentication and session management
# - Portfolio and watchlist context
# - User preferences and risk tolerance
# - Trading history and performance context
# - Market data and news context for the user
# - Clean dependency injection for all agent tools

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from sqlmodel import Session, select
import json

# Import models and tools
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.core_models import User, UserFollowing, Instrument, AgentContext
from models.ai_models import ChatSession
from agents.tools import (
    MarketDataTool, NewsAnalysisTool, PortfolioTool, 
    AlertTool, AnalysisTool, RecommendationTool
)

# ================================================================================
# PYDANTIC MODELS FOR CONTEXT
# ================================================================================

class UserProfile(BaseModel):
    """User profile information for personalized recommendations"""
    user_id: str
    username: str
    email: str
    risk_tolerance: str = "medium"  # "low", "medium", "high"
    investment_experience: str = "intermediate"  # "beginner", "intermediate", "advanced"
    investment_goals: List[str] = []  # ["growth", "income", "preservation", "speculation"]
    time_horizon: str = "medium_term"  # "short_term", "medium_term", "long_term"
    preferred_asset_types: List[str] = ["stocks"]  # ["stocks", "etfs", "crypto", "bonds"]
    max_position_size: float = 10.0  # Maximum percentage per position
    notifications_enabled: bool = True

class PortfolioContext(BaseModel):
    """Current portfolio context for the user"""
    total_value: float
    total_cost: float
    total_return: float
    total_return_percent: float
    day_change: float
    day_change_percent: float
    position_count: int
    followed_asset_count: int
    top_holdings: List[Dict[str, Any]]
    asset_allocation: Dict[str, float]  # {"stocks": 0.8, "etfs": 0.2}
    sector_allocation: Dict[str, float]
    last_updated: datetime

class MarketContext(BaseModel):
    """Current market context and conditions"""
    market_open: bool
    market_state: str  # "PRE", "REGULAR", "POST", "CLOSED"
    major_indices: Dict[str, Dict[str, float]]  # {"SPY": {"price": 450.0, "change": 1.5}}
    market_sentiment: str = "neutral"  # "bullish", "bearish", "neutral"
    vix_level: Optional[float] = None
    recent_news_sentiment: Optional[float] = None
    last_updated: datetime

class ConversationContext(BaseModel):
    """Recent conversation context for continuity"""
    session_id: Optional[str] = None
    recent_topics: List[str] = []
    recent_symbols_discussed: List[str] = []
    last_analysis_performed: Optional[Dict[str, Any]] = None
    last_recommendations: List[Dict[str, Any]] = []
    conversation_summary: Optional[str] = None

# ================================================================================
# AGENT CONTEXT CLASS
# ================================================================================

class AgentContextManager:
    """
    Manages user context and dependencies for the Pydantic AI agent
    
    This class provides comprehensive context management for personalized AI interactions:
    - User profile and preferences management
    - Portfolio and market data context
    - Conversation history and continuity
    - Tool dependency injection
    - Context persistence and caching
    
    The context manager ensures that the AI agent has access to all relevant
    user-specific information needed to provide personalized recommendations
    and maintain conversation continuity across sessions.
    """
    
    def __init__(self, db_session: Session, user_id: str):
        """
        Initialize agent context manager for a specific user
        
        Args:
            db_session: SQLModel database session
            user_id: ID of the user for context
        """
        self.db_session = db_session
        self.user_id = user_id
        self.user_profile: Optional[UserProfile] = None
        self.portfolio_context: Optional[PortfolioContext] = None
        self.market_context: Optional[MarketContext] = None
        self.conversation_context: Optional[ConversationContext] = None
        
        # Initialize tools with database session
        self.market_data_tool = MarketDataTool(db_session)
        self.news_analysis_tool = NewsAnalysisTool(db_session)
        self.portfolio_tool = PortfolioTool(db_session)
        self.alert_tool = AlertTool(db_session)
        self.analysis_tool = AnalysisTool(db_session)
        self.recommendation_tool = RecommendationTool(db_session)
        
        # Load initial context
        self._load_user_context()
    
    def get_user_profile(self) -> UserProfile:
        """
        Get user profile with preferences and settings
        
        Returns:
            UserProfile object with user information and preferences
        """
        if self.user_profile is None:
            self._load_user_profile()
        
        return self.user_profile or UserProfile(
            user_id=self.user_id,
            username="Unknown",
            email=""
        )
    
    def get_portfolio_context(self) -> PortfolioContext:
        """
        Get current portfolio context and summary
        
        Returns:
            PortfolioContext object with portfolio information
        """
        if self.portfolio_context is None:
            self._load_portfolio_context()
        
        return self.portfolio_context or PortfolioContext(
            total_value=0.0,
            total_cost=0.0,
            total_return=0.0,
            total_return_percent=0.0,
            day_change=0.0,
            day_change_percent=0.0,
            position_count=0,
            followed_asset_count=0,
            top_holdings=[],
            asset_allocation={},
            sector_allocation={},
            last_updated=datetime.now()
        )
    
    def get_market_context(self) -> MarketContext:
        """
        Get current market context and conditions
        
        Returns:
            MarketContext object with market information
        """
        if self.market_context is None:
            self._load_market_context()
        
        return self.market_context or MarketContext(
            market_open=False,
            market_state="CLOSED",
            major_indices={},
            last_updated=datetime.now()
        )
    
    def get_conversation_context(self, session_id: Optional[str] = None) -> ConversationContext:
        """
        Get conversation context for continuity
        
        Args:
            session_id: Optional specific session ID to load
            
        Returns:
            ConversationContext object with conversation history
        """
        if self.conversation_context is None or session_id:
            self._load_conversation_context(session_id)
        
        return self.conversation_context or ConversationContext()
    
    def update_conversation_context(self, 
                                   topics: List[str] = None,
                                   symbols: List[str] = None,
                                   analysis: Dict[str, Any] = None,
                                   recommendations: List[Dict[str, Any]] = None):
        """
        Update conversation context with new information
        
        Args:
            topics: New topics discussed
            symbols: New symbols mentioned
            analysis: Latest analysis performed
            recommendations: Latest recommendations given
        """
        if self.conversation_context is None:
            self.conversation_context = ConversationContext()
        
        # Update topics (keep last 10)
        if topics:
            self.conversation_context.recent_topics.extend(topics)
            self.conversation_context.recent_topics = self.conversation_context.recent_topics[-10:]
        
        # Update symbols (keep last 20)
        if symbols:
            self.conversation_context.recent_symbols_discussed.extend(symbols)
            # Remove duplicates while preserving order
            seen = set()
            unique_symbols = []
            for symbol in self.conversation_context.recent_symbols_discussed:
                if symbol not in seen:
                    seen.add(symbol)
                    unique_symbols.append(symbol)
            self.conversation_context.recent_symbols_discussed = unique_symbols[-20:]
        
        # Update analysis and recommendations
        if analysis:
            self.conversation_context.last_analysis_performed = analysis
        
        if recommendations:
            self.conversation_context.last_recommendations = recommendations[-5:]  # Keep last 5
    
    def get_user_followed_symbols(self) -> List[str]:
        """
        Get list of symbols the user is following
        
        Returns:
            List of stock symbols user is following
        """
        try:
            statement = select(UserFollowing, Instrument).join(Instrument).where(
                UserFollowing.user_id == self.user_id
            )
            results = self.db_session.exec(statement).all()
            
            return [instrument.symbol for _, instrument in results]
            
        except Exception as e:
            print(f"Error getting followed symbols: {str(e)}")
            return []
    
    def get_user_portfolio_symbols(self) -> List[str]:
        """
        Get list of symbols in user's portfolio
        
        Returns:
            List of stock symbols user owns
        """
        try:
            statement = select(Investment.symbol).where(Investment.user_id == self.user_id).distinct()
            results = self.db_session.exec(statement).all()
            
            return [symbol for symbol, in results]
            
        except Exception as e:
            print(f"Error getting portfolio symbols: {str(e)}")
            return []
    
    def save_conversation_state(self, session_id: str, conversation_summary: str):
        """
        Save current conversation state to database
        
        Args:
            session_id: Chat session ID
            conversation_summary: Summary of the conversation
        """
        try:
            # Update or create agent context
            statement = select(AgentContext).where(AgentContext.user_id == self.user_id)
            agent_context = self.db_session.exec(statement).first()
            
            if not agent_context:
                agent_context = AgentContext(user_id=self.user_id)
                self.db_session.add(agent_context)
            
            # Update conversation context
            if self.conversation_context:
                context_data = {
                    "session_id": session_id,
                    "recent_topics": self.conversation_context.recent_topics,
                    "recent_symbols": self.conversation_context.recent_symbols_discussed,
                    "last_analysis": self.conversation_context.last_analysis_performed,
                    "last_recommendations": self.conversation_context.last_recommendations,
                    "summary": conversation_summary
                }
                agent_context.set_conversation_history([context_data])
            
            agent_context.updated_at = datetime.now()
            self.db_session.commit()
            
        except Exception as e:
            print(f"Error saving conversation state: {str(e)}")
            self.db_session.rollback()
    
    def create_tools_context(self) -> Dict[str, Any]:
        """
        Create context dictionary for tool access within agent
        
        Returns:
            Dictionary containing all tools and context data
        """
        return {
            "market_data_tool": self.market_data_tool,
            "news_analysis_tool": self.news_analysis_tool,
            "portfolio_tool": self.portfolio_tool,
            "alert_tool": self.alert_tool,
            "analysis_tool": self.analysis_tool,
            "recommendation_tool": self.recommendation_tool,
            "user_profile": self.get_user_profile(),
            "portfolio_context": self.get_portfolio_context(),
            "market_context": self.get_market_context(),
            "conversation_context": self.get_conversation_context(),
            "db_session": self.db_session
        }
    
    # ================================================================================
    # PRIVATE HELPER METHODS
    # ================================================================================
    
    def _load_user_context(self):
        """Load all user context data"""
        self._load_user_profile()
        self._load_portfolio_context()
        self._load_market_context()
        self._load_conversation_context()
    
    def _load_user_profile(self):
        """Load user profile from database"""
        try:
            statement = select(User).where(User.id == self.user_id)
            user = self.db_session.exec(statement).first()
            
            if user:
                # Parse user preferences
                preferences = user.get_preferences()
                
                self.user_profile = UserProfile(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    risk_tolerance=preferences.get("risk_tolerance", "medium"),
                    investment_experience=preferences.get("investment_experience", "intermediate"),
                    investment_goals=preferences.get("investment_goals", []),
                    time_horizon=preferences.get("time_horizon", "medium_term"),
                    preferred_asset_types=preferences.get("preferred_asset_types", ["stocks"]),
                    max_position_size=preferences.get("max_position_size", 10.0),
                    notifications_enabled=preferences.get("notifications_enabled", True)
                )
            
        except Exception as e:
            print(f"Error loading user profile: {str(e)}")
    
    def _load_portfolio_context(self):
        """Load portfolio context using portfolio tool"""
        try:
            portfolio_summary = self.portfolio_tool.get_portfolio_summary(self.user_id)
            followed_assets = self.portfolio_tool.get_followed_assets(self.user_id)
            
            self.portfolio_context = PortfolioContext(
                total_value=portfolio_summary.total_market_value,
                total_cost=portfolio_summary.total_cost_basis,
                total_return=portfolio_summary.total_unrealized_gain_loss,
                total_return_percent=portfolio_summary.total_unrealized_gain_loss_percent,
                day_change=portfolio_summary.day_change,
                day_change_percent=portfolio_summary.day_change_percent,
                position_count=portfolio_summary.asset_count,
                followed_asset_count=len(followed_assets),
                top_holdings=portfolio_summary.top_holdings,
                asset_allocation=portfolio_summary.asset_type_breakdown,
                sector_allocation=portfolio_summary.sector_diversification,
                last_updated=portfolio_summary.last_updated
            )
            
        except Exception as e:
            print(f"Error loading portfolio context: {str(e)}")
    
    def _load_market_context(self):
        """Load market context using market data tool"""
        try:
            market_status = self.market_data_tool.get_market_status()
            
            # Get major indices (simplified)
            major_indices = {}
            for symbol in ["SPY", "QQQ", "DIA"]:
                price_data = self.market_data_tool.get_real_time_price(symbol, "etf")
                if price_data:
                    major_indices[symbol] = {
                        "price": price_data.current_price,
                        "change": price_data.change,
                        "change_percent": price_data.change_percent
                    }
            
            self.market_context = MarketContext(
                market_open=market_status.is_market_open,
                market_state=market_status.market_state,
                major_indices=major_indices,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            print(f"Error loading market context: {str(e)}")
    
    def _load_conversation_context(self, session_id: Optional[str] = None):
        """Load conversation context from database"""
        try:
            statement = select(AgentContext).where(AgentContext.user_id == self.user_id)
            agent_context = self.db_session.exec(statement).first()
            
            if agent_context:
                conversation_history = agent_context.get_conversation_history()
                if conversation_history:
                    latest_context = conversation_history[-1]
                    
                    self.conversation_context = ConversationContext(
                        session_id=latest_context.get("session_id"),
                        recent_topics=latest_context.get("recent_topics", []),
                        recent_symbols_discussed=latest_context.get("recent_symbols", []),
                        last_analysis_performed=latest_context.get("last_analysis"),
                        last_recommendations=latest_context.get("last_recommendations", []),
                        conversation_summary=latest_context.get("summary")
                    )
            
        except Exception as e:
            print(f"Error loading conversation context: {str(e)}")

# ================================================================================
# HELPER FUNCTIONS
# ================================================================================

def create_agent_context(db_session: Session, user_id: str) -> AgentContextManager:
    """
    Factory function to create an AgentContextManager instance
    
    Args:
        db_session: Database session
        user_id: User ID for context
        
    Returns:
        Configured AgentContextManager instance
    """
    return AgentContextManager(db_session, user_id)

def extract_user_id_from_token(token: str, db_session: Session) -> Optional[str]:
    """
    Extract user ID from authentication token
    
    Args:
        token: JWT or session token
        db_session: Database session
        
    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        # This is a simplified implementation
        # In production, you would validate the JWT token properly
        
        # For now, assume token format is "user_id:timestamp" or similar
        # This should be replaced with proper JWT validation
        
        if token == "mock-token":
            # Mock token for development
            statement = select(User).limit(1)
            user = db_session.exec(statement).first()
            return user.id if user else None
        
        # Add proper JWT token validation here
        return None
        
    except Exception as e:
        print(f"Error extracting user ID from token: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    from sqlmodel import create_engine, Session
    
    # Create test database session
    engine = create_engine("sqlite:///test.db")
    session = Session(engine)
    
    # Create context manager
    user_id = "test_user_id"
    context_manager = AgentContextManager(session, user_id)
    
    # Test context loading
    user_profile = context_manager.get_user_profile()
    print(f"User: {user_profile.username}")
    print(f"Risk tolerance: {user_profile.risk_tolerance}")
    
    portfolio_context = context_manager.get_portfolio_context()
    print(f"Portfolio value: ${portfolio_context.total_value:.2f}")
    print(f"Positions: {portfolio_context.position_count}")
    
    market_context = context_manager.get_market_context()
    print(f"Market open: {market_context.market_open}")
    print(f"Market state: {market_context.market_state}")
    
    # Test tools context
    tools_context = context_manager.create_tools_context()
    print(f"Available tools: {len([k for k in tools_context.keys() if 'tool' in k])}")
    
    session.close()