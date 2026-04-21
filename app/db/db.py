from typing import Annotated
from fastapi import Depends
from langgraph.store.postgres import PostgresStore
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from app.config import Config
from app.db.models.chat import ConversationSession  # noqa: F401
from app.db.models.bookings import DestinationBooking  # noqa: F401
from app.db.models.user_metadata import FileSession, UserPreferenceMemory, UserProfile  # noqa: F401

# store = PostgresStore.from_conn_string(Config.DB_URL)

engine = create_engine(Config.DB_URL,echo=True)
def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    # store.setup()

def get_session():
    with Session(engine) as session:
        yield session

DBSessionDep = Annotated[Session, Depends(get_session)]