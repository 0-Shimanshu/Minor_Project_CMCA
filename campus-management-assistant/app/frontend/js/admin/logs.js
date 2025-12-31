document.addEventListener('DOMContentLoaded', () => {
  const logList = document.querySelector('.log-list');
  const searchInput = document.querySelector('.filter-bar input');
  const typeFilter = document.querySelector('.filter-bar select');

  let allLogs = [];

  function loadLogs() {
    Promise.all([
      fetch('/api/admin/logs')
        .then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .catch(err => {
          console.error('Load logs error:', err);
          return { ok: false };
        }),
      fetch('/api/admin/scraper/logs')
        .then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .catch(err => {
          console.error('Load scraper logs error:', err);
          return { ok: false };
        })
    ])
      .then(([data1, data2]) => {
        // System and email logs
        const systemLogs = data1 && data1.ok && Array.isArray(data1.system) 
          ? data1.system.map(l => ({
              type: 'system',
              message: l.message || '',
              level: 'INFO',
              timestamp: l.timestamp || '',
              _sortTime: parseDateToMs(l.timestamp)
            }))
          : [];

        const emailLogs = data1 && data1.ok && Array.isArray(data1.emails)
          ? data1.emails.map(l => ({
              type: 'email',
              message: `${l.subject || ''} → ${l.to || ''}`,
              level: l.status === 'sent' ? 'INFO' : 'ERROR',
              timestamp: l.timestamp || '',
              _sortTime: parseDateToMs(l.timestamp)
            }))
          : [];

        // Scraper logs
        const scraperLogs = data2 && data2.ok && Array.isArray(data2.logs)
          ? data2.logs.map(l => ({
              type: 'scraper',
              message: `${l.status || ''} · text: ${l.extracted_text_length || '0'} · pdfs: ${l.pdf_links_found || '0'}`,
              level: l.status === 'success' ? 'INFO' : 'WARNING',
              timestamp: l.scraped_at || '',
              _sortTime: parseDateToMs(l.scraped_at)
            }))
          : [];

        // Combine and sort by timestamp (newest first)
        allLogs = [...systemLogs, ...emailLogs, ...scraperLogs]
          .sort((x, y) => y._sortTime - x._sortTime);

        renderLogs(allLogs);
      })
      .catch(err => {
        console.error('Load logs error:', err);
        if (toast && toast.show) toast.show('Network error loading logs', 'error');
      });
  }

  function renderLogs(logs) {
    // Clear all rows except header
    const headerRow = logList.querySelector('.header-row');
    logList.innerHTML = '';
    logList.appendChild(headerRow.cloneNode(true));

    logs.forEach(log => {
      const row = document.createElement('div');
      row.className = 'log-row';

      const typeClass = log.type.toLowerCase();
      const levelClass = log.level.toLowerCase();
      const message = escapeHtml(log.message);
      const level = escapeHtml(log.level);
      const timestamp = escapeHtml(log.timestamp);

      row.innerHTML = `
        <span class="type ${typeClass}">${escapeHtml(log.type.toUpperCase())}</span>
        <span>${message}</span>
        <span class="level ${levelClass}">${level}</span>
        <span>${timestamp}</span>
      `;
      logList.appendChild(row);
    });

    if (logs.length === 0) {
      const emptyRow = document.createElement('div');
      emptyRow.className = 'log-row';
      emptyRow.style.textAlign = 'center';
      emptyRow.style.color = '#9ca3af';
      emptyRow.textContent = 'No logs to display';
      logList.appendChild(emptyRow);
    }
  }

  function filterLogs() {
    const searchTerm = (searchInput?.value || '').toLowerCase();
    const selectedType = typeFilter?.value || 'all';

    const filtered = allLogs.filter(log => {
      const matchType = selectedType === 'all' || log.type === selectedType;
      const matchSearch = !searchTerm || 
        (log.message || '').toLowerCase().includes(searchTerm);
      return matchType && matchSearch;
    });

    renderLogs(filtered);
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function parseDateToMs(dateStr) {
    try {
      const t = Date.parse(dateStr);
      return Number.isFinite(t) ? t : 0;
    } catch (e) {
      return 0;
    }
  }

  // Event listeners
  if (searchInput) {
    searchInput.addEventListener('input', filterLogs);
  }
  if (typeFilter) {
    typeFilter.addEventListener('change', filterLogs);
  }

  // Initial load
  loadLogs();

  // Auto-refresh every 30s
  setInterval(loadLogs, 30000);
  if (window.api && api.onChange) api.onChange('logs', loadLogs);
  if (window.api && api.refreshOnFocus) api.refreshOnFocus(loadLogs);
});
