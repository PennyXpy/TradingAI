# FastAPI Routes for 5-Layer Architecture
# Connects the 5 layers to HTTP endpoints for frontend consumption

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# Import all 5 layers
from services.data_collector import (
    start_data_collection, get_cached_data, get_all_cached_data, 
    get_data_collector, schedule_data_collection
)
from services.main_page_service import (
    get_market_overview, get_sector_performance, get_trending_stocks
)
from services.user_data_filter import (
    get_user_filtered_data, get_dashboard_data, get_user_followings
)
from agents.ai_trading_agent import create_ai_trading_agent
from services.user_history_manager import (
    store_interaction, get_user_investment_patterns, get_user_activity_summary
)

# Create router
router = APIRouter()

# Global agent instance (in production, this would be managed differently)
_trading_agent = None


async def get_trading_agent():
    """Get or create trading agent instance"""
    global _trading_agent
    if _trading_agent is None:
        _trading_agent = create_ai_trading_agent()
    return _trading_agent


# ============================================================================
# LAYER 1: Data Collection Endpoints
# ============================================================================

@router.post("/api/data-collection/start")
async def start_data_collection_endpoint(background_tasks: BackgroundTasks):
    """Start data collection process"""
    try:
        background_tasks.add_task(start_data_collection)
        return {
            "success": True,
            "message": "Data collection started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start data collection: {str(e)}")


@router.get("/api/data-collection/status")
async def get_data_collection_status():
    """Get data collection status"""
    try:
        collector = get_data_collector()
        status = collector.get_collection_status()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/api/cache/data/{data_type}")
async def get_cached_data_endpoint(data_type: str):
    """Get cached data by type"""
    try:
        cached_data = await get_cached_data(data_type)
        if cached_data is None:
            raise HTTPException(status_code=404, detail=f"No cached data found for {data_type}")
        
        return {
            "success": True,
            "data_type": data_type,
            "data": cached_data,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cached data: {str(e)}")


# ============================================================================
# LAYER 2: Main Page Endpoints
# ============================================================================

@router.get("/api/main/market-overview")
async def get_main_market_overview():
    """Get market overview for main page - Layer 2"""
    try:
        overview = await get_market_overview()
        if "error" in overview:
            raise HTTPException(status_code=503, detail=overview["error"])
        
        return {
            "success": True,
            "data": overview,
            "layer": "2 - Main Page Service"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market overview: {str(e)}")


@router.get("/api/main/sectors")
async def get_main_sector_performance():
    """Get sector performance for main page"""
    try:
        sectors = await get_sector_performance()
        if "error" in sectors:
            raise HTTPException(status_code=503, detail=sectors["error"])
            
        return {
            "success": True,
            "data": sectors,
            "layer": "2 - Main Page Service"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sector performance: {str(e)}")


@router.get("/api/main/trending")
async def get_main_trending_stocks(limit: int = 10):
    """Get trending stocks for main page"""
    try:
        trending = await get_trending_stocks(limit)
        return {
            "success": True,
            "data": trending,
            "layer": "2 - Main Page Service"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending stocks: {str(e)}")


# ============================================================================
# LAYER 3: User Data Filtering Endpoints  
# ============================================================================

@router.get("/api/user/{user_id}/dashboard")
async def get_user_dashboard_endpoint(user_id: str):
    """Get dashboard data for user - Layer 3"""
    try:
        dashboard_data = await get_dashboard_data(user_id)
        if "error" in dashboard_data:
            raise HTTPException(status_code=404, detail=dashboard_data["error"])
            
        return {
            "success": True,
            "data": dashboard_data,
            "layer": "3 - User Data Filter",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/api/user/{user_id}/filtered-data")
async def get_user_filtered_data_endpoint(user_id: str):
    """Get all filtered data for user - Layer 3"""
    try:
        filtered_data = await get_user_filtered_data(user_id)
        if "error" in filtered_data:
            raise HTTPException(status_code=404, detail=filtered_data["error"])
            
        return {
            "success": True,
            "data": filtered_data,
            "layer": "3 - User Data Filter",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filtered data: {str(e)}")


@router.get("/api/user/{user_id}/followings")
async def get_user_followings_endpoint(user_id: str):
    """Get user's followed symbols"""
    try:
        followings = get_user_followings(user_id)
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "followings": followings,
                "count": len(followings)
            },
            "layer": "3 - User Data Filter"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user followings: {str(e)}")


# ============================================================================
# LAYER 4: AI Agent Endpoints
# ============================================================================

@router.post("/api/agent/{user_id}/chat")
async def chat_with_agent(user_id: str, request: Dict[str, str]):
    """Chat with AI agent - Layer 4"""
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get trading agent
        agent = await get_trading_agent()
        if not agent.agent:
            raise HTTPException(status_code=503, detail="AI agent is not available")
        
        # Process chat
        response = await agent.chat(user_id, message)
        
        return {
            "success": True,
            "data": {
                "user_message": message,
                "agent_response": response,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            },
            "layer": "4 - AI Agent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent chat failed: {str(e)}")


@router.get("/api/agent/status")
async def get_agent_status():
    """Get AI agent status"""
    try:
        agent = await get_trading_agent()
        return {
            "success": True,
            "data": {
                "agent_available": agent.agent is not None,
                "model_name": agent.model_name,
                "status": "ready" if agent.agent else "unavailable",
                "layer": "4 - AI Agent"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "layer": "4 - AI Agent"
        }


# ============================================================================
# LAYER 5: User History Endpoints
# ============================================================================

@router.get("/api/user/{user_id}/investment-patterns")
async def get_user_investment_patterns_endpoint(user_id: str):
    """Get user's investment patterns - Layer 5"""
    try:
        patterns = await get_user_investment_patterns(user_id)
        return {
            "success": True,
            "data": patterns,
            "layer": "5 - User History Manager",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get investment patterns: {str(e)}")


@router.get("/api/user/{user_id}/activity-summary")
async def get_user_activity_summary_endpoint(user_id: str, days: int = 30):
    """Get user activity summary - Layer 5"""
    try:
        activity = get_user_activity_summary(user_id, days)
        return {
            "success": True,
            "data": activity,
            "layer": "5 - User History Manager",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity summary: {str(e)}")


@router.post("/api/user/{user_id}/interaction")
async def store_user_interaction_endpoint(user_id: str, interaction: Dict[str, Any]):
    """Store user interaction - Layer 5"""
    try:
        interaction_id = await store_interaction(user_id, interaction)
        return {
            "success": True,
            "data": {
                "interaction_id": interaction_id,
                "user_id": user_id,
                "stored_at": datetime.now().isoformat()
            },
            "layer": "5 - User History Manager"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store interaction: {str(e)}")


# ============================================================================
# System Health and Testing Endpoints
# ============================================================================

@router.get("/api/system/health")
async def system_health_check():
    """Check health of all 5 layers"""
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "layers": {}
    }
    
    # Layer 1: Data Collection
    try:
        collector = get_data_collector()
        status = collector.get_collection_status()
        health_status["layers"]["layer_1_data_collection"] = {
            "status": "healthy",
            "last_collection": status.get("last_update"),
            "collection_count": status.get("collection_count", 0)
        }
    except Exception as e:
        health_status["layers"]["layer_1_data_collection"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    # Layer 2: Main Page Service
    try:
        overview = await get_market_overview()
        health_status["layers"]["layer_2_main_page"] = {
            "status": "healthy" if "error" not in overview else "unhealthy",
            "data_available": "error" not in overview
        }
        if "error" in overview:
            health_status["overall_status"] = "degraded"
    except Exception as e:
        health_status["layers"]["layer_2_main_page"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    # Layer 3: User Data Filter
    try:
        test_data = await get_user_filtered_data("demo_user")
        health_status["layers"]["layer_3_user_filter"] = {
            "status": "healthy" if "error" not in test_data else "unhealthy",
            "test_user_data_available": "error" not in test_data
        }
    except Exception as e:
        health_status["layers"]["layer_3_user_filter"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    # Layer 4: AI Agent
    try:
        agent = await get_trading_agent()
        health_status["layers"]["layer_4_ai_agent"] = {
            "status": "healthy" if agent.agent else "unhealthy",
            "agent_available": agent.agent is not None,
            "model_name": agent.model_name
        }
        if not agent.agent:
            health_status["overall_status"] = "degraded"
    except Exception as e:
        health_status["layers"]["layer_4_ai_agent"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    # Layer 5: User History Manager
    try:
        activity = get_user_activity_summary("demo_user")
        health_status["layers"]["layer_5_user_history"] = {
            "status": "healthy",
            "history_system_available": True
        }
    except Exception as e:
        health_status["layers"]["layer_5_user_history"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    return {
        "success": True,
        "health": health_status
    }


@router.post("/api/system/initialize")
async def initialize_system(background_tasks: BackgroundTasks):
    """Initialize the complete 5-layer system"""
    try:
        # Start data collection
        background_tasks.add_task(start_data_collection)
        
        # Initialize agent
        await get_trading_agent()
        
        return {
            "success": True,
            "message": "5-layer system initialization started",
            "layers_initialized": [
                "Layer 1: Data Collection",
                "Layer 2: Main Page Service", 
                "Layer 3: User Data Filter",
                "Layer 4: AI Agent",
                "Layer 5: User History Manager"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System initialization failed: {str(e)}")


# Background task to start data collection on startup
@router.on_event("startup")
async def startup_event():
    """Start data collection when the API starts"""
    try:
        print("🚀 Starting 5-Layer TradingAI System...")
        await start_data_collection()
        print("✅ Initial data collection completed")
        
        # Initialize agent
        await get_trading_agent()
        print("✅ AI Agent initialized")
        
    except Exception as e:
        print(f"❌ Startup error: {str(e)}")


if __name__ == "__main__":
    # For testing the routes directly
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="5-Layer TradingAI API")
    app.include_router(router)
    
    print("🚀 Starting 5-Layer TradingAI API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)