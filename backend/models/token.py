# models/token.py

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class UserToken(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
