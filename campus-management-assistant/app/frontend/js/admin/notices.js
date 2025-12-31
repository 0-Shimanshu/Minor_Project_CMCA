document.addEventListener('DOMContentLoaded', () => {
  const list = document.querySelector('.notice-list');
  if (!list) return;

  function load() {
    fetch('/api/admin/notices')
      .then(r => r.json())
      .then(data => {
        if (!data || !data.ok) return;
        const items = Array.isArray(data.notices) ? data.notices : [];
        // Keep header row
        const headerRow = list.querySelector('.header-row');
        list.innerHTML = '';
        if (headerRow) list.appendChild(headerRow.cloneNode(true));
        items.forEach(n => {
          const row = document.createElement('div');
          row.className = 'notice-row';
          row.setAttribute('data-id', n.id);
          const isDraft = String(n.status).toLowerCase() === 'draft';
          const statusCls = isDraft ? 'draft' : 'published';
          row.innerHTML = `
            <span>${escapeHtml(n.title || '')}</span>
            <span>${escapeHtml(n.category || 'General')}</span>
            <span class="status ${statusCls}">${escapeHtml(n.status)}</span>
            <span>${escapeHtml(n.visibility || 'public')}</span>
            <span class="actions">
              <button class="btn-secondary" data-action="edit">Edit</button>
              ${isDraft ? '<button class="btn-primary" data-action="publish">Publish</button>' : ''}
              <button class="btn-delete" data-action="delete">Delete</button>
            </span>
          `;
          list.appendChild(row);
        });
        wireActions();
      })
      .catch(() => {});
  }

  function wireActions() {
    // Edit
    list.querySelectorAll('[data-action="edit"]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.closest('.notice-row')?.getAttribute('data-id');
        if (!id) return;
        await openEdit(id);
      });
    });
    list.querySelectorAll('[data-action="publish"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.notice-row')?.getAttribute('data-id');
        if (!id) return;
        fetch(`/api/admin/notices/${id}/publish`, { method: 'POST' })
          .then(r => r.json())
          .then(data => {
            if (data && data.ok) {
              toast && toast.show && toast.show('Notice published', 'success');
              load();
              if (window.api && api.emitChange) api.emitChange('notices', { id });
            } else {
              toast && toast.show && toast.show('Publish failed', 'error');
            }
          })
          .catch(() => { toast && toast.show && toast.show('Error publishing', 'error'); });
      });
    });
    list.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.closest('.notice-row')?.getAttribute('data-id');
        if (!id) return;
        if (!confirm('Delete this notice?')) return;
        fetch(`/api/admin/notices/${id}/delete`, { method: 'POST' })
          .then(r => r.json())
          .then(data => {
            if (data && data.ok) {
              toast && toast.show && toast.show('Notice deleted', 'success');
              load();
              if (window.api && api.emitChange) api.emitChange('notices', { id });
            } else {
              toast && toast.show && toast.show('Delete failed', 'error');
            }
          })
          .catch(() => { toast && toast.show && toast.show('Error deleting', 'error'); });
      });
    });
  }

  // Modal helpers for Create/Edit
  function show(id){ const el = document.getElementById(id); if(el) el.classList.add('show'); }
  function hide(id){ const el = document.getElementById(id); if(el) el.classList.remove('show'); }
  function openCreateModal(){
    show('createModal');
    // clear fields
    const f = (id)=>document.getElementById(id);
    ['c_title','c_summary','c_content','c_target_department'].forEach(i=>{ const el=f(i); if(el) el.value=''; });
    ['c_category','c_visibility','c_target_year'].forEach(i=>{ const el=f(i); if(el) el.value=''; });
    const pub=f('c_publish_now'); if(pub) pub.checked=false; const no=f('c_notify'); if(no) no.checked=false;
    const file=f('c_file'); if(file) file.value='';
  }
  window.openCreateModal = openCreateModal;
  function closeModal(id){ hide(id); }
  window.closeModal = closeModal;

  async function submitCreate(publishNow){
    const f = (id)=>document.getElementById(id);
    const title = f('c_title')?.value?.trim();
    const summary = f('c_summary')?.value?.trim();
    const content = f('c_content')?.value?.trim();
    const category = f('c_category')?.value || 'General';
    const visibility = f('c_visibility')?.value || 'public';
    const target_department = f('c_target_department')?.value?.trim();
    const target_year = f('c_target_year')?.value;
    const notify = f('c_notify')?.checked;
    const file = f('c_file')?.files?.[0];
    if(!title || !content){
      toast && toast.show && toast.show('Title and content are required','error');
      return;
    }
    const fd = new FormData();
    fd.append('title', title);
    fd.append('summary', summary || '');
    fd.append('content', content);
    fd.append('category', category);
    fd.append('visibility', visibility);
    if(target_department) fd.append('target_department', target_department);
    if(target_year) fd.append('target_year', target_year);
    if(file) fd.append('file', file);
    if(publishNow || f('c_publish_now')?.checked){ fd.append('publish_now','1'); }
    if(notify){ fd.append('notify','1'); }
    try{
      const res = await fetch('/admin/notices/create', { method:'POST', body: fd });
      if(res.ok){
        toast && toast.show && toast.show('Notice created','success');
        closeModal('createModal');
        load();
        if (window.api && api.emitChange) api.emitChange('notices', { action: 'create' });
      }else{
        toast && toast.show && toast.show('Failed to create','error');
      }
    }catch(e){ toast && toast.show && toast.show('Network error','error'); }
  }
  window.submitCreate = submitCreate;

  async function openEdit(id){
    try{
      const r = await fetch(`/api/admin/notices/${id}`);
      const data = await r.json();
      if(!data || !data.ok){ throw new Error(); }
      const n = data.notice;
      const f = (i)=>document.getElementById(i);
      f('e_id').value = id;
      f('e_title').value = n.title || '';
      f('e_summary').value = n.summary || '';
      f('e_content').value = n.content || '';
      f('e_visibility').value = n.visibility || 'public';
      f('e_target_department').value = n.target_department || '';
      f('e_target_year').value = n.target_year != null ? String(n.target_year) : '';
      // Render attachments
      const box = f('e_attachments');
      box.innerHTML = '';
      (n.attachments||[]).forEach(a => {
        const row = document.createElement('div');
        row.className = 'attachment-row';
        const attachmentSpan = document.createElement('span');
        attachmentSpan.textContent = a.name || 'Attachment';
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn-delete';
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', async (e) => {
          e.preventDefault();
          if(!confirm('Delete this attachment?')) return;
          try{
            const res = await fetch(`/api/admin/notices/${id}/attachments/${a.id}/delete`, { method: 'POST' });
            const d = await res.json();
            if(d && d.ok){
              toast && toast.show && toast.show('Attachment deleted','success');
              // Remove row from DOM
              row.remove();
            }else{
              toast && toast.show && toast.show('Delete failed','error');
            }
          }catch(e){ toast && toast.show && toast.show('Network error','error'); }
        });
        row.appendChild(attachmentSpan);
        row.appendChild(deleteBtn);
        box.appendChild(row);
      });
      show('editModal');
    }catch(e){
      toast && toast.show && toast.show('Failed to load notice','error');
    }
  }
  window.openEdit = openEdit;

  async function submitEdit(){
    const f = (i)=>document.getElementById(i);
    const id = f('e_id').value;
    const fd = new FormData();
    fd.append('title', f('e_title').value.trim());
    fd.append('summary', f('e_summary').value.trim());
    fd.append('content', f('e_content').value.trim());
    fd.append('visibility', f('e_visibility').value);
    const td = f('e_target_department').value.trim(); if(td) fd.append('target_department', td);
    const ty = f('e_target_year').value; if(ty) fd.append('target_year', ty);
    const file = f('e_file').files?.[0]; if(file) fd.append('file', file);
    try{
      const res = await fetch(`/admin/notices/${id}/edit`, { method:'POST', body: fd });
      if(res.ok){
        toast && toast.show && toast.show('Notice updated','success');
        closeModal('editModal');
        load();
        if (window.api && api.emitChange) api.emitChange('notices', { id });
      }else{
        toast && toast.show && toast.show('Update failed','error');
      }
    }catch(e){ toast && toast.show && toast.show('Network error','error'); }
  }
  window.submitEdit = submitEdit;

  async function deleteNoticeFromEdit(){
    const id = document.getElementById('e_id').value;
    if(!id) return;
    if(!confirm('Delete this notice?')) return;
    try{
      const r = await fetch(`/api/admin/notices/${id}/delete`, { method: 'POST' });
      const d = await r.json().catch(()=>({ok:false}));
      if(d && d.ok){
        toast && toast.show && toast.show('Notice deleted','success');
        closeModal('editModal');
        load();
        if (window.api && api.emitChange) api.emitChange('notices', { id });
      }else{
        toast && toast.show && toast.show('Delete failed','error');
      }
    }catch(e){ toast && toast.show && toast.show('Network error','error'); }
  }
  window.deleteNoticeFromEdit = deleteNoticeFromEdit;

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
  if (window.api && api.onChange) api.onChange('notices', load);
  if (window.api && api.refreshOnFocus) api.refreshOnFocus(load);
});
