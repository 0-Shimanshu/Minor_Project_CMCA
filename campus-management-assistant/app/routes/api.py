from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.notice import Notice
from app.models.notice_category import NoticeCategory
from app.models.faq import FAQ
from app.services.auth_service import authenticate_user, register_student
from app.services.notice_service import get_visible_notices, create_notice
from app import db
from datetime import datetime

api_bp = Blueprint('api', __name__)

# --- Auth ---

@api_bp.post('/auth/login')
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    login_id = data.get('login_id')
    password = data.get('password')
    
    user, message = authenticate_user(login_id, password)
    if user:
        login_user(user)
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'role': user.role,
                'department': user.department
            },
            'redirect': f'/{user.role}/dashboard'
        })
    return jsonify({'success': False, 'message': message}), 401

@api_bp.post('/auth/register')
def register():
    data = request.get_json()
    try:
        user = register_student(data)
        return jsonify({'success': True, 'message': 'Registration successful'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@api_bp.post('/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

# --- Student ---

@api_bp.get('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Get stats
    active_notices = get_visible_notices(current_user, limit=None) # optimize count later
    notice_count = len(active_notices)
    
    # Simple stats for now
    stats = {
        'active_notices': notice_count,
        'my_faqs': FAQ.query.filter(FAQ.asked_by == current_user.id).count(),
        'user': {
            'name': getattr(current_user, 'sign_name', '') or getattr(current_user, 'name', ''),
            'department': getattr(current_user, 'department', ''),
            'year': getattr(current_user, 'year', None)
        }
    }
    return jsonify(stats)

# --- Notices ---

@api_bp.get('/notices/public')
def public_notices():
    notices = Notice.query.filter_by(audience='public', is_published=True).order_by(Notice.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notices])

@api_bp.get('/notices/student')
@login_required
def student_notices():
    cat_id = request.args.get('category')
    notices = get_visible_notices(current_user, category_id=cat_id)
    return jsonify([n.to_dict() for n in notices])

# --- Chatbot (Stub) ---
@api_bp.post('/chatbot/query')
def chatbot_query():
    # Placeholder for chatbot service integration
    return jsonify({'response': 'Chatbot is initializing...'})
