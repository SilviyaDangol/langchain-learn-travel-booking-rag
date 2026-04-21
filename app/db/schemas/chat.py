from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str
    user_id: str = Field(..., description="Stable user identifier")
    name: str | None = Field(default=None, description="User display name")
    wallet_balance: float | None = Field(
        default=None,
        description="Optional wallet balance to refresh profile before recommendation",
    )


class ChatSessionCreateRequest(BaseModel):
    user_id: str = Field(..., description="Stable user identifier")
