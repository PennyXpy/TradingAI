from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from models.followed import Followed
from models.investments import Investment
from models.users import User
from service.auth import get_current_user
from data import engine

# 请求和响应模型
class FollowedCreate(BaseModel):
    symbol: str
    asset_type: str
    name: Optional[str] = None
    notes: Optional[str] = None

class InvestmentCreate(BaseModel):
    symbol: str
    asset_type: str
    quantity: float
    price_per_unit: float
    transaction_date: datetime
    transaction_type: str  # "buy" 或 "sell"
    fees: Optional[float] = 0.0
    notes: Optional[str] = None

# 创建路由器
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

# 投资记录API端点
@portfolio_router.get("/investments")
async def get_investments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    asset_type: Optional[str] = None,
    symbol: Optional[str] = None
):
    """获取当前用户的所有投资记录"""
    query = select(Investment).where(Investment.user_id == user.id)
    
    if asset_type:
        query = query.where(Investment.asset_type == asset_type)
    
    if symbol:
        query = query.where(Investment.symbol == symbol)
    
    investments = db.exec(query).all()
    return investments

@portfolio_router.post("/investments")
async def add_investment(
    investment: InvestmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加新的投资交易记录"""
    # 创建新投资记录
    new_investment = Investment(
        user_id=user.id,
        symbol=investment.symbol,
        asset_type=investment.asset_type,
        quantity=investment.quantity,
        price_per_unit=investment.price_per_unit,
        transaction_date=investment.transaction_date,
        transaction_type=investment.transaction_type,
        fees=investment.fees,
        notes=investment.notes,
        source="manual"
    )
    
    db.add(new_investment)
    db.commit()
    db.refresh(new_investment)
    
    return new_investment

@portfolio_router.delete("/investments/{investment_id}")
async def delete_investment(
    investment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除投资交易记录"""
    # 查找投资记录
    investment = db.exec(
        select(Investment).where(
            Investment.id == investment_id,
            Investment.user_id == user.id
        )
    ).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投资记录未找到"
        )
    
    # 删除投资记录
    db.delete(investment)
    db.commit()
    
    return {"message": "投资记录已删除"}