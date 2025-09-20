# Layer 5: User History Storage System
# Manages user interaction history and behavioral data for personalization

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
from collections import defaultdict


class UserHistoryManager:
    """
    Manages user interaction history and behavioral patterns - Layer 5 of 5-layer architecture
    In production, this would use a proper database (PostgreSQL with JSONB)
    For demo, using in-memory storage with persistence simulation
    """
    
    def __init__(self):
        # In-memory storage for demo (in production: PostgreSQL/MongoDB)
        self.user_interactions: Dict[str, List[Dict]] = defaultdict(list)
        self.portfolio_history: Dict[str, List[Dict]] = defaultdict(list)
        self.user_preferences: Dict[str, Dict] = {}
        self.conversation_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Analytics data
        self.user_behavior_patterns: Dict[str, Dict] = defaultdict(dict)
        
        print("🏛️ Layer 5: User History Manager initialized")
    
    async def store_interaction(self, user_id: str, interaction_data: Dict[str, Any]) -> str:
        """
        Store user interaction data - Main Layer 5 function
        Called by Agent tools (Layer 4) to record user behavior
        """
        interaction_id = str(uuid.uuid4())
        
        interaction_record = {
            "interaction_id": interaction_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "action_type": interaction_data.get("action", "unknown"),
            "data": interaction_data,
            "session_id": interaction_data.get("session_id"),
            "context": interaction_data.get("context", {})
        }
        
        self.user_interactions[user_id].append(interaction_record)
        
        # Keep only last 1000 interactions per user
        if len(self.user_interactions[user_id]) > 1000:
            self.user_interactions[user_id] = self.user_interactions[user_id][-1000:]
        
        # Update behavioral patterns
        await self._update_behavior_patterns(user_id, interaction_record)
        
        print(f"📝 Stored interaction for {user_id}: {interaction_data.get('action', 'unknown')}")
        return interaction_id
    
    async def store_portfolio_snapshot(self, user_id: str, portfolio_data: Dict[str, Any]) -> str:
        """Store portfolio performance snapshot"""
        snapshot_id = str(uuid.uuid4())
        
        snapshot_record = {
            "snapshot_id": snapshot_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": portfolio_data.get("total_market_value", 0),
            "holdings": portfolio_data.get("holdings", []),
            "unrealized_pnl": portfolio_data.get("total_unrealized_pnl", 0),
            "return_percent": portfolio_data.get("total_return_percent", 0),
            "sector_allocation": portfolio_data.get("sector_allocation", {}),
            "risk_metrics": portfolio_data.get("risk_metrics", {})
        }
        
        self.portfolio_history[user_id].append(snapshot_record)
        
        # Keep only last 365 snapshots (daily for a year)
        if len(self.portfolio_history[user_id]) > 365:
            self.portfolio_history[user_id] = self.portfolio_history[user_id][-365:]
        
        print(f"💼 Stored portfolio snapshot for {user_id}: ${portfolio_data.get('total_market_value', 0):,.2f}")
        return snapshot_id
    
    async def store_conversation(self, user_id: str, user_query: str, agent_response: str, 
                               context: Optional[Dict] = None) -> str:
        """Store agent conversation history"""
        conversation_id = str(uuid.uuid4())
        
        conversation_record = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "agent_response": agent_response,
            "context": context or {},
            "query_length": len(user_query),
            "response_length": len(agent_response),
            "extracted_symbols": self._extract_symbols(user_query),
            "query_type": self._classify_query_type(user_query)
        }
        
        self.conversation_history[user_id].append(conversation_record)
        
        # Keep only last 500 conversations per user
        if len(self.conversation_history[user_id]) > 500:
            self.conversation_history[user_id] = self.conversation_history[user_id][-500:]
        
        print(f"💬 Stored conversation for {user_id}: {user_query[:50]}...")
        return conversation_id
    
    async def get_user_stock_history(self, user_id: str, symbol: str) -> Dict[str, Any]:
        """Get user's historical interactions with a specific stock"""
        interactions = self.user_interactions.get(user_id, [])
        
        stock_interactions = []
        for interaction in interactions:
            if (interaction["data"].get("symbol") == symbol or 
                symbol in interaction["data"].get("symbols", []) or
                symbol in interaction["data"].get("related_symbols", [])):
                stock_interactions.append(interaction)
        
        if not stock_interactions:
            return {
                "symbol": symbol,
                "interaction_count": 0,
                "first_interaction": None,
                "last_interaction": None,
                "interaction_types": [],
                "sentiment_trend": "neutral"
            }
        
        # Analyze interactions
        interaction_types = [i["action_type"] for i in stock_interactions]
        interaction_counts = {}
        for action in interaction_types:
            interaction_counts[action] = interaction_counts.get(action, 0) + 1
        
        # Calculate sentiment trend (simplified)
        sentiment_scores = []
        for interaction in stock_interactions:
            if "sentiment" in interaction["data"]:
                sentiment_scores.append(interaction["data"]["sentiment"])
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        sentiment_trend = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
        
        return {
            "symbol": symbol,
            "interaction_count": len(stock_interactions),
            "first_interaction": stock_interactions[0]["timestamp"],
            "last_interaction": stock_interactions[-1]["timestamp"],
            "interaction_types": list(interaction_counts.keys()),
            "interaction_frequency": interaction_counts,
            "sentiment_trend": sentiment_trend,
            "recent_interactions": stock_interactions[-5:]  # Last 5 interactions
        }
    
    async def get_user_investment_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's investment patterns and behavior"""
        interactions = self.user_interactions.get(user_id, [])
        portfolio_history = self.portfolio_history.get(user_id, [])
        conversations = self.conversation_history.get(user_id, [])
        
        if not interactions and not conversations:
            return {"pattern": "insufficient_data"}
        
        # Analyze interaction patterns
        if interactions:
            action_frequency = {}
            for interaction in interactions:
                action = interaction["action_type"]
                action_frequency[action] = action_frequency.get(action, 0) + 1
            
            # Find most common actions
            most_common_actions = sorted(action_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
        else:
            most_common_actions = []
        
        # Analyze portfolio patterns
        portfolio_trends = {}
        if len(portfolio_history) >= 2:
            recent_snapshots = portfolio_history[-10:]  # Last 10 snapshots
            
            # Calculate volatility tolerance
            value_changes = []
            for i in range(1, len(recent_snapshots)):
                prev_value = recent_snapshots[i-1]["portfolio_value"]
                curr_value = recent_snapshots[i]["portfolio_value"]
                if prev_value > 0:
                    change_percent = ((curr_value / prev_value) - 1) * 100
                    value_changes.append(abs(change_percent))
            
            avg_volatility = sum(value_changes) / len(value_changes) if value_changes else 0
            
            portfolio_trends = {
                "avg_portfolio_volatility": avg_volatility,
                "snapshots_count": len(recent_snapshots),
                "trend": "upward" if recent_snapshots[-1]["portfolio_value"] > recent_snapshots[0]["portfolio_value"] else "downward"
            }
        
        # Analyze conversation patterns
        conversation_patterns = {}
        if conversations:
            query_types = [conv["query_type"] for conv in conversations]
            type_frequency = {}
            for qtype in query_types:
                type_frequency[qtype] = type_frequency.get(qtype, 0) + 1
            
            most_common_queries = sorted(type_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            
            conversation_patterns = {
                "total_conversations": len(conversations),
                "most_common_query_types": most_common_queries,
                "avg_query_length": sum(c["query_length"] for c in conversations) / len(conversations),
                "recent_activity": len([c for c in conversations if 
                                      datetime.fromisoformat(c["timestamp"]) > datetime.now() - timedelta(days=7)])
            }
        
        # Determine user investment personality
        personality = self._determine_investment_personality(interactions, portfolio_history, conversations)
        
        return {
            "user_id": user_id,
            "analysis_date": datetime.now().isoformat(),
            "interaction_patterns": {
                "total_interactions": len(interactions),
                "most_common_actions": most_common_actions,
                "recent_activity_score": len([i for i in interactions if 
                                            datetime.fromisoformat(i["timestamp"]) > datetime.now() - timedelta(days=7)])
            },
            "portfolio_patterns": portfolio_trends,
            "conversation_patterns": conversation_patterns,
            "investment_personality": personality,
            "behavioral_insights": self.user_behavior_patterns.get(user_id, {}),
            "data_quality": {
                "has_interactions": len(interactions) > 0,
                "has_portfolio_history": len(portfolio_history) > 0,
                "has_conversations": len(conversations) > 0,
                "data_completeness": self._calculate_data_completeness(interactions, portfolio_history, conversations)
            }
        }
    
    def _determine_investment_personality(self, interactions: List, portfolio_history: List, 
                                        conversations: List) -> Dict[str, Any]:
        """Determine user's investment personality based on behavior"""
        personality_traits = {
            "risk_tolerance": "moderate",
            "trading_frequency": "moderate", 
            "analysis_depth": "moderate",
            "emotional_trading": False,
            "long_term_focus": True
        }
        
        # Analyze trading frequency
        if interactions:
            recent_interactions = [i for i in interactions if 
                                 datetime.fromisoformat(i["timestamp"]) > datetime.now() - timedelta(days=30)]
            
            if len(recent_interactions) > 50:
                personality_traits["trading_frequency"] = "high"
            elif len(recent_interactions) < 10:
                personality_traits["trading_frequency"] = "low"
        
        # Analyze risk tolerance from conversations
        if conversations:
            risk_keywords = {
                "high_risk": ["aggressive", "risky", "volatile", "speculative"],
                "low_risk": ["safe", "conservative", "stable", "secure"]
            }
            
            high_risk_mentions = sum(1 for conv in conversations 
                                   for keyword in risk_keywords["high_risk"]
                                   if keyword in conv["user_query"].lower())
            low_risk_mentions = sum(1 for conv in conversations
                                  for keyword in risk_keywords["low_risk"]
                                  if keyword in conv["user_query"].lower())
            
            if high_risk_mentions > low_risk_mentions * 2:
                personality_traits["risk_tolerance"] = "aggressive"
            elif low_risk_mentions > high_risk_mentions * 2:
                personality_traits["risk_tolerance"] = "conservative"
        
        return personality_traits
    
    def _calculate_data_completeness(self, interactions: List, portfolio_history: List, 
                                   conversations: List) -> float:
        """Calculate how complete the user's data is (0-1 scale)"""
        completeness_score = 0.0
        
        if interactions:
            completeness_score += 0.3
        if portfolio_history:
            completeness_score += 0.4
        if conversations:
            completeness_score += 0.3
        
        # Bonus for having recent data
        now = datetime.now()
        if any(datetime.fromisoformat(i["timestamp"]) > now - timedelta(days=7) for i in interactions):
            completeness_score += 0.1
        
        return min(completeness_score, 1.0)
    
    async def _update_behavior_patterns(self, user_id: str, interaction: Dict) -> None:
        """Update user behavioral patterns based on new interaction"""
        if user_id not in self.user_behavior_patterns:
            self.user_behavior_patterns[user_id] = {
                "preferred_symbols": {},
                "activity_times": [],
                "action_sequences": [],
                "sentiment_pattern": []
            }
        
        patterns = self.user_behavior_patterns[user_id]
        
        # Track preferred symbols
        symbol = interaction["data"].get("symbol")
        if symbol:
            patterns["preferred_symbols"][symbol] = patterns["preferred_symbols"].get(symbol, 0) + 1
        
        # Track activity times (hour of day)
        hour = datetime.fromisoformat(interaction["timestamp"]).hour
        patterns["activity_times"].append(hour)
        
        # Track action sequences (for pattern recognition)
        patterns["action_sequences"].append(interaction["action_type"])
        if len(patterns["action_sequences"]) > 50:  # Keep last 50 actions
            patterns["action_sequences"] = patterns["action_sequences"][-50:]
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        import re
        symbols = re.findall(r'\b[A-Z]{1,5}\b', text)
        # Filter out common words
        common_words = {"THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "GET", "NEW"}
        return [s for s in symbols if s not in common_words and len(s) >= 2]
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of user query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["price", "cost", "quote", "$"]):
            return "price_inquiry"
        elif any(word in query_lower for word in ["news", "article", "headline"]):
            return "news_request"
        elif any(word in query_lower for word in ["portfolio", "holdings", "positions"]):
            return "portfolio_analysis"
        elif any(word in query_lower for word in ["buy", "sell", "should", "recommend"]):
            return "investment_advice"
        elif any(word in query_lower for word in ["analysis", "analyze", "technical", "fundamental"]):
            return "stock_analysis"
        elif any(word in query_lower for word in ["risk", "volatile", "safe"]):
            return "risk_assessment"
        else:
            return "general_inquiry"
    
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get summary of user activity over specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        interactions = self.user_interactions.get(user_id, [])
        conversations = self.conversation_history.get(user_id, [])
        
        recent_interactions = [i for i in interactions if 
                             datetime.fromisoformat(i["timestamp"]) > cutoff_date]
        recent_conversations = [c for c in conversations if
                              datetime.fromisoformat(c["timestamp"]) > cutoff_date]
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_interactions": len(recent_interactions),
            "total_conversations": len(recent_conversations),
            "active_days": len(set(datetime.fromisoformat(i["timestamp"]).date() 
                                 for i in recent_interactions + recent_conversations)),
            "most_active_day": self._get_most_active_day(recent_interactions + recent_conversations),
            "activity_trend": "increasing" if len(recent_interactions) > len(interactions) * 0.1 else "stable"
        }
    
    def _get_most_active_day(self, activities: List) -> Optional[str]:
        """Find the day with most activity"""
        if not activities:
            return None
        
        day_counts = {}
        for activity in activities:
            day = datetime.fromisoformat(activity["timestamp"]).date().isoformat()
            day_counts[day] = day_counts.get(day, 0) + 1
        
        return max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None


# Global service instance
_user_history_manager = UserHistoryManager()


async def store_interaction(user_id: str, interaction_data: Dict[str, Any]) -> str:
    """Store user interaction - Main Layer 5 function"""
    return await _user_history_manager.store_interaction(user_id, interaction_data)


async def store_portfolio_snapshot(user_id: str, portfolio_data: Dict[str, Any]) -> str:
    """Store portfolio snapshot"""
    return await _user_history_manager.store_portfolio_snapshot(user_id, portfolio_data)


async def store_conversation(user_id: str, user_query: str, agent_response: str, 
                           context: Optional[Dict] = None) -> str:
    """Store conversation"""
    return await _user_history_manager.store_conversation(user_id, user_query, agent_response, context)


async def get_user_stock_history(user_id: str, symbol: str) -> Dict[str, Any]:
    """Get user's stock interaction history"""
    return await _user_history_manager.get_user_stock_history(user_id, symbol)


async def get_user_investment_patterns(user_id: str) -> Dict[str, Any]:
    """Get user investment patterns"""
    return await _user_history_manager.get_user_investment_patterns(user_id)


def get_user_activity_summary(user_id: str, days: int = 30) -> Dict[str, Any]:
    """Get user activity summary"""
    return _user_history_manager.get_user_activity_summary(user_id, days)


def get_user_history_manager() -> UserHistoryManager:
    """Get the user history manager instance"""
    return _user_history_manager


# Testing function
async def test_user_history_manager():
    """Test the user history management system"""
    print("🧪 Testing Layer 5: User History Manager")
    print("=" * 50)
    
    test_user_id = "test_user_123"
    
    # Test storing interactions
    print("\n📝 Testing interaction storage...")
    await store_interaction(test_user_id, {
        "action": "stock_analysis",
        "symbol": "AAPL",
        "data": {"price": 175.0, "sentiment": 0.7}
    })
    
    await store_interaction(test_user_id, {
        "action": "portfolio_check",
        "data": {"total_value": 50000}
    })
    
    # Test storing conversations
    print("\n💬 Testing conversation storage...")
    await store_conversation(
        test_user_id, 
        "What's the current price of AAPL?",
        "Apple (AAPL) is currently trading at $175.00, up 2.3% today."
    )
    
    # Test pattern analysis
    print("\n🔍 Testing pattern analysis...")
    patterns = await get_user_investment_patterns(test_user_id)
    print(f"✅ Investment patterns: {json.dumps(patterns, indent=2, default=str)}")
    
    # Test stock history
    print("\n📈 Testing stock history...")
    stock_history = await get_user_stock_history(test_user_id, "AAPL")
    print(f"✅ AAPL history: {json.dumps(stock_history, indent=2, default=str)}")
    
    # Test activity summary
    print("\n📊 Testing activity summary...")
    activity = get_user_activity_summary(test_user_id)
    print(f"✅ Activity summary: {json.dumps(activity, indent=2, default=str)}")


if __name__ == "__main__":
    print("🚀 Layer 5: User History Manager - Testing Mode")
    asyncio.run(test_user_history_manager())