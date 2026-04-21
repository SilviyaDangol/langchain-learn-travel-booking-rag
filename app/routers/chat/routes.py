from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from starlette.responses import JSONResponse

from app.agent.agent import agent
from app.agent.context import AgentContext
from app.agent.tools import get_user_preferences
from app.db.db import DBSessionDep
from app.db.models.chat import ConversationSession
from app.db.models.user_metadata import UserProfile
from app.db.schemas.chat import ChatRequest, ChatSessionCreateRequest

router: APIRouter = APIRouter(tags=["Part 2 CHAT"])


def _conversation_for_user(
    db: DBSessionDep, conversation_id: str, user_id: str
) -> ConversationSession | None:
    query = select(ConversationSession).where(
        ConversationSession.conversation_id == conversation_id
    )
    conversation = db.exec(query).first()
    if conversation is None or conversation.user_id != user_id:
        return None
    return conversation


def _profile_for_user(db: DBSessionDep, user_id: str) -> UserProfile | None:
    query = select(UserProfile).where(UserProfile.user_id == user_id)
    return db.exec(query).first()


@router.post("/chat/new")
async def create_chat_session(
    db: DBSessionDep, payload: ChatSessionCreateRequest
) -> JSONResponse:
    conversation = ConversationSession(user_id=payload.user_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Conversation created",
            "conversation_id": conversation.conversation_id,
            "user_id": payload.user_id,
        },
    )


@router.post("/chat/{conversation_id}")
async def chat_with_agent(
    db: DBSessionDep, conversation_id: UUID, message: ChatRequest
) -> JSONResponse:
    conversation_key = str(conversation_id)
    conversation = _conversation_for_user(db, conversation_key, message.user_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found for this user_id",
        )

    profile = _profile_for_user(db, message.user_id)
    if message.name is not None or message.wallet_balance is not None:
        if profile is None:
            profile = UserProfile(
                user_id=message.user_id,
                name=message.name or "user",
                wallet_balance=max(message.wallet_balance or 0.0, 0.0),
            )
            db.add(profile)
        else:
            if message.name is not None:
                profile.name = message.name
            if message.wallet_balance is not None:
                profile.wallet_balance = max(message.wallet_balance, 0.0)
            profile.updated_at = datetime.now()
        db.commit()

    profile_name = profile.name if profile else message.name or "user"
    profile_wallet = (
        profile.wallet_balance
        if profile is not None
        else max(message.wallet_balance or 0.0, 0.0)
    )
    long_term_preferences = get_user_preferences(message.user_id)
    config = {"configurable": {"thread_id": conversation_key}}
    context = AgentContext(
        user_id=message.user_id,
        conversation_id=conversation_key,
        name=profile_name,
        wallet_balance=profile_wallet,
        long_term_preferences=long_term_preferences,
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": message.query}]},
        config,
        context=context,
    )
    conversation.updated_at = datetime.now()
    db.add(conversation)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "conversation_id": conversation_key,
            "user_id": message.user_id,
            "response": result["messages"][-1].content,
        },
    )


@router.post("/ask/")
async def chat_with_default_flow(
    db: DBSessionDep, message: ChatRequest
) -> JSONResponse:
    conversation = ConversationSession(user_id=message.user_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return await chat_with_agent(db, UUID(conversation.conversation_id), message)
