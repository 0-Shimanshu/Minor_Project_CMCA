document.addEventListener('DOMContentLoaded', () => {
  const list = document.querySelector('.scraper-list');
  const addModal = document.getElementById('addModal');
  const previewModal = document.getElementById('previewModal');
  const previewContainer = document.getElementById('previewContainer');
  const indicator = document.getElementById('scrapeIndicator');
  const btnRunAllTop = document.getElementById('btnRunAllTop');
  if (!list) return;
  function setIndicator(text, show) {
    if (!indicator) return;
    indicator.textContent = text || 'Running…';
    indicator.style.display = show ? 'inline' : 'none';
  }
  function disableRunButtons(disabled) {
    const buttons = list.querySelectorAll('[data-action="run"]');
    buttons.forEach(b => { b.disabled = !!disabled; b.classList.toggle('is-disabled', !!disabled); });
    if (btnRunAllTop) { btnRunAllTop.disabled = !!disabled; }
  }

  function loadSites() {
    fetch('/api/admin/scraper/sites')
      .then(r => r.json())
      .then(data => {
        if (!data || !data.ok) return;
        const sites = Array.isArray(data.sites) ? data.sites : [];
        list.innerHTML = sites.map(siteHtml).join('');
        wireActions();
      })
      .catch(() => {});
  }

  // Run all sources
  window.runAllScrapers = function(){
    setIndicator('Running all sources…', true);
    disableRunButtons(true);
    fetch('/api/admin/scraper/run-all', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        const ok = d && d.ok;
        const completed = d && d.completed;
        const total = d && d.total;
        toast && toast.show && toast.show(ok ? `Run all completed (${completed}/${total})` : 'Run all failed', ok ? 'success' : 'error');
        // Show latest logs after a short delay
        setTimeout(() => openPreviewForSite(null), 500);
      })
      .catch(() => { toast && toast.show && toast.show('Run all error', 'error'); })
      .finally(() => { disableRunButtons(false); setTimeout(() => setIndicator('', false), 800); });
  };

  function siteHtml(s) {
    return `
      <div class="scraper-item" data-id="${s.id}">
        <div class="scraper-info">
          <h3>${escapeHtml(s.url)}</h3>
          <p class="meta">Added: ${escapeHtml(s.added_at || '')}</p>
        </div>
        <div class="scraper-status ${s.enabled ? 'enabled' : 'disabled'}">${s.enabled ? 'ENABLED' : 'DISABLED'}</div>
        <div class="scraper-actions">
          <button class="btn-primary" data-action="run">Run Now</button>
          <button class="btn-secondary" data-action="logs">Logs</button>
          <button class="btn-secondary" data-action="toggle">${s.enabled ? 'Disable' : 'Enable'}</button>
          <button class="btn-delete" data-action="delete">Delete</button>
        </div>
      </div>`;
  }

  function wireActions() {
    list.querySelectorAll('[data-action="run"]').forEach(btn => {
      const id = btn.closest('.scraper-item')?.getAttribute('data-id');
      btn.addEventListener('click', () => {
        // Mark running state for this item
        const item = btn.closest('.scraper-item');
        const statusEl = item && item.querySelector('.scraper-status');
        const prevText = statusEl ? statusEl.textContent : '';
        if (statusEl) { statusEl.textContent = 'RUNNING…'; statusEl.classList.add('running'); }
        btn.disabled = true;
        setIndicator('Running scraper…', true);
        fetch(`/api/admin/scraper/sites/${id}/run`, { method: 'POST' })
          .then(r => r.json())
          .then(d => {
            const label = d.ok ? 'success' : (d.status === 'disabled' ? 'disabled' : 'failed');
            toast && toast.show && toast.show(`Run ${label}`, d.ok ? 'success' : 'error');
            // Show latest logs for this source
            openPreviewForSite(id);
            if (window.api && api.emitChange) api.emitChange('scraper', { id });
            // Reflect disabled state explicitly
            if (!d.ok && d.status === 'disabled' && statusEl) {
              statusEl.textContent = 'DISABLED';
              statusEl.classList.remove('enabled');
              statusEl.classList.add('disabled');
            }
          })
          .catch(() => { toast && toast.show && toast.show('Run error', 'error'); })
          .finally(() => {
            if (statusEl) { statusEl.textContent = prevText || 'ENABLED'; statusEl.classList.remove('running'); }
            btn.disabled = false;
            setTimeout(() => setIndicator('', false), 600);
          });
      });
    });
    list.querySelectorAll('[data-action="delete"]').forEach(btn => {
      const id = btn.closest('.scraper-item')?.getAttribute('data-id');
      btn.addEventListener('click', () => {
        if (!confirm('Delete this source?')) return;
        fetch(`/api/admin/scraper/sites/${id}/delete`, { method: 'POST' })
          .then(r => r.json())
          .then(d => { if (d && d.ok) { loadSites(); toast && toast.show && toast.show('Source deleted', 'success'); if (window.api && api.emitChange) api.emitChange('scraper', { id }); } });
      });
    });
    list.querySelectorAll('[data-action="logs"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.scraper-item')?.getAttribute('data-id');
        openPreviewForSite(id);
      });
    });
    list.querySelectorAll('[data-action="toggle"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const item = btn.closest('.scraper-item');
        const id = item?.getAttribute('data-id');
        const statusEl = item?.querySelector('.scraper-status');
        const prevBtnText = (btn.textContent || '').trim();
        const intentEnable = /^enable$/i.test(prevBtnText);
        const url = intentEnable ? `/api/admin/scraper/sites/${id}/enable` : `/api/admin/scraper/sites/${id}/disable`;

        // Optimistic UI: show working state
        btn.disabled = true;
        btn.textContent = intentEnable ? 'Enabling…' : 'Disabling…';

        fetch(url, { method: 'POST' })
          .then(r => r.json())
          .then(d => {
            if (d && d.ok) {
              // Update status label and classes
              if (statusEl) {
                statusEl.textContent = intentEnable ? 'ENABLED' : 'DISABLED';
                // Reset classes then add the correct one to avoid stale state
                statusEl.classList.remove('enabled', 'disabled');
                statusEl.classList.add(intentEnable ? 'enabled' : 'disabled');
                // Fallback inline color in case CSS fails to apply
                statusEl.style.color = intentEnable ? '#10b981' : '#f87171';
              }
              // Update button label to next action
              btn.textContent = intentEnable ? 'Disable' : 'Enable';
              toast && toast.show && toast.show(intentEnable ? 'Source enabled' : 'Source disabled', 'success');
              if (window.api && api.emitChange) api.emitChange('scraper', { id });
              // Optional: reload to sync other fields
              setTimeout(loadSites, 200);
            } else {
              btn.textContent = prevBtnText;
              toast && toast.show && toast.show('Toggle failed', 'error');
            }
          })
          .catch(() => { btn.textContent = prevBtnText; toast && toast.show && toast.show('Toggle error', 'error'); })
          .finally(() => { btn.disabled = false; });
      });
    });
  }

  if (window.api && api.refreshOnFocus) api.refreshOnFocus(loadSites);

  // Add source via modal (simple binding)
  window.openAddModal = function() { if (addModal) addModal.style.display = 'flex'; };
  window.closeModal = function(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; };

  const saveBtn = (addModal && addModal.querySelector('.btn-primary')) || null;
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      const nameInput = addModal.querySelector('#sourceName');
      const urlInput = addModal.querySelector('#sourceUrl');
      const name = (nameInput && nameInput.value || '').trim();
      const url = (urlInput && urlInput.value || '').trim();
      if (!url) { toast && toast.show && toast.show('URL is required', 'error'); return; }
      fetch('/api/admin/scraper/sites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, name })
      })
        .then(r => r.json())
        .then(d => {
          if (d && d.ok) {
            toast && toast.show && toast.show('Source added', 'success');
            closeModal('addModal');
            loadSites();
          } else {
            toast && toast.show && toast.show('Add failed', 'error');
          }
        });
    });
  }

  function openPreviewForSite(siteId) {
    fetch('/api/admin/scraper/logs')
      .then(r => r.json())
      .then(d => {
        const logs = Array.isArray(d.logs) ? d.logs : [];
        const filtered = (siteId == null) ? logs : logs.filter(l => String(l.website_id) === String(siteId));
        if (previewContainer) {
          if (!filtered.length) {
            previewContainer.innerHTML = '<div class="preview-logs-container"><p style="color:#9ca3af;padding:20px;text-align:center;">No logs for this source yet.</p></div>';
          } else {
            previewContainer.innerHTML = '<div class="preview-logs-container">' + filtered.map(rowHtml).join('') + '</div>';
          }
        }
        if (previewModal) previewModal.style.display = 'flex';
      })
      .catch(() => { if (previewContainer) previewContainer.innerHTML = '<div class="preview-logs-container"><p style="color:#9ca3af;padding:20px;">Error loading logs.</p></div>'; if (previewModal) previewModal.style.display = 'flex'; });
  }

  function rowHtml(l) {
    const ts = safe(l, 'scraped_at');
    const status = safe(l, 'status');
    const len = safe(l, 'extracted_text_length');
    const pdfs = safe(l, 'pdf_links_found');
    return `
      <div style="padding: 12px; border-bottom: 1px solid #1f2933;">
        <div style="display:flex; justify-content: space-between; margin-bottom:6px;">
          <span style="color:#9ca3af;">${escapeHtml(ts)}</span>
          <span class="badge ${status === 'success' ? 'badge-success' : 'badge-warning'}">${escapeHtml(status)}</span>
        </div>
        <div style="color:#9ca3af;">Extracted text length: ${escapeHtml(len)}</div>
        <div style="color:#9ca3af;">PDF links found: ${escapeHtml(pdfs)}</div>
      </div>`;
  }

  function safe(obj, key) { const v = obj && obj[key]; return v == null ? '' : String(v); }
  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  loadSites();
});
