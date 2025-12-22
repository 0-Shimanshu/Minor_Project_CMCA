from datetime import datetime
from ..extensions import db


class EmailLog(db.Model):
    __tablename__ = 'email_logs'

    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'))
    sent_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    subject = db.Column(db.String)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)


class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String)
    message = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
