from flask import Blueprint, send_from_directory, jsonify
from ..services.notice_service import guest_public_notices, get_public_notice

guest_bp = Blueprint('guest', __name__)


@guest_bp.get('/')
def home():
    # Serve new standalone frontend for home page (no Jinja)
    return send_from_directory('frontend/guest', 'home.html')


@guest_bp.get('/css/<path:filename>')
def frontend_css(filename: str):
    # Serve new frontend CSS under /css/* without modifying styles
    return send_from_directory('frontend/css', filename)
@guest_bp.get('/js/<path:filename>')
def frontend_js(filename: str):
    # Serve new frontend Javascript under /js/*
    return send_from_directory('frontend/js', filename)


# Specific alias for typo mismatch: notices HTML expects public_notice.css but file is pubic_notice.css
@guest_bp.get('/css/guest/public_notice.css')
def frontend_css_public_notice_alias():
    return send_from_directory('frontend/css/guest', 'pubic_notice.css')


# Alias for misplaced login CSS reference from auth page
@guest_bp.get('/css/guest/cred/login.css')
def frontend_css_login_alias():
    return send_from_directory('frontend/css/cred', 'login.css')


# Fallback main stylesheet alias used by admin logs page
@guest_bp.get('/css/main.css')
def frontend_css_main_alias():
    # Map to admin dashboard styles to avoid 404; keeps CSS unchanged
    return send_from_directory('frontend/css/admin', 'admin_dashboard.css')


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
    return send_from_directory('frontend/guest', 'home.html')


@guest_bp.get('/guest/chatbot')
def chatbot_alias():
    # Serve new frontend chatbot page (guest)
    return send_from_directory('frontend/guest', 'chatbot.html')


@guest_bp.get('/guest/notices')
def frontend_guest_notices():
    # Serve new frontend notices page for guests
    return send_from_directory('frontend/guest', 'notices.html')


@guest_bp.get('/api/guest/notices')
def api_guest_notices():
    """Return public, published notices for the new frontend as JSON."""
    items = guest_public_notices()
    def fmt_date(dt):
        try:
            return dt.strftime('%d %b %Y') if dt else ''
        except Exception:
            return ''
    data = [
        {
            'id': n.id,
            'title': n.title,
            'summary': n.summary or '',
            'content': n.content,
            'category': (n.category.name if getattr(n, 'category', None) else ''),
            'date': fmt_date(n.created_at),
        }
        for n in items
    ]
    return jsonify({'ok': True, 'notices': data})


@guest_bp.get('/guest/home.html')
def frontend_guest_home_alias():
    # Alias to serve guest home via new frontend path
    return send_from_directory('frontend/guest', 'home.html')


@guest_bp.get('/guest/login.html')
def frontend_guest_login_alias():
    # Alias to serve login via new frontend path reference
    return send_from_directory('frontend/auth', 'login.html')


@guest_bp.get('/guest/public_notices.html')
def frontend_guest_public_notices_alias():
    # Alias for chatbot header link "public_notices.html" -> notices.html
    return send_from_directory('frontend/guest', 'notices.html')
