document.addEventListener('DOMContentLoaded', () => {
  const list = document.querySelector('.notice-list');
  const select = document.querySelector('.filters select');
  const dateInput = document.querySelector('.filters input[type="date"]');
  const applyBtn = document.querySelector('.filters button');
  const profile = document.querySelector('.student-profile');
  if (!list) return;

  let allNotices = [];

  function load() {
    // Populate header with student name and enrollment ID
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
    fetch('/api/student/notices')
      .then(res => res.json())
      .then(data => {
        if (!data || !data.ok || !Array.isArray(data.notices)) return;
        allNotices = data.notices;
        render(allNotices);
      })
      .catch(() => {});
  }

  function render(items) {
    list.innerHTML = '';
    items.forEach(n => {
      const hasAttach = Array.isArray(n.attachments) && n.attachments.length > 0;
      const cat = n.category || 'Academic';
      const tagClass = mapTagClass(cat);
      const item = document.createElement('div');
      item.className = 'notice-item';
      item.dataset.category = cat;
      item.dataset.date = n.date || '';
      item.innerHTML = `
        <span class="tag ${tagClass}">${escapeHtml(cat)}</span>
        <p>${escapeHtml(n.title)}</p>
        ${hasAttach ? '<span class="attachment" title="Attachment available">📎</span>' : ''}
        <button>View</button>
      `;
      item.querySelector('button').addEventListener('click', () => {
        openNoticeModal(n);
      });
      list.appendChild(item);
    });
  }

  function applyFilters() {
    const cat = (select && select.value) ? select.value : 'All Categories';
    const dateVal = (dateInput && dateInput.value) ? formatDate(dateInput.value) : '';
    const filtered = allNotices.filter(n => {
      const okCat = (cat === 'All Categories') || (normalize(cat) === normalize(n.category));
      const okDate = !dateVal || normalize(n.date) === normalize(dateVal);
      return okCat && okDate;
    });
    render(filtered);
  }

  if (applyBtn) applyBtn.addEventListener('click', applyFilters);

  function openNoticeModal(n) {
    const modal = document.getElementById('noticeModal');
    if (!modal) return;
    const content = modal.querySelector('.modal-content');
    content.querySelector('h2').textContent = n.title;
    content.querySelector('.modal-meta').textContent = `${n.category} · ${n.date}`;
    const pNodes = content.querySelectorAll('p');
    // Assume first long paragraph describes content
    if (pNodes && pNodes.length) pNodes[0].textContent = n.content;

    // Render attachments
    const ul = content.querySelector('.attachments');
    if (ul) {
      ul.innerHTML = '';
      (n.attachments || []).forEach(a => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = `/files/notice/${a.id}`;
        link.textContent = `📄 ${a.name}`;
        link.setAttribute('download', '');
        li.appendChild(link);
        ul.appendChild(li);
      });
    }
    modal.style.display = 'flex';
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
  function formatDate(val) {
    // Input type=date returns yyyy-mm-dd; we need 'DD Mon YYYY'
    const d = new Date(val);
    if (isNaN(d.getTime())) return '';
    const day = d.getDate().toString().padStart(2, '0');
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const mon = months[d.getMonth()];
    const year = d.getFullYear();
    return `${day} ${mon} ${year}`;
  }
  load();
  // Auto-refresh every 30s; preserve current filters
  setInterval(() => { load(); applyFilters(); }, 30000);
});
