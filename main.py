from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent.memory import close_memory, init_memory
from app.db.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI): # noqa      # Ignore Shadowed name "app"
    create_db_and_tables()
    init_memory()
    yield
    close_memory()


app = FastAPI(lifespan=lifespan)
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:3000",
]

from app.routers.ingest.ingest import router as ingest_router
from app.routers.chat.routes import router as chat_router
app.include_router(ingest_router)
app.include_router(chat_router)
