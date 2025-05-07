from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class Followed(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    symbol: str  # 股票代码或加密货币代码
    asset_type: str  # "stock" 或 "crypto"
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 可选元数据字段
    name: Optional[str] = None  # 公司/加密货币名称
    notes: Optional[str] = None  # 用户笔记
    
    # 添加唯一约束，确保用户不能重复关注同一资产
    class Config:
        table_name = "followed"