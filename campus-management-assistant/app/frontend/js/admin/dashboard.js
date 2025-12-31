document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/admin/dashboard')
    .then(r => r.json())
    .then(data => {
      if (!data || !data.ok) return;
      // Update user info (top-left)
      const u = data.user || {};
      const nameEl = document.getElementById('adminName');
      const idEl = document.getElementById('adminId');
      if (nameEl) nameEl.textContent = u.name || 'Admin';
      if (idEl) idEl.textContent = (u.id != null ? `ID: ${u.id}` : '');
      // Update stats
      const statEls = document.querySelectorAll('.stats .stat-card h2');
      const s = data.stats || {};
      if (statEls[0]) statEls[0].textContent = String(s.total_users ?? '0');
      if (statEls[1]) statEls[1].textContent = String(s.published_notices ?? '0');
      if (statEls[2]) statEls[2].textContent = String(s.answered_faqs ?? '0');
      const noticesList = document.querySelectorAll('.panel')[0]?.querySelector('.panel-list');
      const faqsList = document.querySelectorAll('.panel')[1]?.querySelector('.panel-list');
      const emailsList = document.querySelectorAll('.panel')[2]?.querySelector('.panel-list');
      const myNoticesList = document.getElementById('myNoticesList');
      const myFaqsList = document.getElementById('myFaqsList');
      if (noticesList) {
        noticesList.innerHTML = '';
        (data.recent_notices || []).forEach(n => {
          const div = document.createElement('div');
          div.className = 'panel-item';
          div.innerHTML = `<p>${escapeHtml(n.title)}</p><span>${escapeHtml(n.category || '')} · ${escapeHtml(n.date || '')}</span>`;
          noticesList.appendChild(div);
        });
      }
      if (faqsList) {
        faqsList.innerHTML = '';
        (data.recent_faqs || []).forEach(f => {
          const div = document.createElement('div');
          div.className = 'panel-item';
          div.innerHTML = `<p>${escapeHtml(f.question)}</p><span>Answered · ${escapeHtml(f.answered_at || '')}</span>`;
          faqsList.appendChild(div);
        });
      }
      if (emailsList) {
        emailsList.innerHTML = '';
        (data.recent_emails || []).forEach(e => {
          const div = document.createElement('div');
          div.className = 'panel-item';
          div.innerHTML = `<p>${escapeHtml(e.subject || 'Email')}</p><span>Sent · ${escapeHtml(e.date || '')}</span>`;
          emailsList.appendChild(div);
        });
      }

      if (myNoticesList) {
        myNoticesList.innerHTML = '';
        (data.recent_my_notices || []).forEach(n => {
          const div = document.createElement('div');
          div.className = 'panel-item';
          div.innerHTML = `<p>${escapeHtml(n.title)}</p><span>${escapeHtml(n.category || '')} · ${escapeHtml(n.date || '')} · ${escapeHtml(n.status || '')}</span>`;
          myNoticesList.appendChild(div);
        });
      }

      if (myFaqsList) {
        myFaqsList.innerHTML = '';
        (data.recent_my_faqs || []).forEach(f => {
          const div = document.createElement('div');
          div.className = 'panel-item';
          div.innerHTML = `<p>${escapeHtml(f.question)}</p><span>${escapeHtml(f.category || '')} · ${escapeHtml(f.answered_at || '')}</span>`;
          myFaqsList.appendChild(div);
        });
      }
    })
    .catch(() => {});

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
  // Refresh on focus or when data changes elsewhere
  if (window.api && api.refreshOnFocus) api.refreshOnFocus(()=>{
    fetch('/api/admin/dashboard').then(r=>r.json()).then(()=>location.reload());
  });
  if (window.api && api.onChange) api.onChange('*', ()=>{
    // Lightweight: re-run the same fetch pipeline to update lists and stats
    fetch('/api/admin/dashboard')
      .then(r=>r.json())
      .then(data => {
        if (!data || !data.ok) return;
        // Update user info on change as well
        const u = data.user || {};
        const nameEl = document.getElementById('adminName');
        const idEl = document.getElementById('adminId');
        if (nameEl) nameEl.textContent = u.name || 'Admin';
        if (idEl) idEl.textContent = (u.id != null ? `ID: ${u.id}` : '');
        const statEls = document.querySelectorAll('.stats .stat-card h2');
        const s = data.stats || {};
        if (statEls[0]) statEls[0].textContent = String(s.total_users ?? '0');
        if (statEls[1]) statEls[1].textContent = String(s.published_notices ?? '0');
        if (statEls[2]) statEls[2].textContent = String(s.answered_faqs ?? '0');
        // Also update notice list when notices change
        const noticesList = document.querySelectorAll('.panel')[0]?.querySelector('.panel-list');
        if (noticesList && data.recent_notices) {
          noticesList.innerHTML = '';
          (data.recent_notices || []).forEach(n => {
            const div = document.createElement('div');
            div.className = 'panel-item';
            div.innerHTML = `<p>${escapeHtml(n.title)}</p><span>${escapeHtml(n.category || '')} · ${escapeHtml(n.date || '')}</span>`;
            noticesList.appendChild(div);
          });
        }
        const myNoticesList = document.getElementById('myNoticesList');
        if (myNoticesList && data.recent_my_notices) {
          myNoticesList.innerHTML = '';
          (data.recent_my_notices || []).forEach(n => {
            const div = document.createElement('div');
            div.className = 'panel-item';
            div.innerHTML = `<p>${escapeHtml(n.title)}</p><span>${escapeHtml(n.category || '')} · ${escapeHtml(n.date || '')} · ${escapeHtml(n.status || '')}</span>`;
            myNoticesList.appendChild(div);
          });
        }
        const myFaqsList = document.getElementById('myFaqsList');
        if (myFaqsList && data.recent_my_faqs) {
          myFaqsList.innerHTML = '';
          (data.recent_my_faqs || []).forEach(f => {
            const div = document.createElement('div');
            div.className = 'panel-item';
            div.innerHTML = `<p>${escapeHtml(f.question)}</p><span>${escapeHtml(f.category || '')} · ${escapeHtml(f.answered_at || '')}</span>`;
            myFaqsList.appendChild(div);
          });
        }
      })
      .catch(()=>{});
  });
});
