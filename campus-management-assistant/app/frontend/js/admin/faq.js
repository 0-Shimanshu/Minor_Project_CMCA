document.addEventListener('DOMContentLoaded', () => {
  const list = document.getElementById('faqList');
  const viewModal = document.getElementById('viewModal');
  const answerModal = document.getElementById('answerModal');
  const createModal = document.getElementById('createModal');
  if (!list) return;

  function load() {
    fetch('/api/admin/faqs')
      .then(r => r.json())
      .then(data => {
        if (!data || !data.ok) return;
        const faqs = Array.isArray(data.faqs) ? data.faqs : [];
        list.innerHTML = faqs.map(itemHtml).join('');
        wireActions();
      })
      .catch(() => {});
  }

  function itemHtml(f) {
    const isAnswered = String(f.status).toLowerCase() === 'answered';
    const cls = isAnswered ? 'answered' : 'unanswered';
    return `
      <div class="faq-item ${cls}" data-id="${f.id}">
        <div class="faq-left">
          <p class="question">${escapeHtml(f.question)}</p>
          <span class="meta">${escapeHtml(f.category || 'General')}</span>
        </div>
        <div class="faq-actions">
          <button class="btn-secondary" data-action="view">View</button>
          ${isAnswered ? '' : '<button class="btn-primary" data-action="answer">Answer</button>'}
          <button class="btn-delete" data-action="delete">Delete</button>
        </div>
      </div>`;
  }

  function wireActions() {
    list.querySelectorAll('[data-action="view"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.faq-item')?.getAttribute('data-id');
        if (!id || !viewModal) return;
        // Fetch single FAQ from list again (simple approach)
        fetch('/api/admin/faqs')
          .then(r => r.json())
          .then(data => {
            const faqs = Array.isArray(data.faqs) ? data.faqs : [];
            const faq = faqs.find(x => String(x.id) === String(id));
            if (!faq) return;
            const q = viewModal.querySelector('.modal-question');
            const meta = viewModal.querySelector('.modal-meta');
            const ans = viewModal.querySelector('.modal-answer');
            if (q) q.textContent = faq.question;
            if (meta) meta.textContent = faq.category || 'General';
            if (ans) ans.textContent = (faq.answer ? faq.answer : 'This FAQ is currently unanswered.');
            viewModal.style.display = 'flex';
          });
      });
    });
    list.querySelectorAll('[data-action="answer"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.faq-item')?.getAttribute('data-id');
        if (!id || !answerModal) return;
        answerModal.dataset.faqId = id;
        const textarea = answerModal.querySelector('textarea');
        if (textarea) textarea.value = '';
        answerModal.style.display = 'flex';
      });
    });
    list.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.faq-item')?.getAttribute('data-id');
        if (!id) return;
        if (!confirm('Delete this FAQ?')) return;
        fetch(`/api/admin/faqs/${id}/delete`, { method: 'POST' })
          .then(r => r.json())
          .then(data => {
            if (data && data.ok) {
              toast && toast.show && toast.show('FAQ deleted', 'success');
              load();
            } else {
              toast && toast.show && toast.show('Delete failed', 'error');
            }
          })
          .catch(() => { toast && toast.show && toast.show('Error deleting', 'error'); });
      });
    });
  }

  // Modal helpers bound to existing buttons
  window.openCreateModal = function() { if (createModal) createModal.style.display = 'flex'; };
  window.closeModal = function(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; };

  // Create FAQ (uses existing modal structure without changing HTML)
  if (createModal) {
    const createBtn = createModal.querySelector('.btn-primary');
    if (createBtn) {
      createBtn.addEventListener('click', async () => {
        const qTextarea = createModal.querySelector('textarea');
        const question = (qTextarea && qTextarea.value || '').trim();
        if (!question) { toast && toast.show && toast.show('Question is required','error'); return; }
        const fd = new FormData();
        fd.append('question', question);
        try{
          const r = await fetch('/admin/faq/create', { method: 'POST', body: fd });
          if (r.ok) {
            toast && toast.show && toast.show('FAQ created','success');
            createModal.style.display = 'none';
            load();
          } else {
            toast && toast.show && toast.show('Failed to create FAQ','error');
          }
        }catch(_) { toast && toast.show && toast.show('Network error','error'); }
      });
    }
  }


  // Submit answer
  const answerSubmit = (answerModal && answerModal.querySelector('.btn-primary')) || null;
  if (answerSubmit) {
    answerSubmit.addEventListener('click', () => {
      const id = answerModal?.dataset?.faqId;
      const textarea = answerModal?.querySelector('textarea');
      const text = (textarea && textarea.value || '').trim();
      if (!id || !text) return;
      fetch(`/api/admin/faqs/${id}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: text })
      })
        .then(r => r.json())
        .then(data => {
          if (data && data.ok) {
            toast && toast.show && toast.show('Answer published', 'success');
            if (answerModal) answerModal.style.display = 'none';
            load();
          } else {
            toast && toast.show && toast.show('Failed to publish answer', 'error');
          }
        })
        .catch(() => { toast && toast.show && toast.show('Error publishing', 'error'); });
    });
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  load();
  // Auto-refresh every 30s
  setInterval(load, 30000);
  
});
