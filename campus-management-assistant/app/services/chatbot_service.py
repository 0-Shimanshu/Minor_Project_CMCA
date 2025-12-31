from typing import Tuple, Dict
from .chatbot_static_knowledge import answer_for


def ask_gemini(user_query: str, role: str) -> Tuple[bool, str]:
    """Deterministic knowledge-based response without external APIs."""
    ok, ans = answer_for(user_query, role)
    return ok, ans


def chatbot_health() -> Dict[str, object]:
    return {
        'ok': True,
        'mode': 'static',
        'ready': True,
    }
