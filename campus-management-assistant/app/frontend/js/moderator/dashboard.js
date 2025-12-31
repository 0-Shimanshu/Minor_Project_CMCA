document.addEventListener('DOMContentLoaded', () => {
  // Populate dashboard stats and recent lists from backend
  fetch('/api/moderator/dashboard')
    .then(r => r.json())
    .then(data => {
      if (!data || !data.ok) return;
      // Update user info (top-left)
      const u = data.user || {};
      const nameEl = document.getElementById('modName');
      const idEl = document.getElementById('modId');
      if (nameEl) nameEl.textContent = u.name || 'Moderator';
      if (idEl) idEl.textContent = (u.id != null ? `ID: ${u.id}` : '');
      const stats = data.stats || {};
      const statEls = document.querySelectorAll('.stats .stat h2');
      if (statEls[0]) statEls[0].textContent = String(stats.pending_faqs || 0);
      if (statEls[1]) statEls[1].textContent = String(stats.answered_by_me || 0);
      if (statEls[2]) statEls[2].textContent = String(stats.my_notices || 0);

      const lists = document.querySelectorAll('.list-box .scroll-list');
      const pendingList = lists[0];
      const noticesList = lists[1];
      if (pendingList) {
        pendingList.innerHTML = '';
        (data.recent_pending_faqs || []).forEach(f => {
          const div = document.createElement('div');
          div.className = 'item';
          div.textContent = f.question;
          pendingList.appendChild(div);
        });
      }

      // Optional: refresh user info when focusing back or changes occur
      if (window.api && api.refreshOnFocus) api.refreshOnFocus(()=>{
        fetch('/api/moderator/dashboard').then(r=>r.json()).then(data=>{
          const u = (data && data.user) || {};
          const nameEl = document.getElementById('modName');
          const idEl = document.getElementById('modId');
          if (nameEl) nameEl.textContent = u.name || 'Moderator';
          if (idEl) idEl.textContent = (u.id != null ? `ID: ${u.id}` : '');
        }).catch(()=>{});
      });
      if (noticesList) {
        noticesList.innerHTML = '';
        (data.recent_my_notices || []).forEach(n => {
          const div = document.createElement('div');
          div.className = 'item';
          div.textContent = n.title;
          noticesList.appendChild(div);
        });
      }
    })
    .catch(() => {});
});
