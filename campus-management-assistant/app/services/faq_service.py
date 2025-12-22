from typing import List, Tuple, Optional
from datetime import datetime
import hashlib
from ..extensions import db
from ..models.faq import FAQ
from ..models.user import User
from ..models.chatbot_document import ChatbotDocument
from ..models.logs import SystemLog


def _hash_text(text: str) -> str:
    normalized = " ".join(text.split()).strip().lower()
    import hashlib
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def submit_question(asked_by: User, question: str, category: str, target_department: Optional[str]) -> Tuple[bool, Optional[FAQ], str]:
    try:
        faq = FAQ(
            question=question,
            category=category,
            target_department=target_department,
            status='pending',
            asked_by=asked_by.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(faq)
        db.session.commit()
        return True, faq, 'submitted'
    except Exception as e:
        db.session.add(SystemLog(module='faq', message=f'submit error: {e}'))
        db.session.commit()
        return False, None, 'error'


def answer_faq(faq: FAQ, answer: str, answered_by: User) -> Tuple[bool, str]:
    try:
        faq.answer = answer
        faq.status = 'answered'
        faq.answered_by = answered_by.id
        faq.answered_at = datetime.utcnow()
        db.session.commit()
        # Create chatbot document
        text = f"Q: {faq.question}\nA: {faq.answer}"
        h = _hash_text(text)
        if not ChatbotDocument.query.filter_by(content_hash=h).first():
            db.session.add(ChatbotDocument(
                source_type='faq',
                source_id=faq.id,
                content=text,
                content_hash=h,
                visibility='public',  # FAQs are public unless restricted later by category logic
                created_at=datetime.utcnow(),
            ))
            db.session.commit()
        return True, 'answered'
    except Exception as e:
        db.session.add(SystemLog(module='faq', message=f'answer error: {e}'))
        db.session.commit()
        return False, 'error'


def answered_faqs() -> List[FAQ]:
    return FAQ.query.filter_by(status='answered').order_by(FAQ.answered_at.desc()).all()


def student_answered_faqs() -> List[FAQ]:
    # Students only see answered
    return answered_faqs()


def answered_faqs_filtered(category: Optional[str] = None, q: Optional[str] = None) -> List[FAQ]:
    from sqlalchemy import or_
    qry = FAQ.query.filter_by(status='answered')
    if category:
        qry = qry.filter_by(category=category)
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(FAQ.question.ilike(like), FAQ.answer.ilike(like)))
    return qry.order_by(FAQ.answered_at.desc()).all()


def todays_answered_faqs() -> List[FAQ]:
    from datetime import datetime
    today = datetime.utcnow().date()
    return FAQ.query.filter_by(status='answered').filter(db.func.date(FAQ.answered_at) == today).order_by(FAQ.answered_at.desc()).all()


def student_asked_faqs(student: User) -> List[FAQ]:
    return FAQ.query.filter(FAQ.asked_by == student.id).order_by(FAQ.created_at.desc()).all()


def pending_faqs_for_moderator(department: Optional[str], moderator: User) -> List[FAQ]:
    q = FAQ.query.filter_by(status='pending')
    if department:
        q = q.filter_by(target_department=department)
    return q.order_by(FAQ.created_at.asc()).all()


def all_faqs_admin() -> List[FAQ]:
    return FAQ.query.order_by(FAQ.created_at.desc()).all()


def get_faq(faq_id: int) -> Optional[FAQ]:
    try:
        return db.session.get(FAQ, faq_id)
    except Exception:
        return None


def recent_answered_faqs(limit: int = 10) -> List[FAQ]:
    return FAQ.query.filter_by(status='answered').order_by(FAQ.answered_at.desc()).limit(limit).all()


def create_faq(question: str, category: str, target_department: Optional[str], asked_by: Optional[User]) -> Tuple[bool, Optional[FAQ], str]:
    try:
        faq = FAQ(
            question=question,
            category=category,
            target_department=target_department,
            status='pending',
            asked_by=asked_by.id if asked_by else None,
            created_at=datetime.utcnow(),
        )
        db.session.add(faq)
        db.session.commit()
        return True, faq, 'created'
    except Exception as e:
        db.session.add(SystemLog(module='faq', message=f'create error: {e}'))
        db.session.commit()
        return False, None, 'error'
