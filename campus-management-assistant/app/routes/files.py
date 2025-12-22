import os
from flask import Blueprint, abort, send_from_directory, request
from werkzeug.exceptions import HTTPException
from flask_login import current_user
from ..extensions import db
from ..models.notice_file import NoticeFile
from ..models.logs import SystemLog
from ..services.logs_service import log_event
from ..services.notice_service import UPLOAD_DIR

files_bp = Blueprint('files', __name__)


@files_bp.get('/files/notice/<int:file_id>')
def download_notice_file(file_id: int):
    try:
        # Use Query.get for broader SQLAlchemy compatibility
        nf = NoticeFile.query.get(file_id)
        if not nf or not nf.notice or nf.notice.status != 'published':
            log_event('files', 'not_found_or_unpublished', {
                'file_id': file_id,
                'notice_id': getattr(nf, 'notice_id', None),
                'method': request.method,
                'ip': request.remote_addr,
            })
            abort(404)

        # Enforce visibility: public → anyone; student/restricted → requires auth + student role
        visibility = nf.notice.visibility
        if visibility != 'public':
            if not getattr(current_user, 'is_authenticated', False) or getattr(current_user, 'role', '') != 'student':
                log_event('files', 'forbidden_download', {
                    'file_id': file_id,
                    'notice_id': nf.notice_id,
                    'user': getattr(current_user, 'login_id', 'guest'),
                    'role': getattr(current_user, 'role', 'guest'),
                    'method': request.method,
                    'ip': request.remote_addr,
                })
                abort(403)

        # Serve safely from the known uploads directory
        directory = os.path.dirname(nf.file_path)
        filename = os.path.basename(nf.file_path)
        # Ensure the file resides under the expected uploads dir
        uploads_root = os.path.abspath(UPLOAD_DIR)
        if not os.path.abspath(directory).startswith(uploads_root):
            log_event('files', 'blocked_path_traversal', {
                'file_id': file_id,
                'notice_id': nf.notice_id,
                'method': request.method,
                'ip': request.remote_addr,
            })
            abort(403)

        # If the file is missing on disk, return 404
        if not os.path.exists(nf.file_path):
            log_event('files', 'missing_file_on_disk', {
                'file_id': file_id,
                'notice_id': nf.notice_id,
                'method': request.method,
                'ip': request.remote_addr,
            })
            abort(404)

        # Serve file; avoid specifying download_name for broader Flask compatibility
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        # Preserve HTTPException statuses (404/403) raised by abort()
        if isinstance(e, HTTPException):
            raise e
        try:
            log_event('files', 'error', {'file_id': file_id, 'error': str(e), 'method': request.method, 'ip': request.remote_addr})
        except Exception:
            pass
        abort(500)
