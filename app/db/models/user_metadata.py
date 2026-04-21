from uuid import UUID

from sqlmodel import SQLModel, Field
from datetime import datetime

class FileSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    file_id: str = Field(index=True)
    filename: str
    split_type:str
    created_at: datetime = Field(default_factory= lambda: datetime.now())


class UserProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)
    name: str
    wallet_balance: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())


class UserPreferenceMemory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)
    preferences: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())