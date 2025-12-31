from datetime import datetime
from ..extensions import db


class ScrapedWebsite(db.Model):
    __tablename__ = 'scraped_websites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    url = db.Column(db.String, unique=True, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    enabled = db.Column(db.Boolean, default=True)


class ScrapeLog(db.Model):
    __tablename__ = 'scrape_logs'

    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('scraped_websites.id'))

    status = db.Column(db.String)
    extracted_text_length = db.Column(db.Integer)
    pdf_links_found = db.Column(db.Integer)

    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)

    website = db.relationship('ScrapedWebsite', backref=db.backref('logs', lazy=True, cascade='all, delete-orphan'))
