document.addEventListener('DOMContentLoaded', () => {
  if (typeof auth !== 'undefined' && auth.requireAuth) {
    try { auth.requireAuth(['moderator']); } catch (_) {}
  }
  const tbody = document.getElementById('noticesTable');

  function loadNotices() {
    fetch('/api/moderator/notices')
      .then(r => r.json())
      .then(data => {
        if (!data || !data.ok) return;
        const notices = Array.isArray(data.notices) ? data.notices : [];
        tbody.innerHTML = notices.map(n => rowHtml(n)).join('');
        wireActions();
      })
      .catch(() => {});
  }

  function rowHtml(n) {
    const isDraft = String(n.status).toLowerCase() === 'draft';
    return `
      <tr>
        <td><strong>${escapeHtml(n.title)}</strong></td>
        <td><span class="badge badge-info">${escapeHtml(n.category || '')}</span></td>
        <td><span class="badge badge-${isDraft ? 'warning' : 'success'}">${escapeHtml(n.status)}</span></td>
        <td><span class="badge badge-info">${escapeHtml(n.visibility || '')}</span></td>
        <td>${escapeHtml(n.created_at || '')}</td>
        <td>
          <div class="flex gap-sm">
            <a class="btn btn-sm btn-secondary" href="/moderator/notices/${n.id}">View</a>
            <a class="btn btn-sm btn-secondary" href="/moderator/notices/${n.id}/edit">Edit</a>
            ${isDraft ? `<button class="btn btn-sm btn-success" data-action="publish" data-id="${n.id}">Publish</button>` : ''}
            <button class="btn btn-sm btn-danger" data-action="delete" data-id="${n.id}">Delete</button>
          </div>
        </td>
      </tr>`;
  }

  function wireActions() {
    tbody.querySelectorAll('[data-action="publish"]').forEach(btn => {
      btn.addEventListener('click', () => publishNotice(btn.getAttribute('data-id')));
    });
    tbody.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', () => deleteNotice(btn.getAttribute('data-id')));
    });
  }

  function publishNotice(id) {
    fetch(`/api/moderator/notices/${id}/publish`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        if (data && data.ok) {
          toast.show('Notice published!', 'success');
          loadNotices();
        } else {
          toast.show('Publish failed', 'error');
        }
      })
      .catch(() => { toast.show('Error publishing', 'error'); });
  }

  function deleteNotice(id) {
    if (!confirm('Delete this notice?')) return;
    fetch(`/api/moderator/notices/${id}/delete`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        if (data && data.ok) {
          toast.show('Notice deleted', 'success');
          loadNotices();
        } else {
          toast.show('Delete failed', 'error');
        }
      })
      .catch(() => { toast.show('Error deleting', 'error'); });
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  loadNotices();
  // Auto-refresh every 30s
  setInterval(loadNotices, 30000);
});
