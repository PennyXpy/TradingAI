from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class UserToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    access_token: str  # 仅存 access token
    created_at: datetime = Field(default_factory=datetime.utcnow)
