from typing import Optional
from ..extensions import db
from ..models.logs import SystemLog
import pdfplumber


def extract_pdf_text(file_path: str) -> Optional[str]:
    try:
        with pdfplumber.open(file_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                text_parts.append(text)
            raw = "\n".join(text_parts)
            normalized = " ".join(raw.split()).strip().lower()
            return normalized if normalized else None
    except Exception as e:
        try:
            db.session.add(SystemLog(module='pdf', message=f'pdf extract error: {e}'))
            db.session.commit()
        except Exception:
            pass
        return None
