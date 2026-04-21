from dataclasses import dataclass


@dataclass
class AgentContext:
    user_id: str
    conversation_id: str
    name: str
    wallet_balance: float
    long_term_preferences: str
