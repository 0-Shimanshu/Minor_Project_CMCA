document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('.notice-container');
  const searchInput = document.getElementById('searchInput');
  const categoryFilter = document.getElementById('categoryFilter');
  if (!container) return;

  let allNotices = [];

  fetch('/api/guest/notices')
    .then(res => res.json())
    .then(data => {
      if (!data || !data.ok || !Array.isArray(data.notices)) return;
      allNotices = data.notices;
      // Expose for filter function using window reference
      window.allNotices = allNotices;
      render(allNotices);
      wireFilters();
    })
    .catch(() => {
      // Leave dummy content if fetch fails
    });
  // Auto-refresh every 30s; preserve current filters
  setInterval(() => {
    fetch('/api/guest/notices')
      .then(res => res.json())
      .then(data => {
        if (!data || !data.ok || !Array.isArray(data.notices)) return;
        allNotices = data.notices;
        window.allNotices = allNotices;
        const term = (searchInput && searchInput.value || '').toLowerCase();
        const cat = (categoryFilter && categoryFilter.value) || 'all';
        const filtered = (window.allNotices || []).filter(n => {
          const matchesText = (n.title || '').toLowerCase().includes(term) || (n.content || '').toLowerCase().includes(term);
          const matchesCat = cat === 'all' || String(n.category || '').toLowerCase() === String(cat).toLowerCase();
          return matchesText && matchesCat;
        });
        render(filtered);
      })
      .catch(() => {});
  }, 30000);
});

function mapBadgeClass(category) {
  const c = String(category || '').toLowerCase();
  if (c === 'academic') return 'academic';
  if (c === 'event') return 'event';
  if (c === 'administration' || c === 'admin') return 'admin';
  return 'academic';
}

function truncate(text, max) {
  const t = String(text || '');
  return t.length > max ? t.slice(0, max - 1) + '…' : t;
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function render(items) {
  const container = document.querySelector('.notice-container');
  if (!container) return;
  container.innerHTML = '';
  items.forEach(n => {
    const cat = n.category || 'Academic';
    const badgeClass = mapBadgeClass(cat);
    const dateStr = n.date || '';
    const summary = (n.summary && n.summary.trim()) ? n.summary : truncate(n.content, 140);
    const item = document.createElement('div');
    item.className = 'notice-item';
    item.dataset.category = cat;
    item.innerHTML = `
      <div class="notice-left">
        <div class="notice-top">
          <span class="badge ${badgeClass}">${escapeHtml(cat)}</span>
          <span class="date">${escapeHtml(dateStr)}</span>
        </div>
        <h3>${escapeHtml(n.title)}</h3>
        <p>${escapeHtml(summary)}</p>
      </div>
      <div class="notice-right">
        <button>View</button>
      </div>`;
    item.querySelector('button').addEventListener('click', () => {
      openNotice(n.title, cat, dateStr, n.content);
    });
    container.appendChild(item);
  });
}

function wireFilters() {
  const searchInput = document.getElementById('searchInput');
  const categoryFilter = document.getElementById('categoryFilter');
  if (searchInput) searchInput.addEventListener('input', applyFilters);
  if (categoryFilter) categoryFilter.addEventListener('change', applyFilters);

  function applyFilters() {
    const term = (searchInput && searchInput.value || '').toLowerCase();
    const cat = (categoryFilter && categoryFilter.value) || 'all';
    const filtered = (window.allNotices || []).filter(n => {
      const matchesText = (n.title || '').toLowerCase().includes(term) || (n.content || '').toLowerCase().includes(term);
      const matchesCat = cat === 'all' || String(n.category || '').toLowerCase() === String(cat).toLowerCase();
      return matchesText && matchesCat;
    });
    render(filtered);
  }
}

function openNotice(title, tag, date, body) {
  document.getElementById('modalTitle').innerText = title;
  document.getElementById('modalTag').innerText = tag;
  document.getElementById('modalDate').innerText = date;
  document.getElementById('modalBody').innerText = body;
  document.getElementById('noticeModal').style.display = 'flex';
}

function closeNotice() {
  document.getElementById('noticeModal').style.display = 'none';
}
