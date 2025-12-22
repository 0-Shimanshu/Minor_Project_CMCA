import os
from typing import List, Tuple, Dict
from ..extensions import db
from ..models.chatbot_document import ChatbotDocument
from ..models.logs import SystemLog

# Gemini SDK: use google.genai only (no deprecated fallback)
USE_NEW_SDK = True
genai_new = None
try:
    import google.genai as genai_new  # type: ignore
except Exception:
    genai_new = None

def _normalize_env_value(val: str):
    if val is None:
        return None
    v = val.strip()
    if not v:
        return None
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1].strip()
    if v.upper() in {'YOUR_API_KEY', 'PLACEHOLDER', 'NONE'}:
        return None
    return v

# Configure once (safe if called multiple times)
API_KEY = _normalize_env_value(os.getenv('GEMINI_API_KEY'))
_configured_client = None
if API_KEY and genai_new is not None:
    try:
        _configured_client = genai_new.Client(api_key=API_KEY)
    except Exception:
        _configured_client = None

# Prefer env-provided model; fallback to widely available free-tier
_env_model = _normalize_env_value(os.getenv('GEMINI_MODEL'))
MODEL_NAME = _env_model or 'gemini-1.5-flash'

MAX_CONTEXT_CHARS = 15000  # keep payload reasonable


def _fetch_allowed_docs(role: str) -> List[ChatbotDocument]:
    if role == 'student':
        return ChatbotDocument.query.filter(ChatbotDocument.visibility.in_(['public', 'student']))\
            .order_by(ChatbotDocument.created_at.desc()).all()
    # guest or default
    return ChatbotDocument.query.filter_by(visibility='public').order_by(ChatbotDocument.created_at.desc()).all()


def _build_context(documents: List[ChatbotDocument]) -> str:
    parts: List[str] = []
    total = 0
    for d in documents:
        # Strictly include only content; avoid leaking metadata
        chunk = f"{d.content}\n\n"
        if total + len(chunk) > MAX_CONTEXT_CHARS:
            break
        parts.append(chunk)
        total += len(chunk)
    return "".join(parts)


def ask_gemini(user_query: str, role: str) -> Tuple[bool, str]:
    try:
        docs = _fetch_allowed_docs(role)
        context = _build_context(docs)
        if not context:
            return False, "I don't have enough information to answer that."
        if not API_KEY:
            return False, "Model not configured. Please set GEMINI_API_KEY."
        instruction = (
            "Answer ONLY from the provided context. "
            "If the answer is not in the context, say: I don't have enough information. "
            "Respond in the same language as the user's question. "
            "Do not use any external knowledge."
        )
        prompt = (
            f"System Instruction:\n{instruction}\n\n"
            f"Context:\n{context}\n"
            f"User Question:\n{user_query}"
        )
        if _configured_client is None or genai_new is None:
            return False, "Model SDK not available. Please install google-genai and set GEMINI_API_KEY."
        # Use google.genai responses API; send contents with role/parts per SDK contract
        resp = _configured_client.responses.generate(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        text = getattr(resp, 'output_text', None)
        if not text:
            try:
                cand = resp.candidates[0].content.parts[0].text
                text = cand
            except Exception:
                text = None
        if not text:
            return False, "I don't have enough information to answer that."
        return True, text.strip()
    except Exception as e:
        msg = str(e)
        try:
            log = SystemLog()
            log.module = 'chatbot'
            log.message = f'gemini error: {msg}'
            db.session.add(log)
            db.session.commit()
        except Exception:
            pass
        if ('API_KEY_INVALID' in msg) or ('API key not valid' in msg):
            return False, 'AI API key is invalid or restricted. Update GEMINI_API_KEY or key restrictions.'
        if ('is not found for API version' in msg) or ('not supported for generateContent' in msg):
            return False, 'Configured model is not available for this SDK/version. Set GEMINI_MODEL to a supported model (e.g., gemini-1.5-flash) or update google-genai.'
        return False, "Sorry, an error occurred while generating the answer."


def chatbot_health() -> Dict[str, object]:
    key_present = bool(API_KEY)
    sdk_name = 'google.genai'
    sdk_configure_available = True
    model_class_available = True
    client_ready = _configured_client is not None and genai_new is not None
    ready = key_present and client_ready
    return {
        'ok': True,
        'sdk': sdk_name,
        'key_present': key_present,
        'model': MODEL_NAME,
        'sdk_configure_available': sdk_configure_available,
        'model_class_available': model_class_available,
        'ready': ready,
    }
