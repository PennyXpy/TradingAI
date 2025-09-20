# Simple Chat Manager for Testing
# Simplified version without complex AI agent dependencies

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import json
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleChatSession:
    """Simple chat session for testing"""
    
    def __init__(self, user_id: str, session_id: str, websocket: WebSocket):
        self.user_id = user_id
        self.session_id = session_id
        self.websocket = websocket
        self.is_active = True
        self.created_at = datetime.now()
        self.messages = []
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to websocket"""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.is_active = False
    
    async def handle_user_message(self, content: str) -> Dict[str, Any]:
        """Handle incoming user message and generate response"""
        # Store user message
        user_message = {
            "type": "user_message",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(user_message)
        
        # Generate simple AI response
        ai_response = self._generate_simple_response(content)
        
        # Store AI response
        ai_message = {
            "type": "ai_response", 
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(ai_message)
        
        return {
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
    
    def _generate_simple_response(self, user_input: str) -> str:
        """Generate simple rule-based responses"""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello! I'm your AI trading assistant. I can help you with market analysis, stock information, and trading insights. What would you like to know?"
        
        elif any(word in user_input_lower for word in ['aapl', 'apple']):
            return "Apple Inc. (AAPL) is currently trading well. Based on recent market data, AAPL shows strong fundamentals with solid earnings growth. The stock has been performing consistently in the tech sector. Would you like more detailed analysis?"
        
        elif any(word in user_input_lower for word in ['stock', 'market', 'price']):
            return "The current market is showing mixed signals. Major indexes like S&P 500 are holding steady, while tech stocks show some volatility. I can provide specific analysis for any stock you're interested in. Which stocks would you like me to analyze?"
        
        elif any(word in user_input_lower for word in ['news', 'latest']):
            return "Recent market news includes: Federal Reserve policy updates, tech sector earnings, and global economic indicators. The overall sentiment appears cautiously optimistic. Would you like me to dive deeper into any specific sector?"
        
        elif any(word in user_input_lower for word in ['buy', 'sell', 'recommend']):
            return "I can provide analysis to help inform your decisions, but remember that all trading involves risk. Based on current market conditions, I'd suggest focusing on companies with strong fundamentals and clear growth prospects. What's your investment timeframe and risk tolerance?"
        
        elif any(word in user_input_lower for word in ['trend', 'analysis']):
            return "Current market trends show: 1) Continued interest in AI and technology stocks, 2) Energy sector volatility, 3) Healthcare showing stability. The key is diversification and staying informed. What specific trends are you most interested in?"
        
        else:
            return f"I understand you're asking about '{user_input}'. As your AI trading assistant, I can help analyze market data, provide stock insights, and discuss investment strategies. Could you be more specific about what kind of analysis you're looking for?"

class SimpleChatManager:
    """Simple chat manager for WebSocket connections"""
    
    def __init__(self):
        self.active_sessions: Dict[str, SimpleChatSession] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Connect a new WebSocket client"""
        try:
            await websocket.accept()
            
            session_id = str(uuid.uuid4())
            session = SimpleChatSession(user_id, session_id, websocket)
            self.active_sessions[session_id] = session
            
            logger.info(f"New chat session created: {session_id} for user: {user_id}")
            
            # Send welcome message
            welcome_response = {
                "content": f"Welcome to TradingAI! I'm your AI assistant ready to help with market analysis and trading insights. How can I assist you today?",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to connect chat session: {e}")
            raise
    
    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_active = False
            del self.active_sessions[session_id]
            logger.info(f"Chat session disconnected: {session_id}")
    
    async def handle_message(self, session_id: str, content: str) -> Optional[Dict[str, Any]]:
        """Handle incoming message from client"""
        if session_id not in self.active_sessions:
            logger.warning(f"Message received for unknown session: {session_id}")
            return None
        
        try:
            session = self.active_sessions[session_id]
            response = await session.handle_user_message(content)
            logger.info(f"Generated response for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error handling message for session {session_id}: {e}")
            return {
                "content": "I apologize, but I encountered an error processing your message. Please try again.",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "error": True
            }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "is_active": session.is_active,
                "message_count": len(session.messages)
            }
        return None

# Global simple chat manager instance
simple_chat_manager = SimpleChatManager()