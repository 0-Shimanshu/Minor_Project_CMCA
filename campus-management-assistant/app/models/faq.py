from datetime import datetime
from ..extensions import db


class FAQ(db.Model):
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)

    category = db.Column(db.String, nullable=False)
    target_department = db.Column(db.String)

    status = db.Column(db.String, nullable=False)

    asked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    answered_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)

    # Relationships
    asker = db.relationship('User', foreign_keys=[asked_by], backref=db.backref('asked_faqs', lazy=True))
    answerer = db.relationship('User', foreign_keys=[answered_by], backref=db.backref('answered_faqs', lazy=True))
