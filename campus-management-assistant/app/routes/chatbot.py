from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from . import require_role
from ..services.chatbot_service import ask_gemini, chatbot_health

chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.get('/guest/chatbot')
def guest_chatbot():
    return render_template('guest/chatbot.html')


@chatbot_bp.post('/guest/chatbot')
def guest_chatbot_post():
    q = request.form.get('query', '').strip()
    ok, ans = ask_gemini(q, role='guest')
    return render_template('guest/chatbot.html', query=q, answer=ans, ok=ok)


@chatbot_bp.get('/student/chatbot')
@login_required
@require_role('student')
def student_chatbot():
    return render_template('student/chatbot.html')


@chatbot_bp.post('/student/chatbot')
@login_required
@require_role('student')
def student_chatbot_post():
    q = request.form.get('query', '').strip()
    ok, ans = ask_gemini(q, role='student')
    return render_template('student/chatbot.html', query=q, answer=ans, ok=ok)


@chatbot_bp.post('/chatbot/query')
def chatbot_query():
    try:
        data = request.get_json(silent=True) or {}
        q = str(data.get('query', '')).strip()
        if not q:
            return jsonify({"ok": False, "answer": "Please provide a question."}), 400
        role = 'student' if getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'role', '') == 'student' else 'guest'
        ok, ans = ask_gemini(q, role=role)
        status = 200 if ok else 400
        return jsonify({"ok": ok, "answer": ans}), status
    except Exception:
        return jsonify({"ok": False, "answer": "Sorry, an error occurred."}), 500


@chatbot_bp.get('/chatbot/health')
def chatbot_health_route():
    try:
        return jsonify(chatbot_health()), 200
    except Exception:
        return jsonify({"ok": False}), 500
