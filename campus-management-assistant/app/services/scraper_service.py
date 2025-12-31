from typing import List, Tuple, Optional
from urllib.parse import urljoin
import os
import hashlib
import time
import requests
from bs4 import BeautifulSoup
from ..extensions import db
from ..models.scraper import ScrapedWebsite, ScrapeLog
from ..models.chatbot_document import ChatbotDocument
from ..models.logs import SystemLog
from .pdf_service import extract_pdf_text

SCRAPED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'scraped'))


def _hash_text(text: str) -> str:
    normalized = " ".join(text.split()).strip().lower()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def add_website(url: str, name: Optional[str] = None) -> Tuple[bool, str]:
    try:
        if ScrapedWebsite.query.filter_by(url=url).first():
            return False, 'URL already added'
        site = ScrapedWebsite(url=url, name=(name or None), enabled=True)
        db.session.add(site)
        db.session.commit()
        return True, 'Added'
    except Exception as e:
        db.session.add(SystemLog(module='scraper', message=f'add error: {e}'))
        db.session.commit()
        return False, 'Error'


def list_websites() -> List[ScrapedWebsite]:
    return ScrapedWebsite.query.order_by(ScrapedWebsite.added_at.desc()).all()


def list_logs(limit: int = 50) -> List[ScrapeLog]:
    return ScrapeLog.query.order_by(ScrapeLog.scraped_at.desc()).limit(limit).all()


def get_website(website_id: int) -> ScrapedWebsite | None:
    try:
        return db.session.get(ScrapedWebsite, website_id)
    except Exception:
        return None


def _extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text(separator=' ')
    normalized = " ".join(text.split()).strip()
    return normalized


def _find_pdf_links(base_url: str, html: str) -> List[str]:
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().endswith('.pdf'):
            links.append(urljoin(base_url, href))
    return links


def _save_pdf(url: str, website_id: int) -> str:
    os.makedirs(SCRAPED_DIR, exist_ok=True)
    fname = f"site{website_id}_{int(time.time())}_{hashlib.sha256(url.encode()).hexdigest()[:8]}.pdf"
    path = os.path.join(SCRAPED_DIR, fname)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    with open(path, 'wb') as f:
        f.write(r.content)
    return path


def scrape_website(website: ScrapedWebsite) -> Tuple[bool, str]:
    status = 'success'
    text_len = 0
    pdf_count = 0
    try:
        r = requests.get(website.url, timeout=15)
        r.raise_for_status()
        html = r.text
        # Extract text
        visible = _extract_visible_text(html)
        if visible:
            text_len = len(visible)
            h = _hash_text(visible)
            if not ChatbotDocument.query.filter_by(content_hash=h).first():
                db.session.add(ChatbotDocument(
                    source_type='scrape_text',
                    source_id=website.id,
                    content=visible,
                    content_hash=h,
                    visibility='public',
                ))
                db.session.commit()
        # PDFs
        pdf_links = _find_pdf_links(website.url, html)
        for link in pdf_links:
            try:
                path = _save_pdf(link, website.id)
                text = extract_pdf_text(path)
                if text:
                    h = _hash_text(text)
                    if not ChatbotDocument.query.filter_by(content_hash=h).first():
                        db.session.add(ChatbotDocument(
                            source_type='scrape_pdf',
                            source_id=website.id,
                            content=text,
                            content_hash=h,
                            visibility='public',
                        ))
                        db.session.commit()
                pdf_count += 1
            except Exception as e:
                db.session.add(SystemLog(module='scraper', message=f'pdf download/extract error: {e}'))
                db.session.commit()
        status = 'success'
    except Exception as e:
        status = 'error'
        db.session.add(SystemLog(module='scraper', message=f'scrape error: {e}'))
        db.session.commit()
    finally:
        try:
            db.session.add(ScrapeLog(
                website_id=website.id,
                status=status,
                extracted_text_length=text_len,
                pdf_links_found=pdf_count,
            ))
            db.session.commit()
        except Exception:
            pass
    return (status == 'success'), status


def scrape_all() -> Tuple[int, int]:
    ok = 0
    total = 0
    for site in list_websites():
        total += 1
        if getattr(site, 'enabled', True):
            s, _ = scrape_website(site)
        else:
            s = False
        ok += 1 if s else 0
    return ok, total
