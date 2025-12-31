document.addEventListener('DOMContentLoaded', () => {
  if (typeof auth !== 'undefined' && auth.requireAuth) {
    try { auth.requireAuth(['moderator']); } catch (_) {}
  }
  const faqsList = document.getElementById('faqList');
  const answerForm = document.getElementById('answerForm');
  const faqIdInput = document.getElementById('faqId');
  const questionText = document.getElementById('questionText');
  const answerInput = document.getElementById('answer');
  const createForm = document.getElementById('createForm');
  const createQuestion = document.getElementById('createQuestion');
  const createCategory = document.getElementById('createCategory');
  const createTargetDepartment = document.getElementById('createTargetDepartment');

  function loadFAQs() {
    fetch('/api/moderator/faqs')
      .then(r => r.json())
      .then(data => {
        if (!data || !data.ok) return;
        const faqs = Array.isArray(data.faqs) ? data.faqs : [];
        faqsList.innerHTML = faqs.map(faq => rowHtml(faq)).join('');
        // Wire buttons
        faqsList.querySelectorAll('[data-action="answer"]').forEach(btn => {
          btn.addEventListener('click', () => openAnswerModal(btn.getAttribute('data-id')));
        });
        faqsList.querySelectorAll('[data-action="delete"]').forEach(btn => {
          btn.addEventListener('click', () => deleteFaq(btn.getAttribute('data-id')));
        });
      })
      .catch(() => {});
  }

  function rowHtml(faq){
    const answered = String(faq.status).toLowerCase() === 'answered';
    return `
      <div class="faq-item ${answered ? 'answered' : 'unanswered'}">
        <div class="faq-left">
          <div class="question">${escapeHtml(faq.question)}</div>
          <div class="meta">
            ${escapeHtml(faq.category || 'General')}
          </div>
        </div>
        <div class="faq-actions">
          <a class="btn btn-sm btn-secondary" href="/moderator/faq/${faq.id}">View</a>
          <button class="btn btn-sm btn-primary" data-action="answer" data-id="${faq.id}">${answered ? 'Edit' : 'Answer'}</button>
          <button class="btn btn-sm btn-delete" data-action="delete" data-id="${faq.id}">Delete</button>
        </div>
      </div>`;
  }

  function openAnswerModal(id) {
    fetch('/api/moderator/faqs')
      .then(r => r.json())
      .then(data => {
        const faqs = Array.isArray(data.faqs) ? data.faqs : [];
        const faq = faqs.find(f => String(f.id) === String(id));
        if (!faq) return;
        faqIdInput.value = faq.id;
        // When using admin-styled modal, questionText is a textarea
        if (questionText && questionText.tagName && questionText.tagName.toLowerCase() === 'textarea') {
          questionText.value = faq.question;
        } else {
          questionText.textContent = faq.question;
        }
        answerInput.value = faq.answer || '';
        try { modal.show('answerModal'); } catch(_) {
          const m = document.getElementById('answerModal');
          if (m) { m.style.display = 'flex'; m.classList.add('show'); }
        }
      })
      .catch(() => {});
  }

  // Create FAQ modal controls
  window.openCreateModal = function() {
    const m = document.getElementById('createModal');
    if (m) { m.style.display = 'flex'; }
  };

  window.closeModal = function(id) {
    const m = document.getElementById(id);
    if (m) { m.style.display = 'none'; }
  };

  if (createForm) {
    createForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const question = (createQuestion?.value || '').trim();
      const category = (createCategory?.value || '').trim();
      const target_department = (createTargetDepartment?.value || '').trim();
      if (!question || !category) { toast.show('Question and category are required', 'error'); return; }
      const body = new URLSearchParams({ question, category, target_department });
      fetch('/moderator/faq/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      })
        .then(r => r.text().then(t => ({ ok: r.ok, status: r.status, text: t })))
        .then(res => {
          if (res.ok) {
            toast.show('FAQ created', 'success');
            closeModal('createModal');
            if (createQuestion) createQuestion.value = '';
            if (createCategory) createCategory.value = '';
            if (createTargetDepartment) createTargetDepartment.value = '';
            loadFAQs();
          } else {
            toast.show('Create failed', 'error');
          }
        })
        .catch(() => { toast.show('Network error', 'error'); });
    });
  }

  if (answerForm) {
    answerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const id = faqIdInput.value;
      const answer = answerInput.value.trim();
      if (!id || !answer) return;
      fetch(`/api/moderator/faqs/${id}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer })
      })
        .then(r => r.json())
        .then(data => {
          if (data && data.ok) {
            toast.show('Answer published successfully!', 'success');
            try { modal.hide('answerModal'); } catch(_) {
              const m = document.getElementById('answerModal');
              if (m) m.classList.remove('show');
            }
            loadFAQs();
          } else {
            toast.show('Failed to publish answer', 'error');
          }
        })
        .catch(() => { toast.show('Error publishing answer', 'error'); });
    });
  }

  function deleteFaq(id){
    fetch(`/api/moderator/faqs/${id}/delete`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        if (data && data.ok) {
          toast.show('FAQ deleted', 'success');
          loadFAQs();
        } else {
          const msg = (data && data.message) || 'Delete failed';
          toast.show(msg, 'error');
        }
      })
      .catch(() => { toast.show('Error deleting FAQ', 'error'); });
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  loadFAQs();
  // Auto-refresh every 30s
  setInterval(loadFAQs, 30000);
});
