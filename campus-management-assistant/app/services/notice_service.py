from typing import List, Optional, Tuple
from datetime import datetime
import hashlib
import os
from werkzeug.datastructures import FileStorage
from ..extensions import db
from ..models.user import User
from ..models.notice import Notice
from ..models.notice_category import NoticeCategory
from ..models.notice_file import NoticeFile
from ..models.chatbot_document import ChatbotDocument
from ..models.logs import SystemLog
from .pdf_service import extract_pdf_text
from .email_service import send_notice_published

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'notices'))
ALLOWED_EXT = {'.pdf', '.png', '.jpg', '.jpeg'}


def _hash_text(text: str) -> str:
    normalized = " ".join(text.split()).strip().lower()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def create_notice(author: User, title: str, summary: Optional[str], content: str, category_name: str,
                  visibility: str, target_department: Optional[str], target_year: Optional[int]) -> Tuple[bool, Optional[Notice], str]:
    try:
        # Enforce restricted visibility requirements
        if visibility == 'restricted' and (not target_department or not target_year):
            return False, None, 'Restricted requires department and year'
        category = NoticeCategory.query.filter_by(name=category_name).first()
        if not category:
            category = NoticeCategory(name=category_name)
            db.session.add(category)
            db.session.flush()
        notice = Notice(
            title=title,
            summary=summary,
            content=content,
            category_id=category.id,
            visibility=visibility,
            status='draft',
            target_department=target_department,
            target_year=target_year,
            created_by=author.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(notice)
        db.session.commit()
        return True, notice, 'created'
    except Exception as e:
        db.session.add(SystemLog(module='notice', message=f"create error: {e} title='{title}' author_id={author.id}"))
        db.session.commit()
        return False, None, 'error'


def update_notice(notice: Notice, **fields) -> Tuple[bool, str]:
    try:
        for k, v in fields.items():
            if hasattr(notice, k):
                setattr(notice, k, v)
        db.session.commit()
        return True, 'updated'
    except Exception as e:
        db.session.add(SystemLog(module='notice', message=f"update error: {e} notice_id={notice.id} title='{getattr(notice,'title', '')}'"))
        db.session.commit()
        return False, 'error'


def attach_file(notice: Notice, storage: FileStorage) -> Tuple[bool, Optional[NoticeFile], str]:
    try:
        if not storage:
            return False, None, 'no file'
        name = storage.filename or ''
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXT:
            return False, None, 'invalid type'
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_name = f"{notice.id}_{int(datetime.utcnow().timestamp())}{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        storage.save(file_path)
        nf = NoticeFile(
            notice_id=notice.id,
            file_name=name,
            file_path=file_path,
            file_type=ext,
            uploaded_at=datetime.utcnow(),
        )
        db.session.add(nf)
        db.session.commit()
        return True, nf, 'uploaded'
    except Exception as e:
        db.session.add(SystemLog(module='notice', message=f"upload error: {e} notice_id={notice.id} file='{storage.filename if storage else ''}'"))
        db.session.commit()
        return False, None, 'error'


def publish_notice(notice: Notice, send_email: bool = True) -> Tuple[bool, str]:
    try:
        notice.status = 'published'
        db.session.commit()
        # Create chatbot document from content and any PDF summaries
        visibility = 'public' if notice.visibility == 'public' else (
            'student' if notice.visibility == 'student' else 'student'
        )
        base_text = f"{notice.title}\n{notice.summary or ''}\n{notice.content}"
        hash_value = _hash_text(base_text)
        if not ChatbotDocument.query.filter_by(content_hash=hash_value).first():
            db.session.add(ChatbotDocument(
                source_type='notice',
                source_id=notice.id,
                content=base_text,
                content_hash=hash_value,
                visibility=visibility,
                created_at=datetime.utcnow(),
            ))
            db.session.commit()
        # PDFs
        for nf in notice.files:
            if nf.file_type == '.pdf':
                text = extract_pdf_text(nf.file_path)
                if text:
                    h = _hash_text(text)
                    if not ChatbotDocument.query.filter_by(content_hash=h).first():
                        db.session.add(ChatbotDocument(
                            source_type='notice_pdf',
                            source_id=notice.id,
                            content=text,
                            content_hash=h,
                            visibility=visibility,
                            created_at=datetime.utcnow(),
                        ))
                        db.session.commit()
        # Send email notifications (do not block on failure)
        if send_email:
            try:
                send_notice_published(notice)
            except Exception as e:
                db.session.add(SystemLog(module='email', message=f"publish email error: {e} notice_id={notice.id} title='{notice.title}'"))
                db.session.commit()
        return True, 'published'
    except Exception as e:
        db.session.add(SystemLog(module='notice', message=f"publish error: {e} notice_id={notice.id}"))
        db.session.commit()
        return False, 'error'


# Visibility fetching

def guest_public_notices() -> List[Notice]:
    return Notice.query.filter_by(visibility='public', status='published').order_by(Notice.created_at.desc()).all()


def student_visible_notices(student: User) -> List[Notice]:
    q = Notice.query.filter(Notice.status == 'published').filter(
        (Notice.visibility == 'public') |
        (Notice.visibility == 'student') |
        ((Notice.visibility == 'restricted') & (Notice.target_department == student.department) & (Notice.target_year == student.year))
    ).order_by(Notice.created_at.desc())
    return q.all()


def moderator_notices(moderator: User) -> List[Notice]:
    return Notice.query.filter_by(created_by=moderator.id).order_by(Notice.created_at.desc()).all()


def admin_all_notices() -> List[Notice]:
    return Notice.query.order_by(Notice.created_at.desc()).all()


def delete_notice_owned(notice_id: int, owner: User) -> Tuple[bool, str]:
    """Delete a notice if owned by the given moderator/admin. Remove files from disk safely."""
    try:
        n = db.session.get(Notice, notice_id)
        if not n:
            return False, 'not found'
        if n.created_by != owner.id and owner.role != 'admin':
            return False, 'forbidden'
        # Delete attached files from disk safely
        for nf in list(n.files):
            try:
                if nf.file_path and os.path.exists(nf.file_path):
                    os.remove(nf.file_path)
            except Exception as e:
                db.session.add(SystemLog(module='notice', message=f"file delete warn: {e} notice_id={n.id} file_id={nf.id}"))
                db.session.commit()
        db.session.delete(n)
        db.session.commit()
        return True, 'deleted'
    except Exception as e:
        db.session.add(SystemLog(module='notice', message=f"delete error: {e} notice_id={notice_id} owner_id={owner.id}"))
        db.session.commit()
        return False, 'error'


def recent_published_notices(limit: int = 10) -> List[Notice]:
    return Notice.query.filter_by(status='published').order_by(Notice.created_at.desc()).limit(limit).all()


def get_notice_for_moderator(notice_id: int, moderator: User) -> Optional[Notice]:
    try:
        n = db.session.get(Notice, notice_id)
        if not n or n.created_by != moderator.id:
            return None
        return n
    except Exception:
        return None


def get_public_notice(notice_id: int) -> Optional[Notice]:
    try:
        n = db.session.get(Notice, notice_id)
        if not n or n.status != 'published' or n.visibility != 'public':
            return None
        return n
    except Exception:
        return None


def list_categories() -> List[NoticeCategory]:
    return NoticeCategory.query.order_by(NoticeCategory.name.asc()).all()


def student_visible_notices_by_category(student: User, category_name: Optional[str]) -> List[Notice]:
    q = Notice.query.filter(Notice.status == 'published').filter(
        (Notice.visibility == 'public') |
        (Notice.visibility == 'student') |
        ((Notice.visibility == 'restricted') & (Notice.target_department == student.department) & (Notice.target_year == student.year))
    )
    if category_name:
        cat = NoticeCategory.query.filter_by(name=category_name).first()
        if cat:
            q = q.filter(Notice.category_id == cat.id)
    return q.order_by(Notice.created_at.desc()).all()


def todays_student_notices(student: User) -> List[Notice]:
    from datetime import datetime
    today = datetime.utcnow().date()
    q = Notice.query.filter(Notice.status == 'published').filter(
        (Notice.visibility == 'public') |
        (Notice.visibility == 'student') |
        ((Notice.visibility == 'restricted') & (Notice.target_department == student.department) & (Notice.target_year == student.year))
    ).filter(db.func.date(Notice.created_at) == today)
    return q.order_by(Notice.created_at.desc()).all()
