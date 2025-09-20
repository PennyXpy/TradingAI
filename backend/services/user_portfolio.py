from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from models.core_models import User, UserFollowing as Followed
from services.auth import get_current_user
from services.polygon_rest_service import get_polygon_rest_service
from services.polygon_websocket_service import get_polygon_service
from data import engine

# 请求和响应模型
class FollowedCreate(BaseModel):
    symbol: str
    asset_type: str
    name: Optional[str] = None
    notes: Optional[str] = None


# 创建路由器 (现在仅处理关注列表，无投资功能)
portfolio_router = APIRouter()

# 辅助函数，获取数据库会话
def get_db():
    with Session(engine) as session:
        yield session

# 关注列表API端点
@portfolio_router.get("/followed")
async def get_followed_items(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    asset_type: Optional[str] = None
):
    """获取当前用户的所有关注项目"""
    query = select(Followed).where(Followed.user_id == user.id)
    
    if asset_type:
        query = query.where(Followed.asset_type == asset_type)
    
    followed_items = db.exec(query).all()
    return followed_items

@portfolio_router.post("/followed")
async def follow_item(
    item: FollowedCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加项目到关注列表"""
    # 检查是否已经关注
    existing = db.exec(
        select(Followed).where(
            Followed.user_id == user.id,
            Followed.symbol == item.symbol,
            Followed.asset_type == item.asset_type
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该项目已在关注列表中"
        )
    
    # 创建新关注项目
    followed_item = Followed(
        user_id=user.id,
        symbol=item.symbol,
        asset_type=item.asset_type,
        name=item.name,
        notes=item.notes
    )
    
    db.add(followed_item)
    db.commit()
    db.refresh(followed_item)
    
    return followed_item

@portfolio_router.delete("/followed/{item_id}")
async def unfollow_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从关注列表中移除项目"""
    # 查找项目
    followed_item = db.exec(
        select(Followed).where(
            Followed.id == item_id,
            Followed.user_id == user.id
        )
    ).first()
    
    if not followed_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关注项目未找到"
        )
    
    # 删除项目
    db.delete(followed_item)
    db.commit()
    
    return {"message": "项目已从关注列表中移除"}

@portfolio_router.get("/followed/realtime")
async def get_followed_with_realtime_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    asset_type: Optional[str] = None
):
    """获取关注列表中的实时股票数据"""
    # Get followed items
    query = select(Followed).where(Followed.user_id == user.id)
    
    if asset_type:
        query = query.where(Followed.asset_type == asset_type)
    
    followed_items = db.exec(query).all()
    
    # Get real-time data for followed stocks
    polygon_service = await get_polygon_rest_service()
    websocket_service = await get_polygon_service()
    
    enhanced_items = []
    
    for item in followed_items:
        # Get current market data
        if item.asset_type == "stock":
            stock_data = await polygon_service.get_stock_details(item.symbol)
            
            # Add real-time data if available
            latest_data = websocket_service.get_latest_data(item.symbol)
            if latest_data:
                stock_data.update(latest_data)
            
            enhanced_item = {
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "name": item.name or stock_data.get("name", item.symbol),
                "notes": item.notes,
                "followed_at": item.followed_at,
                "market_data": stock_data
            }
            enhanced_items.append(enhanced_item)
        else:
            # For non-stock assets, return basic info
            enhanced_items.append({
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "name": item.name,
                "notes": item.notes,
                "followed_at": item.followed_at,
                "market_data": None
            })
    
    return {"followed_items": enhanced_items, "count": len(enhanced_items)}

@portfolio_router.post("/followed/search-and-follow")
async def search_and_follow_stock(
    query: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索股票并添加到关注列表"""
    polygon_service = await get_polygon_rest_service()
    
    # Search for stocks
    search_results = await polygon_service.search_stocks(query, limit=5)
    
    if not search_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stocks found for query: {query}"
        )
    
    # For simplicity, follow the first result
    # In a real app, user would select which one to follow
    stock = search_results[0]
    
    # Check if already following
    existing = db.exec(
        select(Followed).where(
            Followed.user_id == user.id,
            Followed.symbol == stock["symbol"],
            Followed.asset_type == "stock"
        )
    ).first()
    
    if existing:
        return {
            "message": f"Already following {stock['symbol']}",
            "followed_item": existing,
            "search_results": search_results
        }
    
    # Create new followed item
    followed_item = Followed(
        user_id=user.id,
        symbol=stock["symbol"],
        asset_type="stock",
        name=stock["name"]
    )
    
    db.add(followed_item)
    db.commit()
    db.refresh(followed_item)
    
    return {
        "message": f"Successfully followed {stock['symbol']}",
        "followed_item": followed_item,
        "search_results": search_results
    }

@portfolio_router.get("/dashboard/data")
async def get_dashboard_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取仪表板所需的所有数据"""
    # Get followed stocks
    followed_stocks = db.exec(
        select(Followed).where(
            Followed.user_id == user.id,
            Followed.asset_type == "stock"
        )
    ).all()
    
    polygon_service = await get_polygon_rest_service()
    websocket_service = await get_polygon_service()
    
    # Get real-time data for followed stocks
    dashboard_stocks = []
    
    for stock in followed_stocks:
        stock_data = await polygon_service.get_stock_details(stock.symbol)
        
        # Add real-time data if available
        latest_data = websocket_service.get_latest_data(stock.symbol)
        if latest_data:
            stock_data.update(latest_data)
        
        dashboard_stocks.append({
            "id": stock.id,
            "symbol": stock.symbol,
            "name": stock.name or stock_data.get("name", stock.symbol),
            "type": "stock",
            "price": stock_data.get("price", 0),
            "change": stock_data.get("change", 0),
            "change_percent": stock_data.get("change_percent", 0),
            "isPositive": stock_data.get("change", 0) >= 0,
            "volume": stock_data.get("volume", 0),
            "market_cap": stock_data.get("market_cap"),
            "timestamp": stock_data.get("timestamp")
        })
    
    # If user has no followed stocks, provide some popular ones
    if not dashboard_stocks:
        popular_stocks = await polygon_service.get_top_stocks(5)
        
        for stock in popular_stocks:
            latest_data = websocket_service.get_latest_data(stock["symbol"])
            if latest_data:
                stock.update(latest_data)
            
            dashboard_stocks.append({
                "id": f"popular_{stock['symbol']}",
                "symbol": stock["symbol"],
                "name": stock["name"],
                "type": "stock",
                "price": stock.get("price", 0),
                "change": stock.get("change", 0),
                "change_percent": stock.get("change_percent", 0),
                "isPositive": stock.get("change", 0) >= 0,
                "volume": stock.get("volume", 0),
                "market_cap": stock.get("market_cap"),
                "timestamp": stock.get("timestamp")
            })
    
    return {
        "followed_stocks": dashboard_stocks,
        "user_has_followed_stocks": len(followed_stocks) > 0,
        "last_updated": datetime.now().isoformat()
    }

@portfolio_router.get("/dashboard/data/public")
async def get_public_dashboard_data(
    db: Session = Depends(get_db)
):
    """获取公开仪表板数据（用于测试，无需认证）"""
    polygon_service = await get_polygon_rest_service()
    websocket_service = await get_polygon_service()
    
    # Get popular stocks for demo
    popular_stocks = await polygon_service.get_top_stocks(5)
    
    dashboard_stocks = []
    for stock in popular_stocks:
        # Add real-time data if available
        latest_data = websocket_service.get_latest_data(stock["symbol"])
        if latest_data:
            stock.update(latest_data)
        
        dashboard_stocks.append({
            "id": f"demo_{stock['symbol']}",
            "symbol": stock["symbol"],
            "name": stock["name"],
            "type": "stock",
            "price": stock.get("price", 0),
            "change": stock.get("change", 0),
            "change_percent": stock.get("change_percent", 0),
            "isPositive": stock.get("change", 0) >= 0,
            "volume": stock.get("volume", 0),
            "market_cap": stock.get("market_cap"),
            "timestamp": stock.get("timestamp")
        })
    
    return {
        "followed_stocks": dashboard_stocks,
        "user_has_followed_stocks": False,  # Demo mode
        "last_updated": datetime.now().isoformat()
    }

@portfolio_router.get("/analytics/public")
async def get_public_portfolio_analytics(
    db: Session = Depends(get_db)
):
    """获取公开投资组合分析数据（用于测试，无需认证）"""
    polygon_service = await get_polygon_rest_service()
    websocket_service = await get_polygon_service()
    
    # Get popular stocks for demo analytics
    popular_stocks = await polygon_service.get_top_stocks(10)
    
    # Enhanced stocks with real-time data
    enhanced_stocks = []
    for stock in popular_stocks:
        latest_data = websocket_service.get_latest_data(stock["symbol"])
        if latest_data:
            stock.update(latest_data)
        enhanced_stocks.append(stock)
    
    # Calculate analytics
    total_stocks = len(enhanced_stocks)
    gainers = len([s for s in enhanced_stocks if s.get("change", 0) >= 0])
    losers = total_stocks - gainers
    
    # Calculate average change
    avg_change = sum(s.get("change_percent", 0) for s in enhanced_stocks) / max(total_stocks, 1)
    
    # Sector breakdown (simplified classification)
    sector_map = {
        'AAPL': 'Technology', 'GOOGL': 'Technology', 'MSFT': 'Technology',
        'TSLA': 'Automotive', 'NVDA': 'Technology', 'AMD': 'Technology', 
        'META': 'Technology', 'AMZN': 'E-commerce', 'NFLX': 'Entertainment',
        'CRM': 'Technology', 'ORCL': 'Technology', 'INTC': 'Technology'
    }
    
    sector_breakdown = {}
    for stock in enhanced_stocks:
        sector = sector_map.get(stock["symbol"], "Other")
        if sector not in sector_breakdown:
            sector_breakdown[sector] = {"count": 0, "total_change": 0, "stocks": []}
        
        sector_breakdown[sector]["count"] += 1
        sector_breakdown[sector]["total_change"] += stock.get("change_percent", 0)
        sector_breakdown[sector]["stocks"].append(stock["symbol"])
    
    # Calculate sector averages
    for sector in sector_breakdown:
        count = sector_breakdown[sector]["count"]
        sector_breakdown[sector]["avg_change"] = sector_breakdown[sector]["total_change"] / count
    
    # Find top and worst performers
    sorted_stocks = sorted(enhanced_stocks, key=lambda x: x.get("change_percent", 0), reverse=True)
    top_performer = sorted_stocks[0] if sorted_stocks else None
    worst_performer = sorted_stocks[-1] if sorted_stocks else None
    
    # Calculate risk level based on volatility
    volatilities = [abs(s.get("change_percent", 0)) for s in enhanced_stocks]
    avg_volatility = sum(volatilities) / max(len(volatilities), 1)
    
    risk_level = "High" if avg_volatility > 3 else "Medium" if avg_volatility > 1.5 else "Low"
    
    # Calculate diversification score
    sector_count = len(sector_breakdown)
    diversification_score = min(100, (sector_count / 5) * 100)
    
    # Generate recommendations
    recommendations = []
    if sector_count <= 2:
        recommendations.append("Consider diversifying across more sectors to reduce risk")
    if losers > gainers:
        recommendations.append("More stocks are declining than gaining - review market conditions")
    if avg_volatility > 4:
        recommendations.append("High volatility detected - consider risk management strategies")
    if diversification_score < 60:
        recommendations.append("Low diversification score - add stocks from different industries")
    
    return {
        "summary": {
            "total_stocks": total_stocks,
            "gainers": gainers,
            "losers": losers,
            "avg_change": round(avg_change, 2),
            "risk_level": risk_level,
            "diversification_score": round(diversification_score, 1),
            "total_value": sum(s.get("price", 0) * 100 for s in enhanced_stocks)  # Assume 100 shares each
        },
        "sector_breakdown": sector_breakdown,
        "top_performer": top_performer,
        "worst_performer": worst_performer,
        "recommendations": recommendations,
        "stocks": enhanced_stocks,
        "last_updated": datetime.now().isoformat()
    }

@portfolio_router.get("/followed/realtime/public")
async def get_public_followed_realtime(
    db: Session = Depends(get_db)
):
    """获取公开的实时跟踪股票数据（用于测试）"""
    polygon_service = await get_polygon_rest_service()
    websocket_service = await get_polygon_service()
    
    # Use popular stocks as demo followed stocks
    popular_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    enhanced_items = []
    
    for symbol in popular_symbols:
        stock_data = await polygon_service.get_stock_details(symbol)
        
        # Add real-time data if available
        latest_data = websocket_service.get_latest_data(symbol)
        if latest_data:
            stock_data.update(latest_data)
        
        enhanced_item = {
            "id": f"demo_{symbol}",
            "symbol": symbol,
            "asset_type": "stock",
            "name": stock_data.get("name", symbol),
            "notes": None,
            "followed_at": datetime.now().isoformat(),
            "market_data": stock_data,
            "price": stock_data.get("price", 0),
            "change": stock_data.get("change", 0),
            "change_percent": stock_data.get("change_percent", 0),
            "volume": stock_data.get("volume", 0),
            "isPositive": stock_data.get("change", 0) >= 0,
            "isRealtime": bool(latest_data)
        }
        enhanced_items.append(enhanced_item)
    
    return {
        "followed_items": enhanced_items,
        "count": len(enhanced_items),
        "last_updated": datetime.now().isoformat()
    }

