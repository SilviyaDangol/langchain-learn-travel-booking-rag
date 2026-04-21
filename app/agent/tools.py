import re
from datetime import datetime

from langchain.tools import ToolRuntime, tool
from sqlmodel import Session, select

from app.agent.context import AgentContext
from app.agent import memory
from app.db.db import engine
from app.db.models.bookings import DestinationBooking
from app.db.models.user_metadata import UserPreferenceMemory, UserProfile
from app.config import Config
from app.rag_helpers.vectorstore import destination_vector_store, hybrid_search, vector_store


def _extract_prices(content: str) -> list[float]:
    patterns = [
        r"\$\s?(\d+(?:,\d{3})*(?:\.\d{1,2})?)",
        r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s?(?:usd|dollars?)\b",
        r"(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s?(?:per person|pp)\b",
    ]
    prices: list[float] = []
    for pattern in patterns:
        for match in re.findall(pattern, content, flags=re.IGNORECASE):
            normalized = match.replace(",", "")
            prices.append(float(normalized))
    return prices


def _profile_by_user_id(session: Session, user_id: str) -> UserProfile | None:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    return session.exec(stmt).first()


def _preferences_by_user_id(
    session: Session, user_id: str
) -> UserPreferenceMemory | None:
    stmt = select(UserPreferenceMemory).where(UserPreferenceMemory.user_id == user_id)
    return session.exec(stmt).first()


def get_user_preferences(user_id: str) -> str:
    store_preferences = memory.load_user_preferences(user_id)
    if store_preferences is not None:
        return store_preferences

    with Session(engine) as session:
        preference_row = _preferences_by_user_id(session, user_id)
    if preference_row is None or not preference_row.preferences.strip():
        return "No saved preferences"
    return preference_row.preferences


def _runtime_user_id(runtime: ToolRuntime[AgentContext]) -> str:
    return runtime.context.user_id


@tool(
    "retrieve_context",
    description="Retrieves information related to user query from the document they provided",
    response_format="content_and_artifact",
)
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    try:
        retrieved_docs = hybrid_search(query=query, k=2)
    except Exception:
        # Fallback keeps retrieval available even if sparse encoder/model is unavailable.
        retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}") for doc in retrieved_docs
    )
    return serialized, retrieved_docs


@tool(
    "upsert_user_profile",
    description=(
        "Create or update a user profile with name and wallet balance for the runtime user. "
        "Call this before budget-aware destination recommendations."
    ),
)
def upsert_user_profile(
    name: str, wallet_balance: float, runtime: ToolRuntime[AgentContext]
) -> str:
    """Create or update a user's budget profile."""
    user_id = _runtime_user_id(runtime)
    with Session(engine) as session:
        profile = _profile_by_user_id(session, user_id)
        if profile is None:
            profile = UserProfile(
                user_id=user_id,
                name=name,
                wallet_balance=max(wallet_balance, 0.0),
            )
            session.add(profile)
            action = "created"
        else:
            profile.name = name
            profile.wallet_balance = max(wallet_balance, 0.0)
            profile.updated_at = datetime.now()
            action = "updated"
        session.commit()
    return (
        f"User profile {action} for user_id={user_id}. "
        f"Wallet balance set to ${max(wallet_balance, 0.0):.2f}."
    )


@tool(
    "remember_user_preferences",
    description=(
        "Save non-sensitive user preferences that should persist across conversations "
        "(e.g., food, budget style, travel pace)."
    ),
)
def remember_user_preferences(
    preferences: str, runtime: ToolRuntime[AgentContext]
) -> str:
    """Create or update durable user preference memory."""
    user_id = _runtime_user_id(runtime)
    cleaned_preferences = preferences.strip()
    if not cleaned_preferences:
        return "No preferences provided to remember."
    saved_in_store = memory.save_user_preferences(user_id, cleaned_preferences)

    # with Session(engine) as session:
    #     preference_row = _preferences_by_user_id(session, user_id)
    #     if preference_row is None:
    #         preference_row = UserPreferenceMemory(
    #             user_id=user_id, preferences=cleaned_preferences
    #         )
    #         session.add(preference_row)
    #         action = "created"
    #     else:
    #         preference_row.preferences = cleaned_preferences
    #         preference_row.updated_at = datetime.now()
    #         action = "updated"
    #     session.commit()
    if saved_in_store:
        return f"Preference memory {action} for user_id={user_id} (MemoryStore + SQL sync)."
    # return f"Preference memory {action} for user_id={user_id} (SQL only fallback)."


@tool(
    "view_user_preferences",
    description="Read saved long-term user preferences for the runtime user.",
)
def view_user_preferences(runtime: ToolRuntime[AgentContext]) -> str:
    """Return long-term preference memory for user."""
    user_id = _runtime_user_id(runtime)
    preferences = get_user_preferences(user_id)
    return f"Saved preferences for {user_id}: {preferences}"


@tool(
    "search_destination",
    description=(
        "Search holiday destinations and offerings from the catalog, then compare options with "
        "the user's wallet balance from profile."
    ),
    response_format="content_and_artifact",
)
def search_destination(query: str, runtime: ToolRuntime[AgentContext]):
    """Search catalog and return options that match the user's budget."""
    user_id = _runtime_user_id(runtime)
    with Session(engine) as session:
        profile = _profile_by_user_id(session, user_id)

    if profile is None:
        message = (
            f"No user profile found for user_id={user_id}. "
            "Create one first with upsert_user_profile(name, wallet_balance)."
        )
        return message, []

    try:
        retrieved_docs = hybrid_search(
            query=query, k=8, namespace=Config.PINECONE_DESTINATIONS_NAMESPACE
        )
    except Exception:
        # Fallback keeps destination search available if hybrid query fails.
        retrieved_docs = destination_vector_store.similarity_search(query, k=8)

    affordable_docs = []
    rendered_chunks: list[str] = []
    for doc in retrieved_docs:
        prices = _extract_prices(doc.page_content)
        min_price = min(prices) if prices else None
        is_affordable = min_price is None or min_price <= profile.wallet_balance
        if is_affordable:
            affordable_docs.append(doc)
        budget_label = (
            "price not specified"
            if min_price is None
            else f"estimated price ${min_price:.2f} ({'within' if is_affordable else 'over'} budget)"
        )
        rendered_chunks.append(
            f"Source: {doc.metadata}\nBudget check: {budget_label}\nContent: {doc.page_content}"
        )

    selected_docs = affordable_docs if affordable_docs else retrieved_docs[:3]
    serialized = (
        f"User budget: ${profile.wallet_balance:.2f}\n"
        + "\n\n".join(rendered_chunks)
    )
    return serialized, selected_docs


@tool(
    "book_destination",
    description=(
        "Create a confirmed booking after collecting required fields: "
        "destination, total_cost, confirmed."
    ),
)
def book_destination(
    destination: str,
    total_cost: float,
    confirmed: bool,
    runtime: ToolRuntime[AgentContext],
) -> str:
    """Persist a booking and deduct cost from wallet after explicit confirmation."""
    user_id = _runtime_user_id(runtime)
    required_fields = {
        "destination": destination,
        "total_cost": total_cost,
    }
    missing = [name for name, value in required_fields.items() if value in (None, "", 0)]
    if missing:
        return f"Missing required booking details: {', '.join(missing)}."
    if not confirmed:
        return "Booking not created. Ask user for explicit confirmation and retry with confirmed=True."

    with Session(engine) as session:
        profile = _profile_by_user_id(session, user_id)
        if profile is None:
            return (
                f"No user profile found for user_id={user_id}. "
                "Create one first with upsert_user_profile."
            )
        if total_cost > profile.wallet_balance:
            return (
                f"Insufficient wallet balance. Total cost ${total_cost:.2f} exceeds "
                f"available ${profile.wallet_balance:.2f}."
            )

        booking = DestinationBooking(
            user_id=user_id,
            user_name=profile.name,
            destination=destination,
            package_name="standard",
            travelers=1,
            total_cost=total_cost,
            contact_email="not-provided@example.com",
        )
        profile.wallet_balance -= total_cost
        profile.updated_at = datetime.now()

        session.add(booking)
        session.add(profile)
        session.commit()
        session.refresh(booking)
        remaining = profile.wallet_balance

    return (
        f"Booking confirmed. Reference: {booking.booking_reference}, destination: {destination}, "
        f"total cost: ${total_cost:.2f}. Remaining wallet balance: ${remaining:.2f}."
    )