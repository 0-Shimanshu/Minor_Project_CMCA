from ..extensions import db
from ..models.logs import SystemLog, EmailLog


def get_system_logs(limit: int = 200):
	try:
		return SystemLog.query.order_by(SystemLog.created_at.desc()).limit(limit).all()
	except Exception:
		return []


def get_email_logs(limit: int = 200):
	try:
		return EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(limit).all()
	except Exception:
		return []
