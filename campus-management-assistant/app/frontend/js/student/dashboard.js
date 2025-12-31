document.addEventListener('DOMContentLoaded', () => {
  // New layout elements (updated dashboard.html)
  const noticeCountEl = document.getElementById('noticeCount');
  const faqCountEl = document.getElementById('faqCount');
  const pendingFaqEl = document.getElementById('pendingFaq');
  const recentNoticesList = document.getElementById('recentNotices');
  const myQuestionsList = document.getElementById('myQuestions');

  // Legacy layout elements (older dashboard structure)
  const profile = document.querySelector('.student-profile');
  const summary = document.querySelector('.summary');
  const panels = document.querySelectorAll('.panel');
  const recentPanel = panels && panels[0];
  const questionsPanel = panels && panels[1];

  function load() {
    fetch('/api/student/dashboard')
      .then(res => res.json())
      .then(data => {
      if (!data || !data.ok) return;
      const u = data.user || {};
      const noticesToday = Array.isArray(data.notices_today) ? data.notices_today : [];
      const recentFallback = Array.isArray(data.recent_notices) ? data.recent_notices : [];
      const notices = (noticesToday.length ? noticesToday : recentFallback);
      const myFaqs = Array.isArray(data.my_faqs) ? data.my_faqs : [];

      // Update header with real student name
      const headerTitle = document.querySelector('.header h1');
      if (headerTitle) {
        const name = u.name ? `, ${escapeHtml(u.name)} ` : ' ';
        headerTitle.innerHTML = `Welcome${name}👋`;
      }

      // New layout population
      if (noticeCountEl) noticeCountEl.textContent = String(notices.length);
      if (faqCountEl) faqCountEl.textContent = String(myFaqs.length);
      if (pendingFaqEl) {
        const pending = myFaqs.filter(q => String(q.status).toLowerCase() === 'pending').length;
        pendingFaqEl.textContent = String(pending);
      }
      if (recentNoticesList) {
        recentNoticesList.innerHTML = '';
        notices.forEach(n => {
          const cat = n.category || 'Academic';
          const tagClass = mapTagClass(cat);
          const row = document.createElement('div');
          row.className = 'list-item';
          row.innerHTML = `
            <span><a href="/student/notices/${String(n.id)}">${escapeHtml(n.title)}</a></span>
            <span class="tag ${tagClass}">${escapeHtml(cat)}</span>
          `;
          recentNoticesList.appendChild(row);
        });
        if (notices.length === 0) {
          const row = document.createElement('div');
          row.className = 'list-item';
          row.innerHTML = '<span>No recent notices available.</span>';
          recentNoticesList.appendChild(row);
        }
      }
      if (myQuestionsList) {
        myQuestionsList.innerHTML = '';
        myFaqs.forEach(q => {
          const statusClass = (String(q.status).toLowerCase() === 'answered') ? 'answered' : 'pending';
          const row = document.createElement('div');
          row.className = 'list-item';
          row.innerHTML = `
            <span>${escapeHtml(q.question)}</span>
            <span class="status ${statusClass}">${capitalize(statusClass)}</span>
          `;
          myQuestionsList.appendChild(row);
        });
        if (myFaqs.length === 0) {
          const row = document.createElement('div');
          row.className = 'list-item';
          row.innerHTML = '<span>You have not asked any questions yet.</span>';
          myQuestionsList.appendChild(row);
        }
      }
      if (profile) {
        const nameEl = profile.querySelector('strong');
        const idEl = profile.querySelector('span');
        if (nameEl) nameEl.textContent = u.name || '';
        if (idEl) idEl.textContent = u.enrollment_no || '';
      }
      if (summary) {
        const divs = summary.querySelectorAll('div');
        if (divs[0]) {
          const strong = divs[0].querySelector('strong');
          if (strong) strong.textContent = (u.department ? `B.Tech ${u.department}` : 'B.Tech');
        }
        if (divs[1]) {
          const strong = divs[1].querySelector('strong');
          if (strong) strong.textContent = formatYear(u.year);
        }
        if (divs[2]) {
          const strong = divs[2].querySelector('strong');
          if (strong) strong.textContent = u.status || 'Active';
        }
      }

      // Legacy: Recent Notices
      if (recentPanel) {
        const list = recentPanel.querySelector('.list');
        if (list) {
          list.innerHTML = '';
          notices.forEach(n => {
            const cat = n.category || 'Academic';
            const tagClass = mapTagClass(cat);
            const item = document.createElement('div');
            item.className = 'item notice';
            item.innerHTML = `
              <p>${escapeHtml(n.title)}</p>
              <span class="tag ${tagClass}">${escapeHtml(cat)}</span>
              <a href="/student/student_notices.html">View</a>
            `;
            list.appendChild(item);
          });
          if (notices.length === 0) {
            const item = document.createElement('div');
            item.className = 'item notice';
            item.innerHTML = '<p>No recent notices available.</p>';
            list.appendChild(item);
          }
        }
      }

      // Legacy: My Questions
      if (questionsPanel) {
        const list = questionsPanel.querySelector('.list');
        if (list) {
          list.innerHTML = '';
          myFaqs.forEach(q => {
            const statusClass = (String(q.status).toLowerCase() === 'answered') ? 'answered' : 'pending';
            const item = document.createElement('div');
            item.className = 'item question';
            const actionText = (statusClass === 'answered') ? 'View' : 'Edit';
              const actionHref = (statusClass === 'answered') ? '/student/faq' : '#';
            item.innerHTML = `
              <p>${escapeHtml(q.question)}</p>
              <div class="right">
                <span class="status ${statusClass}">${capitalize(statusClass)}</span>
                <a href="${actionHref}">${actionText}</a>
              </div>
            `;
            list.appendChild(item);
          });
        }
      }
      })
      .catch(() => {});
  }

  function mapTagClass(category) {
    const c = normalize(category);
    if (c === 'academic') return 'academic';
    if (c === 'event') return 'event';
    if (c === 'administration' || c === 'admin') return 'admin';
    return 'academic';
  }
  function normalize(s) { return String(s || '').trim().toLowerCase(); }
  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
  function capitalize(s) { s = String(s || ''); return s.charAt(0).toUpperCase() + s.slice(1); }

  function formatYear(y) {
    if (!y) return '';
    const n = Number(y);
    if (!Number.isFinite(n)) return String(y);
    const suffix = (n === 1) ? 'st' : (n === 2) ? 'nd' : (n === 3) ? 'rd' : 'th';
    return `${n}${suffix}`;
  }

  load();
  // Auto-refresh every 30s
  setInterval(load, 30000);
});
