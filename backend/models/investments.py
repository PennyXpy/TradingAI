from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class Investment(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    symbol: str
    asset_type: str  # "stock" 或 "crypto"
    
    # 交易详情
    quantity: float
    price_per_unit: float
    transaction_date: datetime
    transaction_type: str  # "buy" 或 "sell"
    source: str = "manual"  # "manual" 或 "robinhood" 或其他API来源
    
    # 附加字段
    fees: Optional[float] = 0.0
    notes: Optional[str] = None
    
    # 时间戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))