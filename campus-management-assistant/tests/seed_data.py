import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.notice import Notice
from app.models.notice_category import NoticeCategory
from app.models.notice_file import NoticeFile
from app.services.notice_service import publish_notice, UPLOAD_DIR
from app.services.faq_service import submit_question, answer_faq
from app.models.chatbot_document import ChatbotDocument
import hashlib

"""
Seed dataset (focused, reasoning-ready):
- Moderator: login_id=mod1, password=mod123, role=moderator, department=CSE
- Students:
    - ENR001: dept=CSE, year=2, email=stu1@example.com
    - ENR002: dept=ECE, year=3, email=stu2@example.com
- Categories: General, Exam
- Notices: keep minimal set used by tests
    - Public (with dummy PDF), Student, Restricted (CSE, year 2)
- FAQs: 5 meaningful questions with reasoned answers
- ChatbotDocuments: reasoning-rich policy snippets (public/student)
"""

def ensure_category(name: str) -> NoticeCategory:
    cat = NoticeCategory.query.filter_by(name=name).first()
    if not cat:
        cat = NoticeCategory(name=name)
        db.session.add(cat)
        db.session.commit()
    return cat


def ensure_user(login_id: str, role: str, **fields) -> User:
    u = User.query.filter_by(login_id=login_id).first()
    if not u:
        u = User(
            login_id=login_id,
            password_hash=generate_password_hash(fields.get('password', 'pass123')),
            role=role,
            enrollment_no=fields.get('enrollment_no'),
            department=fields.get('department'),
            year=fields.get('year'),
            sign_name=fields.get('sign_name') or login_id,
            email=fields.get('email'),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.session.add(u)
        db.session.commit()
    return u


def create_notice_record(author: User, title: str, summary: str, content: str, category: NoticeCategory,
                         visibility: str, target_department=None, target_year=None) -> Notice:
    n = Notice(
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
    db.session.add(n)
    db.session.commit()
    return n


def attach_dummy_pdf(notice: Notice, filename: str = 'dummy.pdf') -> NoticeFile:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"{notice.id}_{int(datetime.utcnow().timestamp())}.pdf"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    # Write a minimal PDF-like file; extraction may fail gracefully and be logged
    with open(file_path, 'wb') as f:
        f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\n%%EOF\n")
    nf = NoticeFile(
        notice_id=notice.id,
        file_name=filename,
        file_path=file_path,
        file_type='.pdf',
        uploaded_at=datetime.utcnow(),
    )
    db.session.add(nf)
    db.session.commit()
    return nf


def ensure_chatbot_doc(content: str, visibility: str, source_type: str = 'seed', source_id: int | None = None) -> ChatbotDocument:
    content = content.strip()
    h = hashlib.sha256(content.encode('utf-8')).hexdigest()
    existing = ChatbotDocument.query.filter_by(content_hash=h).first()
    if existing:
        return existing
    doc = ChatbotDocument(
        source_type=source_type,
        source_id=source_id,
        content=content,
        content_hash=h,
        visibility=visibility,
    )
    db.session.add(doc)
    db.session.commit()
    return doc


def main():
    app = create_app()
    with app.app_context():
        # Users
        mod = ensure_user('mod1', 'moderator', password='mod123', department='CSE', sign_name='Moderator One')
        stu1 = ensure_user('ENR001', 'student', password='stu123', enrollment_no='ENR001', department='CSE', year=2, email='stu1@example.com', sign_name='Student One')
        stu2 = ensure_user('ENR002', 'student', password='stu456', enrollment_no='ENR002', department='ECE', year=3, email='stu2@example.com', sign_name='Student Two')

        # Categories
        gen = ensure_category('General')
        exam = ensure_category('Exam')

        # Notices
        pub = create_notice_record(mod, 'Public Notice', 'Visible to all', 'This is a public notice.', gen, 'public')
        attach_dummy_pdf(pub, 'public_dummy.pdf')
        publish_notice(pub)

        student_n = create_notice_record(mod, 'Student Notice', 'Visible to students', 'This is a student notice.', gen, 'student')
        publish_notice(student_n)

        restr = create_notice_record(mod, 'Restricted Notice', 'CSE year 2 only', 'Restricted content.', exam, 'restricted', target_department='CSE', target_year=2)
        attach_dummy_pdf(restr, 'restricted_dummy.pdf')
        publish_notice(restr)

        # FAQs: create 5 meaningful questions and answer them
        meaningful_faqs = [
            ("How can I apply for an exam retake due to illness?", "Submit a medical certificate within 7 days and request HOD approval."),
            ("What is the minimum attendance required to sit for exams?", "75% attendance; shortage requires Dean approval with valid reasons."),
            ("Can CSE year-2 students access restricted lab notices?", "Yes, if the notice targets CSE year 2, access is allowed."),
            ("How do I challenge a grade?", "File a grade review within 3 working days through the academic portal."),
            ("How to get an official bonafide certificate?", "Apply via student services; processing time is 2 working days."),
        ]
        for q, a in meaningful_faqs:
            ok, faq, msg = submit_question(stu1, q, 'General', 'CSE')
            if faq:
                answer_faq(faq, a, mod)

        # Chatbot reasoning documents (public and student)
        public_reasoning = """
    Policy: Exam Retake (Public)
    Rule: A student may request an exam retake if they provide a valid medical certificate and obtain HOD approval within 7 days of the exam date.
    Procedure:
    1) Collect medical certificate.
    2) Submit retake request through the academic portal.
    3) Receive HOD approval within 7 days.
    Outcome: Approved requests get a scheduled retake; otherwise, no retake.
    Examples:
    - Student with certificate submitted on day 5: APPROVED.
    - Student without certificate: NOT APPROVED.
    """.strip()
        ensure_chatbot_doc(public_reasoning, 'public')

        student_reasoning = """
    Policy: Attendance Threshold (Student)
    Rule: Minimum attendance is 75% to sit for final exams.
    Exceptions: If attendance is between 65% and 75%, submit an undertaking and seek Dean approval.
    Procedure:
    1) Check attendance in student portal.
    2) If < 75%, open undertaking form.
    3) Upload justification (medical/official) and request approval.
    Outcome: Approval permits exam entry; rejection requires attending the next session.
    Examples:
    - Attendance 72% with medical proof: CONDITIONALLY APPROVED.
    - Attendance 60%: NOT ELIGIBLE.
    """.strip()
        ensure_chatbot_doc(student_reasoning, 'student')

        general_services = """
    Policy: Bonafide Certificate
    Rule: Issue to currently enrolled students upon request.
    Procedure:
    1) Submit request in student services.
    2) Processing time: 2 working days.
    Outcome: Certificate available in downloads.
    Examples:
    - Request on Monday: Ready by Wednesday.
    """.strip()
        ensure_chatbot_doc(general_services, 'public')

        # 3rd-year exam samples
        exam_notice_3rd = create_notice_record(
            mod,
            'Exam Schedule - 3rd Year',
            'End-semester timetable and guidelines for 3rd-year students.',
            'Please review the attached timetable for all departments. Bring your ID card. Mobile phones and smart watches are not permitted in the exam hall.',
            exam,
            'restricted',
            target_department='CSE',
            target_year=3,
        )
        attach_dummy_pdf(exam_notice_3rd, 'exam_schedule_3rd_year.pdf')
        publish_notice(exam_notice_3rd)

        third_year_policy = """
    Policy: Exam Registration (3rd Year)
    Rule: All 3rd-year students must complete exam registration at least 10 days before the first exam.
    Procedure:
    1) Open the academic portal and navigate to Exam Registration.
    2) Confirm subjects and pay applicable fees.
    3) Download the admit card once registration is approved.
    Outcome: Late submissions are not accepted; students without admit cards cannot sit the exam.
    Examples:
    - Registration completed 12 days prior: APPROVED.
    - Registration attempted 5 days prior: NOT ACCEPTED.
    """.strip()
        ensure_chatbot_doc(third_year_policy, 'student')

        print('SEED_OK')

if __name__ == '__main__':
    main()
