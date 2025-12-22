from datetime import datetime
from ..extensions import db


class ChatbotDocument(db.Model):
    __tablename__ = 'chatbot_documents'

    id = db.Column(db.Integer, primary_key=True)

    source_type = db.Column(db.String, nullable=False)
    source_id = db.Column(db.Integer)

    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String, unique=True, nullable=False)

    visibility = db.Column(db.String, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
