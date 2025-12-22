from ..extensions import db


class NoticeCategory(db.Model):
    __tablename__ = 'notice_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
