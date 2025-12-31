(function(){
  const params = new URLSearchParams(location.search);
  const noticeId = params.get('id');
  if(!noticeId){
    alert('Missing notice id');
    location.href = '/admin/admin_notices.html';
    return;
  }

  const form = document.getElementById('editForm');
  const title = document.getElementById('title');
  const summary = document.getElementById('summary');
  const content = document.getElementById('content');
  const visibility = document.getElementById('visibility');
  const targetDepartment = document.getElementById('target_department');
  const targetYear = document.getElementById('target_year');
  const attachments = document.getElementById('attachments');

  function renderAttachments(list){
    attachments.innerHTML = '';
    if(!list || list.length === 0){
      attachments.innerHTML = '<em>No attachments</em>';
      return;
    }
    list.forEach(a => {
      const row = document.createElement('div');
      row.className = 'attachment-row';
      const link = document.createElement('a');
      link.href = a.url || a.path || '#';
      link.textContent = a.name || a.filename || 'Attachment';
      link.target = '_blank';
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'btn-danger-outline';
      remove.textContent = 'Remove';
      remove.addEventListener('click', async () => {
        try{
          const res = await fetch(`/admin/notices/${noticeId}/attachments/${a.id}/delete`, { method: 'POST' });
          const data = await res.json().catch(()=>({ok:false}));
          if(data && data.ok){
            row.remove();
          }else{
            alert('Failed to remove attachment');
          }
        }catch(err){
          alert('Failed to remove attachment');
        }
      });
      row.appendChild(link);
      row.appendChild(remove);
      attachments.appendChild(row);
    });
  }

  async function load(){
    try{
      const res = await fetch(`/api/admin/notices/${noticeId}`);
      const data = await res.json();
      if(!data || !data.ok){
        throw new Error('Not found');
      }
      const n = data.notice || data.data || data;
      title.value = n.title || '';
      summary.value = n.summary || '';
      content.value = n.content || '';
      visibility.value = n.visibility || 'public';
      targetDepartment.value = n.target_department || '';
      targetYear.value = (n.target_year!=null ? String(n.target_year) : '');
      renderAttachments(n.attachments || []);
      form.action = `/admin/notices/${noticeId}/edit`;
    }catch(err){
      alert('Failed to load notice');
      location.href = '/admin/admin_notices.html';
    }
  }

  form.addEventListener('submit', function(){
    // allow native form submit
    setTimeout(()=>{
      const url = new URL(location.href);
      url.searchParams.set('updated','1');
      history.replaceState(null,'',url.toString());
    }, 0);
  });

  load();
})();
