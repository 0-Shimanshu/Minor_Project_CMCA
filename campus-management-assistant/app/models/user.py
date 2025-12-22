from datetime import datetime
from flask_login import UserMixin
from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

    role = db.Column(db.String, nullable=False)

    enrollment_no = db.Column(db.String, unique=True)
    department = db.Column(db.String)
    year = db.Column(db.Integer)

    sign_name = db.Column(db.String)
    email = db.Column(db.String)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
