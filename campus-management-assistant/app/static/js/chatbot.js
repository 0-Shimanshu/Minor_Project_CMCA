// Simple chatbot client-side behavior for student/guest pages
(function(){
  function $(sel){ return document.querySelector(sel); }
  function appendMessage(container, text, who){
    const bubble = document.createElement('div');
    bubble.className = 'bubble ' + (who === 'user' ? 'user' : 'bot');
    bubble.textContent = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }
  function setLoading(state){
    const btn = $('#sendBtn');
    if (!btn) return;
    btn.disabled = state;
    btn.textContent = state ? 'Sending…' : 'Send';
  }
  function showTyping(container){
    const t = document.createElement('div');
    t.className = 'typing';
    t.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    container.appendChild(t);
    container._typing = t;
    container.scrollTop = container.scrollHeight;
  }
  function hideTyping(container){
    const t = container._typing;
    if (t && t.parentNode){ t.parentNode.removeChild(t); }
    container._typing = null;
  }
  function updateStatus(){
    const el = $('#chatStatus');
    if (!el) return;
    el.textContent = 'Checking…';
    fetch('/chatbot/health').then(function(r){ return r.json(); })
      .then(function(h){
        const ready = !!(h && h.ready);
        el.textContent = ready ? 'Ready' : 'Offline';
        el.classList.remove('ok','bad');
        el.classList.add(ready ? 'ok' : 'bad');
      })
      .catch(function(){ el.textContent = 'Offline'; el.classList.add('bad'); });
  }

  document.addEventListener('DOMContentLoaded', function(){
    const form = $('#chatForm');
    const input = $('#chatInput');
    const messages = $('#messages');
    if (!form || !input || !messages) return;
    updateStatus();

    form.addEventListener('submit', function(ev){
      ev.preventDefault();
      const q = (input.value || '').trim();
      if (!q) return;
      appendMessage(messages, q, 'user');
      input.value = '';
      setLoading(true);
      showTyping(messages);
      fetch('/chatbot/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q })
      }).then(function(r){ return r.json(); })
        .then(function(res){
          const ans = (res && res.answer) ? res.answer : 'Sorry, an error occurred.';
          hideTyping(messages);
          appendMessage(messages, ans, 'bot');
        })
        .catch(function(){
          hideTyping(messages);
          appendMessage(messages, 'Sorry, an error occurred.', 'bot');
        })
        .finally(function(){ setLoading(false); });
    });

    input.addEventListener('keydown', function(ev){
      if (ev.key === 'Enter' && !ev.shiftKey){
        ev.preventDefault();
        form.dispatchEvent(new Event('submit'));
      }
    });
  });
})();
