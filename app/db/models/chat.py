from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class ConversationSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        index=True,
        unique=True,
    )
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
