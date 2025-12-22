from typing import List, Dict, Any
from ..extensions import db
from ..models.logs import SystemLog, EmailLog


def list_system_logs(limit: int = 50) -> List[SystemLog]:
    return SystemLog.query.order_by(SystemLog.created_at.desc()).limit(limit).all()


def list_email_logs(limit: int = 50) -> List[EmailLog]:
    return EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(limit).all()


def log_event(module: str, action: str, details: Dict[str, Any] | None = None):
    """Create a structured system log message.

    Formats as: "action key=value key=value" for clarity without schema changes.
    """
    parts = [action]
    if details:
        for k, v in details.items():
            if v is None:
                continue
            parts.append(f"{k}={v}")
    msg = " ".join(parts)
    db.session.add(SystemLog(module=module, message=msg))
    db.session.commit()
