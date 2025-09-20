# Simple WebSocket Chat Manager using Direct OpenAI Integration
# Replacement for pydantic-ai based chat due to Python 3.10 compatibility issues

import asyncio
import json
import logging
import uuid
from typing import Dict, Optional, Any
from datetime import datetime
from fastapi import WebSocket

from agents.simple_ai_agent import SimpleAITradingAgent, UserContext, create_simple_ai_trading_agent

logger = logging.getLogger(__name__)

class SimpleChatSession:
    """Simple chat session for WebSocket communication"""
    
    def __init__(self, user_id: str, session_id: str, websocket: Optional[WebSocket] = None):
        self.user_id = user_id
        self.session_id = session_id
        self.websocket = websocket
        self.created_at = datetime.now()
        self.message_history: list = []
        
        # User context (in real app, this would be loaded from database)
        self.user_context = UserContext(
            user_id=user_id,
            followed_symbols=["AAPL", "GOOGL", "MSFT"],  # Default symbols
            risk_tolerance="medium",
            portfolio_value=25000.0
        )
        
        # AI agent
        self.ai_agent = create_simple_ai_trading_agent()
        
    async def process_user_message(self, message: str) -> Dict[str, Any]:
        """Process user message and generate AI response"""
        try:
            # Add user message to history
            user_message = {
                "type": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            self.message_history.append(user_message)
            
            # Generate AI response if agent is available
            if self.ai_agent:
                ai_response = await self.ai_agent.process_message(message, self.user_context)
                
                # Add AI response to history
                agent_message = {
                    "type": "agent", 
                    "content": ai_response.content,
                    "tool_calls": ai_response.tool_calls,
                    "timestamp": ai_response.timestamp
                }
                self.message_history.append(agent_message)
                
                return {
                    "session_id": self.session_id,
                    "response": ai_response.content,
                    "tool_calls": ai_response.tool_calls,
                    "context_used": ai_response.context_used,
                    "timestamp": ai_response.timestamp
                }
            else:
                # Fallback response when AI agent is not available
                fallback_response = f"I received your message: '{message}'. However, I'm currently experiencing technical difficulties with the AI system. Please try again later."
                
                fallback_message = {
                    "type": "agent",
                    "content": fallback_response,
                    "timestamp": datetime.now().isoformat()
                }
                self.message_history.append(fallback_message)
                
                return {
                    "session_id": self.session_id,
                    "response": fallback_response,
                    "tool_calls": [],
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            
            return {
                "session_id": self.session_id,
                "response": error_response,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "message_count": len(self.message_history),
            "user_context": self.user_context.model_dump(),
            "ai_agent_available": self.ai_agent is not None
        }

class SimpleChatManager:
    """Simple chat manager for WebSocket connections"""
    
    def __init__(self):
        self.active_sessions: Dict[str, SimpleChatSession] = {}
        self.websocket_sessions: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Connect a user and create a new chat session"""
        session_id = str(uuid.uuid4())
        
        # Create new chat session
        chat_session = SimpleChatSession(user_id, session_id, websocket)
        
        # Store session
        self.active_sessions[session_id] = chat_session
        self.websocket_sessions[session_id] = websocket
        
        logger.info(f"New chat session created: {session_id} for user: {user_id}")
        return session_id
    
    async def disconnect(self, session_id: str):
        """Disconnect a chat session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.websocket_sessions:
            del self.websocket_sessions[session_id]
        
        logger.info(f"Chat session disconnected: {session_id}")
    
    async def handle_message(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Handle incoming message from WebSocket"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        chat_session = self.active_sessions[session_id]
        return await chat_session.process_user_message(message)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].get_session_info()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chat manager statistics"""
        return {
            "active_sessions": len(self.active_sessions),
            "total_messages": sum(len(session.message_history) for session in self.active_sessions.values()),
            "sessions_with_ai": sum(1 for session in self.active_sessions.values() if session.ai_agent is not None)
        }

# Global chat manager instance
simple_chat_manager = SimpleChatManager()

# Backward compatibility - export the same interface
chat_manager = simple_chat_manager