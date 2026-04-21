from datetime import date, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class DestinationBooking(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    booking_reference: str = Field(
        default_factory=lambda: f"BK-{uuid4().hex[:8].upper()}",
        index=True,
        unique=True,
    )
    user_id: str = Field(index=True)
    user_name: str = Field(default="user")
    destination: str
    package_name: str = Field(default="standard")
    travel_date: date = Field(default_factory=date.today)
    travelers: int = Field(default=1, ge=1)
    total_cost: float = Field(ge=0.0)
    contact_email: str = Field(default="not-provided@example.com")
    status: str = Field(default="confirmed")
    created_at: datetime = Field(default_factory=datetime.utcnow)