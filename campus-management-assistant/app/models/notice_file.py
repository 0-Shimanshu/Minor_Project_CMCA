from datetime import datetime
from ..extensions import db


class NoticeFile(db.Model):
    __tablename__ = 'notice_files'

    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)

    file_name = db.Column(db.String, nullable=False)
    file_path = db.Column(db.String, nullable=False)
    file_type = db.Column(db.String)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    notice = db.relationship('Notice', backref=db.backref('files', lazy=True, cascade='all, delete-orphan'))
