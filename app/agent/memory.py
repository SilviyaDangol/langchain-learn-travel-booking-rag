from datetime import datetime
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from app.config import Config

_store_cm = None
_checkpointer_cm = None
store = None
checkpointer = None
PREFERENCES_KEY = "preferences"


def init_memory() -> None:
    global _store_cm, _checkpointer_cm, store, checkpointer
    if store is not None and checkpointer is not None:
        return

    _store_cm = PostgresStore.from_conn_string(Config.DB_URL)
    _checkpointer_cm = PostgresSaver.from_conn_string(Config.DB_URL)
    store = _store_cm.__enter__()
    checkpointer = _checkpointer_cm.__enter__()
    store.setup()
    checkpointer.setup()


def close_memory() -> None:
    global _store_cm, _checkpointer_cm, store, checkpointer
    if _checkpointer_cm is not None:
        _checkpointer_cm.__exit__(None, None, None)
    if _store_cm is not None:
        _store_cm.__exit__(None, None, None)
    _store_cm = None
    _checkpointer_cm = None
    store = None
    checkpointer = None


def _preferences_namespace(user_id: str) -> tuple[str, str, str]:
    return ("users", user_id, "preferences")


def save_user_preferences(user_id: str, preferences: str) -> bool:
    """Persist user preferences in LangGraph MemoryStore."""
    if store is None:
        init_memory()
    payload = {
        "preferences": preferences,
        "updated_at": datetime.now().isoformat(),
    }
    try:
        store.put(_preferences_namespace(user_id), PREFERENCES_KEY, payload)
        return True
    except Exception:
        return False


def load_user_preferences(user_id: str) -> str | None:
    """Fetch user preferences from LangGraph MemoryStore."""
    if store is None:
        init_memory()
    try:
        item = store.get(_preferences_namespace(user_id), PREFERENCES_KEY)
    except Exception:
        return None
    if item is None:
        return None

    value: dict[str, Any] | None = None
    if hasattr(item, "value"):
        value = item.value
    elif isinstance(item, dict):
        value = item
    if not isinstance(value, dict):
        return None

    preferences = value.get("preferences")
    return preferences if isinstance(preferences, str) and preferences.strip() else None
