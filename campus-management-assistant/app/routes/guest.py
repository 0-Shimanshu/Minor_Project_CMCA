from flask import Blueprint, render_template
from ..services.notice_service import guest_public_notices, get_public_notice

guest_bp = Blueprint('guest', __name__)


@guest_bp.get('/')
def home():
    return render_template('guest/home.html')


@guest_bp.get('/notices')
def notices():
    items = guest_public_notices()
    return render_template('guest/notices.html', notices=items)


@guest_bp.get('/notices/<int:notice_id>')
def notice_detail(notice_id: int):
    n = get_public_notice(notice_id)
    if not n:
        return render_template('guest/notices.html', notices=guest_public_notices(), error='Notice not available'), 404
    return render_template('guest/notice_detail.html', notice=n)


@guest_bp.get('/chatbot')
def chatbot():
    # Spec guest chatbot page
    return render_template('guest/chatbot.html')


@guest_bp.get('/guest/chatbot')
def chatbot_alias():
    # Compatibility for existing link in guest/home.html
    return render_template('guest/chatbot.html')
