document.addEventListener('DOMContentLoaded', () => {
  const list = document.getElementById('faqList');
  const askBtn = document.querySelector('.ask-btn');
  const profile = document.querySelector('.student-profile');
  if (!list) return;

  let currentStudentId = '';
  let faqs = [];

  // Populate header with student info
  fetch('/api/student/dashboard')
    .then(res => res.json())
    .then(data => {
      const u = (data && data.user) || {};
      if (profile) {
        const nameEl = profile.querySelector('strong');
        const idEl = profile.querySelector('span');
        if (nameEl) nameEl.textContent = u.name || '';
        if (idEl) idEl.textContent = u.enrollment_no || '';
      }
    })
    .catch(() => {});

  fetch('/api/student/faqs')
    .then(res => res.json())
    .then(data => {
      if (!data || !data.ok) return;
      currentStudentId = data.current_student_id || '';
      faqs = Array.isArray(data.faqs) ? data.faqs : [];
      renderFAQs();
    })
    .catch(() => {});

  function renderFAQs() {
    list.innerHTML = '';
    faqs.forEach(faq => {
      const row = document.createElement('div');
      row.className = 'faq-item';
      const statusClass = String(faq.status).toLowerCase();
      const canEdit = (statusClass === 'pending') && (faq.askedBy && faq.askedBy === currentStudentId);
      row.innerHTML = `
        <p>${escapeHtml(faq.question)}</p>
        <span class="status ${statusClass}">${escapeHtml(faq.status)}</span>
        <div class="actions">
          <button class="view-btn">View</button>
          ${canEdit ? '<button class="edit-btn">Edit</button>' : ''}
        </div>
      `;
      row.querySelector('.view-btn').addEventListener('click', () => viewFAQ(faq));
      if (canEdit) {
        row.querySelector('.edit-btn').addEventListener('click', () => editFAQ(faq));
      }
      list.appendChild(row);
    });
  }

  function viewFAQ(faq) {
    const modal = document.getElementById('viewModal');
    if (!modal) return;
    modal.querySelector('#viewQuestion').textContent = faq.question;
    modal.querySelector('#viewStatus').textContent = faq.status;
    modal.querySelector('#viewAnswer').textContent = (faq.status.toLowerCase() === 'answered' && faq.answer) ? faq.answer : 'This question is yet to be answered.';
    openModal('viewModal');
  }

  function editFAQ(faq) {
    const modal = document.getElementById('editModal');
    if (!modal) return;
    modal.querySelector('#editQuestion').value = faq.question;
    modal.dataset.faqId = faq.id;
    openModal('editModal');
  }

  // Editing student FAQs after submission is not allowed per spec.
  window.saveEdit = function() {
    alert('Editing your question after submission is not allowed.');
    closeModal('editModal');
  };

  window.openAskModal = function() { openModal('askModal'); };

  window.submitQuestion = function() {
    const textarea = document.getElementById('newQuestion');
    const text = (textarea && textarea.value || '').trim();
    if (!text) return;
    fetch('/api/student/faqs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text })
    })
      .then(res => res.json())
      .then(data => {
        if (data && data.ok) {
          // Prepend locally
          faqs.unshift({ id: data.id, question: text, answer: '', status: 'Pending', askedBy: currentStudentId });
          renderFAQs();
          if (textarea) textarea.value = '';
          closeModal('askModal');
        }
      })
      .catch(() => {});
  };

  function openModal(id) { const el = document.getElementById(id); if (el) el.style.display = 'flex'; }
  window.closeModal = function(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; };

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  
});
