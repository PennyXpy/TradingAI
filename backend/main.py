# backend/main.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="../.env")  # Load from parent directory

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from services.simple_chat_manager import simple_chat_manager as chat_manager
import logging
import json
from datetime import datetime

# 导入routers (Updated paths after consolidating service folders)
from services.auth import auth_router
from services.main_routes import router as main_router  # 👈 你的新业务路由
from services.user_portfolio import portfolio_router
from services.ai_chat_routes import router as ai_chat_router  # 👈 Re-enabled for Python 3.13
from services.five_layer_routes import router as five_layer_router  # 👈 新的5层架构路由

app = FastAPI(
    title="TradingAI API",
    description="""
    ## TradingAI - Intelligent Trading Assistant API
    
    A comprehensive API for financial data, real-time market information, and AI-powered trading insights.
    
    ### Features:
    - **Real-time Stock Data** from Polygon.io
    - **Financial News** from NewsAPI  
    - **AI Trading Agent** with OpenAI integration
    - **WebSocket Streaming** for live price updates
    - **Portfolio Management** and analysis
    - **5-Layer Architecture** for optimal performance
    
    ### API Categories:
    - **Market Data**: Stocks, ETFs, Cryptocurrencies, Market Indexes
    - **News & Analysis**: Financial news with sentiment analysis
    - **AI Agent**: Intelligent trading recommendations and chat
    - **Real-time**: WebSocket endpoints for live data
    - **Portfolio**: User portfolio and watchlist management
    
    ### Authentication:
    Most endpoints are public for testing. Portfolio endpoints require authentication.
    """,
    version="1.0.0",
    contact={
        "name": "TradingAI API Support",
        "email": "support@tradingai.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/",
    summary="API Welcome",
    description="Welcome endpoint for TradingAI API",
    tags=["System"]
)
def read_root():
    """
    **Welcome to TradingAI API**
    
    This is the main entry point for the TradingAI API.
    Navigate to `/docs` to explore all available endpoints.
    """
    return {"msg": "Welcome to TradingAI API"}

@app.get(
    "/debug/env",
    summary="Environment Debug",
    description="Debug endpoint to check API key configuration",
    tags=["System"]
)
def debug_env():
    """
    **Environment Variables Debug**
    
    Check if API keys are properly loaded from environment variables.
    Shows preview of first 10 characters of each API key for security.
    
    **Use this to verify**:
    - Polygon.io API key is loaded
    - NewsAPI key is loaded  
    - OpenAI API key is loaded
    """
    return {
        "polygon_api_key_loaded": bool(os.getenv("POLYGON_API_KEY")),
        "news_api_key_loaded": bool(os.getenv("NEWS_API_KEY")),
        "openai_api_key_loaded": bool(os.getenv("OPENAI_API_KEY")),
        "polygon_key_preview": os.getenv("POLYGON_API_KEY", "")[:10] + "..." if os.getenv("POLYGON_API_KEY") else "Not found",
        "news_key_preview": os.getenv("NEWS_API_KEY", "")[:10] + "..." if os.getenv("NEWS_API_KEY") else "Not found"
    }

# 👇 注册多个模块路由
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])  # 登录注册相关接口
app.include_router(main_router, tags=["Market Data", "News & Analysis"])  # 股票/新闻/加密币信息接口
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio Management"])
app.include_router(ai_chat_router, tags=["AI Agent"])  # AI聊天和智能分析接口
app.include_router(five_layer_router, tags=["System Architecture"])  # 5层架构路由

# WebSocket Chat Endpoint
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str = Query(...)):
    """WebSocket endpoint for real-time chat with TradingAI agent"""
    session_id = await chat_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message through chat manager
            response = await chat_manager.handle_message(session_id, data)
            
            # Send response back to client
            if response:
                await websocket.send_json({
                    "type": "response",
                    "session_id": session_id,
                    "data": response,
                    "timestamp": response.get("timestamp")
                })
    
    except WebSocketDisconnect:
        await chat_manager.disconnect(session_id)
        logging.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        await chat_manager.disconnect(session_id)

# Real-Time Market Data WebSocket
@app.websocket("/ws/realtime")
async def websocket_realtime_endpoint(websocket: WebSocket, client_id: str = Query(...)):
    """WebSocket endpoint for real-time market data from Polygon.io"""
    from services.realtime_data_manager import get_realtime_manager
    
    realtime_manager = await get_realtime_manager()
    
    # Connect client
    connected = await realtime_manager.connect_client(client_id, websocket)
    if not connected:
        return
    
    try:
        while True:
            # Receive subscription requests from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    symbols = message.get("symbols", [])
                    await realtime_manager.subscribe_client(client_id, symbols)
                    
                elif action == "unsubscribe":
                    symbol = message.get("symbol")
                    if symbol:
                        await realtime_manager.unsubscribe_client(client_id, symbol)
                        
                elif action == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                    
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON format"})
                
    except WebSocketDisconnect:
        await realtime_manager.disconnect_client(client_id)
        logging.info(f"Real-time WebSocket disconnected for client: {client_id}")
    except Exception as e:
        logging.error(f"Real-time WebSocket error: {str(e)}")
        await realtime_manager.disconnect_client(client_id)

# Chat Session Management Endpoints
@app.get("/chat/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a chat session"""
    session_info = chat_manager.get_session_info(session_id)
    if session_info:
        return session_info
    else:
        return {"error": "Session not found"}

# Real-Time Data Management Endpoints
@app.get("/realtime/stats")
async def get_realtime_stats():
    """Get real-time data manager statistics"""
    from services.realtime_data_manager import get_realtime_manager
    
    realtime_manager = await get_realtime_manager()
    return realtime_manager.get_connection_stats()

# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logging.info("Starting TradingAI backend services...")
    
    # Initialize Polygon services
    from services.polygon_websocket_service import get_polygon_service
    from services.polygon_rest_service import get_polygon_rest_service
    
    await get_polygon_service()
    await get_polygon_rest_service()
    
    # Initialize real-time data manager
    from services.realtime_data_manager import get_realtime_manager
    await get_realtime_manager()
    
    logging.info("TradingAI backend started successfully")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup services on shutdown"""
    logging.info("Shutting down TradingAI backend services...")
    
    # Shutdown Polygon services
    from services.polygon_websocket_service import shutdown_polygon_service
    await shutdown_polygon_service()
    
    # Shutdown real-time data manager
    from services.realtime_data_manager import shutdown_realtime_manager
    await shutdown_realtime_manager()
    
    logging.info("TradingAI backend shutdown complete")