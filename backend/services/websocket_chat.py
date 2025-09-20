# WebSocket Chat Service for TradingAI Agent
# Provides coherent chat sessions like Claude with user authentication and session management

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict, List, Any, Optional
import json
import asyncio
import uuid
from datetime import datetime
import logging

from services.user_data_filter import UserDataFilter
from services.user_history_manager import UserHistoryManager
from agents.tools import (
    MarketDataTool, NewsAnalysisTool, PortfolioTool, 
    AnalysisTool, RecommendationTool
)
from models.core_models import AgentContext

logger = logging.getLogger(__name__)

class ChatSession:
    """Individual chat session for a user"""
    
    def __init__(self, user_id: str, session_id: str, websocket: WebSocket):
        self.user_id = user_id
        self.session_id = session_id
        self.websocket = websocket
        self.is_active = True
        self.created_at = datetime.now()
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Initialize AI agent tools
        self.market_tool = MarketDataTool()
        self.news_tool = NewsAnalysisTool()
        self.portfolio_tool = PortfolioTool()
        self.analysis_tool = AnalysisTool()
        self.recommendation_tool = RecommendationTool()
        
        # User context services
        self.user_filter = UserDataFilter()
        self.history_manager = UserHistoryManager()
    
    async def add_message(self, message: Dict[str, Any]):
        """Add a message to conversation history"""
        message['timestamp'] = datetime.now().isoformat()
        message['session_id'] = self.session_id
        self.conversation_history.append(message)
        
        # Store interaction in user history
        await self.history_manager.store_interaction(self.user_id, {
            "action": "chat_message",
            "message_type": message.get("type", "user"),
            "content": message.get("content", ""),
            "session_id": self.session_id
        })
    
    async def get_user_context(self) -> Dict[str, Any]:
        """Get current user context for AI agent"""
        user_data = await self.user_filter.get_user_filtered_data(self.user_id)
        user_patterns = await self.history_manager.get_user_investment_patterns(self.user_id)
        
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "portfolio": user_data.get("portfolio_summary", {}),
            "followed_stocks": user_data.get("user_stocks", []),
            "relevant_news": user_data.get("relevant_news", []),
            "investment_patterns": user_patterns,
            "conversation_history": self.conversation_history[-10:],  # Last 10 messages for context
        }
    
    async def process_user_message(self, message: str) -> Dict[str, Any]:
        """Process user message and generate AI response"""
        try:
            # Add user message to history
            await self.add_message({
                "type": "user",
                "content": message,
                "sender": self.user_id
            })
            
            # Get user context
            context = await self.get_user_context()
            
            # Analyze message intent and generate response
            response = await self._generate_ai_response(message, context)
            
            # Add AI response to history
            await self.add_message({
                "type": "assistant",
                "content": response["content"],
                "sender": "trading_agent",
                "tools_used": response.get("tools_used", []),
                "analysis_data": response.get("analysis_data", {})
            })
            
            return {
                "session_id": self.session_id,
                "response": response["content"],
                "analysis_data": response.get("analysis_data", {}),
                "tools_used": response.get("tools_used", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_response = {
                "session_id": self.session_id,
                "response": f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question.",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.add_message({
                "type": "assistant",
                "content": error_response["response"],
                "sender": "trading_agent",
                "error": True
            })
            
            return error_response
    
    async def _generate_ai_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response using available tools and context"""
        message_lower = message.lower()
        tools_used = []
        analysis_data = {}
        
        # Intent detection and tool usage
        if any(word in message_lower for word in ['portfolio', 'holdings', 'investment']):
            # Portfolio-related query
            if context.get('portfolio'):
                portfolio_analysis = await self.portfolio_tool.analyze_portfolio_performance(context['portfolio'])
                analysis_data['portfolio_analysis'] = portfolio_analysis
                tools_used.append('portfolio_analysis')
                
                response_content = self._format_portfolio_response(portfolio_analysis, message)
            else:
                response_content = "I don't see any portfolio data for you yet. You can start by adding some investments to track your performance."
        
        elif any(word in message_lower for word in ['news', 'what\'s happening', 'market news']):
            # News-related query
            if context.get('relevant_news'):
                news_summary = await self.news_tool.summarize_news(context['relevant_news'])
                analysis_data['news_summary'] = news_summary
                tools_used.append('news_analysis')
                
                response_content = f"Here's what's happening in the markets:\n\n{news_summary}"
            else:
                response_content = "I don't have specific news for your followed stocks right now. Try asking about a specific stock or adding stocks to your watchlist."
        
        elif any(symbol in message.upper() for symbol in ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'META']):
            # Stock-specific query
            symbols = [word.upper() for word in message.split() if word.upper() in ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'META']]
            
            if symbols:
                symbol = symbols[0]
                stock_data = await self.market_tool.get_stock_data(symbol)
                analysis_data['stock_data'] = stock_data
                tools_used.append('market_data')
                
                # Technical analysis
                if 'analysis' in message_lower or 'technical' in message_lower:
                    tech_analysis = await self.analysis_tool.perform_technical_analysis(symbol, stock_data)
                    analysis_data['technical_analysis'] = tech_analysis
                    tools_used.append('technical_analysis')
                    
                    response_content = self._format_stock_analysis_response(stock_data, tech_analysis)
                else:
                    response_content = self._format_stock_response(stock_data)
        
        elif any(word in message_lower for word in ['recommend', 'should i buy', 'what do you think']):
            # Recommendation query
            if context.get('followed_stocks'):
                # Generate recommendation for first followed stock
                stock_symbol = context['followed_stocks'][0].get('symbol', 'AAPL')
                stock_data = await self.market_tool.get_stock_data(stock_symbol)
                
                recommendation = await self.recommendation_tool.generate_recommendation(
                    stock_symbol, 
                    stock_data, 
                    context.get('portfolio', {}),
                    {"risk_tolerance": "medium"}  # Default risk tolerance
                )
                
                analysis_data['recommendation'] = recommendation
                tools_used.append('recommendation')
                
                response_content = self._format_recommendation_response(recommendation)
            else:
                response_content = "I'd be happy to provide recommendations! First, could you tell me which stocks you're interested in or add some to your watchlist?"
        
        else:
            # General conversational response
            response_content = self._generate_general_response(message, context)
        
        return {
            "content": response_content,
            "tools_used": tools_used,
            "analysis_data": analysis_data
        }
    
    def _format_portfolio_response(self, portfolio_analysis: Dict[str, Any], original_message: str) -> str:
        """Format portfolio analysis into readable response"""
        total_value = portfolio_analysis.get('total_value', 0)
        total_return = portfolio_analysis.get('total_return', 0)
        return_percent = portfolio_analysis.get('total_return_percent', 0)
        
        response = f"Here's your portfolio overview:\n\n"
        response += f"💰 Total Value: ${total_value:,.2f}\n"
        response += f"📈 Total Return: ${total_return:,.2f} ({return_percent:+.2f}%)\n"
        response += f"📊 Number of Positions: {portfolio_analysis.get('position_count', 0)}\n\n"
        
        if portfolio_analysis.get('best_performer'):
            best = portfolio_analysis['best_performer']
            response += f"🏆 Best Performer: {best.get('symbol', 'N/A')}\n"
        
        if portfolio_analysis.get('worst_performer'):
            worst = portfolio_analysis['worst_performer']
            response += f"📉 Needs Attention: {worst.get('symbol', 'N/A')}\n"
        
        return response
    
    def _format_stock_response(self, stock_data: Dict[str, Any]) -> str:
        """Format stock data into readable response"""
        if 'error' in stock_data:
            return f"I couldn't find data for that stock. {stock_data['error']}"
        
        name = stock_data.get('name', 'Unknown')
        price = stock_data.get('price', 0)
        change = stock_data.get('change', 0)
        change_percent = stock_data.get('change_percent', 0)
        
        response = f"📊 {name}\n"
        response += f"💲 Current Price: ${price:.2f}\n"
        response += f"📈 Change: ${change:+.2f} ({change_percent:+.2f}%)\n"
        
        if stock_data.get('volume'):
            response += f"📊 Volume: {stock_data['volume']:,}\n"
        
        return response
    
    def _format_stock_analysis_response(self, stock_data: Dict[str, Any], tech_analysis: Dict[str, Any]) -> str:
        """Format stock data with technical analysis"""
        basic_info = self._format_stock_response(stock_data)
        
        analysis = f"\n🔍 Technical Analysis:\n"
        analysis += f"RSI: {tech_analysis.get('rsi', 'N/A')}\n"
        analysis += f"MACD: {tech_analysis.get('macd', 'N/A')}\n"
        analysis += f"Signal: {tech_analysis.get('signal', 'NEUTRAL')}\n"
        
        return basic_info + analysis
    
    def _format_recommendation_response(self, recommendation: Dict[str, Any]) -> str:
        """Format recommendation into readable response"""
        symbol = recommendation.get('symbol', 'Unknown')
        action = recommendation.get('action', 'HOLD')
        confidence = recommendation.get('confidence', 0.5)
        reasoning = recommendation.get('reasoning', 'Based on current analysis')
        
        response = f"💡 Recommendation for {symbol}:\n\n"
        response += f"🎯 Action: {action}\n"
        response += f"📊 Confidence: {confidence*100:.0f}%\n"
        response += f"🧠 Reasoning: {reasoning}\n"
        
        if recommendation.get('target_price'):
            response += f"🎯 Target Price: ${recommendation['target_price']:.2f}\n"
        
        return response
    
    def _generate_general_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate general conversational response"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        
        if any(greeting in message.lower() for greeting in greetings):
            return f"Hello! I'm your TradingAI assistant. I can help you analyze your portfolio, get market data, read news, and provide investment insights. What would you like to explore today?"
        
        return f"I'm here to help with your trading and investment questions. I can analyze your portfolio, provide stock data, summarize market news, and give recommendations. What specific information are you looking for?"


class WebSocketChatManager:
    """Manages WebSocket chat connections and sessions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, ChatSession] = {}
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Connect a user and create a new chat session"""
        await websocket.accept()
        
        session_id = str(uuid.uuid4())
        
        # Close existing connection for this user if any
        if user_id in self.user_connections:
            old_session = next((s for s in self.active_sessions.values() if s.user_id == user_id), None)
            if old_session:
                old_session.is_active = False
                await self.disconnect(old_session.session_id)
        
        # Create new session
        session = ChatSession(user_id, session_id, websocket)
        self.active_sessions[session_id] = session
        self.user_connections[user_id] = websocket
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "session_id": session_id,
            "message": "Connected to TradingAI. How can I help you today?",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"New chat session created: {session_id} for user {user_id}")
        return session_id
    
    async def disconnect(self, session_id: str):
        """Disconnect a chat session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_active = False
            
            if session.user_id in self.user_connections:
                del self.user_connections[session.user_id]
            
            del self.active_sessions[session_id]
            logger.info(f"Chat session disconnected: {session_id}")
    
    async def handle_message(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Handle incoming message from user"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        if not session.is_active:
            return {"error": "Session is no longer active"}
        
        try:
            response = await session.process_user_message(message)
            return response
        except Exception as e:
            logger.error(f"Error handling message in session {session_id}: {str(e)}")
            return {"error": f"Failed to process message: {str(e)}"}
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to a specific session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.is_active:
                try:
                    await session.websocket.send_json(message)
                except:
                    # Connection closed, clean up
                    await self.disconnect(session_id)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "is_active": session.is_active,
                "message_count": len(session.conversation_history)
            }
        return None


# Global chat manager instance
chat_manager = WebSocketChatManager()