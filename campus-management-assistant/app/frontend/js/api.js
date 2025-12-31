// Minimal API + change events
(function(){
  // Global auto-refresh on successful non-GET fetches (skips chatbot endpoints)
  try {
    const originalFetch = window.fetch.bind(window);
    let reloadScheduled = false;
    function shouldSkip(url){
      try{
        const u = new URL((url||''), window.location.origin);
        const path = u.pathname || '';
        return /chatbot/i.test(path);
      }catch(_){ return false; }
    }
    function isSameOrigin(url){
      try{
        if (!url) return true;
        const u = new URL(url, window.location.origin);
        return u.origin === window.location.origin;
      }catch(_){ return true; }
    }
    window.fetch = async function(input, init){
      const method = ((init && init.method) || (input && input.method) || 'GET').toString().toUpperCase();
      const url = (typeof input === 'string') ? input : (input && input.url) || '';
      const res = await originalFetch(input, init);
      try{
        if (method !== 'GET' && res && res.ok && isSameOrigin(url) && !shouldSkip(url)){
          if (!reloadScheduled){
            reloadScheduled = true;
            setTimeout(()=>{ try{ location.reload(); }catch(_){} }, 0);
          }
        }
      }catch(_){}
      return res;
    };
  } catch (_){ /* no-op */ }

  const CHANGE_EVENT = 'data:changed';
  function emitChange(scope, detail){
    try { window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: { scope: scope||'*', ...(detail||{}) } })); } catch(_) {}
  }
  function onChange(scope, handler){
    window.addEventListener(CHANGE_EVENT, (e)=>{
      const s = (e.detail && e.detail.scope) || '*';
      if (!scope || scope === '*' || scope === s) handler(e.detail||{});
    });
  }
  function refreshOnFocus(fn){
    if (typeof fn !== 'function') return;
    window.addEventListener('visibilitychange', ()=>{ if (!document.hidden) fn(); });
    window.addEventListener('focus', fn);
  }
  window.api = {
    get(url) {
      return fetch(url).then(r => r.json());
    },
    post(url, body, opts) {
      return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body||{}) })
        .then(async r => {
          const data = await r.json().catch(()=>({ ok: r.ok }));
          if (r.ok && (data == null || data.ok !== false)) {
            emitChange((opts && opts.scope) || '*', { url, body });
          }
          return data;
        });
    },
    emitChange,
    onChange,
    refreshOnFocus,
  };
})();
