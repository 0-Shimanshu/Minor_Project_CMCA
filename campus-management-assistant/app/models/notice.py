from datetime import datetime
from ..extensions import db


class Notice(db.Model):
    __tablename__ = 'notices'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    summary = db.Column(db.String)
    content = db.Column(db.Text, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('notice_categories.id'), nullable=False)

    visibility = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)

    target_department = db.Column(db.String)
    target_year = db.Column(db.Integer)

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    category = db.relationship('NoticeCategory', backref=db.backref('notices', lazy=True))
    author = db.relationship('User', backref=db.backref('created_notices', lazy=True))
