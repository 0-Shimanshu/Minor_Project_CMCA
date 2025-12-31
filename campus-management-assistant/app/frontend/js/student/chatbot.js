document.addEventListener('DOMContentLoaded', () => {
  if (typeof auth !== 'undefined' && auth.requireAuth) {
    try { auth.requireAuth(['student']); } catch (_) {}
  }

  const chat = document.getElementById('chatMessages');
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  if (!chat || !input || !sendBtn) return;

  // Initial greeting ensures UI renders predictably
  appendMessage('Hi! Ask me anything about notices, FAQs, or campus info.', 'bot');

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      sendMessage();
    }
  });

  function appendMessage(text, sender) {
    const msg = document.createElement('div');
    // Match CSS: .message.user / .message.bot and inner .bubble
    const cls = (sender === 'user') ? 'user' : 'bot';
    msg.className = `message ${cls}`;
    msg.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
  }

  function showTyping() {
    const typing = document.createElement('div');
    typing.id = 'typingIndicator';
    typing.className = 'message bot';
    typing.innerHTML = `<div class="bubble">Thinking...</div>`;
    chat.appendChild(typing);
    chat.scrollTop = chat.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
  }

  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    appendMessage(text, 'user');
    input.value = '';
    showTyping();
    const post = (window.api && typeof window.api.post === 'function')
      ? (url, body) => window.api.post(url, body, { scope: 'chatbot' })
      : (url, body) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body||{}) })
          .then(async r => {
            try { return await r.json(); } catch(_) { return { ok: r.ok }; }
          });

    post('/chatbot/query', { query: text })
      .then(data => {
        removeTyping();
        if (data && data.ok) {
          appendMessage(data.answer || ' ', 'bot');
          // Optional: show confidence bar if provided by backend
          if (typeof data.confidence === 'number') {
            const last = chat.lastElementChild;
            if (last && last.classList.contains('bot')) {
              const conf = document.createElement('div');
              conf.className = 'confidence';
              const pct = Math.max(0, Math.min(100, data.confidence));
              conf.innerHTML = `<div class="bar" style="width: ${pct}%;"></div><span>Confidence: ${pct}%</span>`;
              last.appendChild(conf);
            }
          }
        } else {
          appendMessage('Sorry, I could not answer that.', 'bot');
        }
      })
      .catch(() => {
        removeTyping();
        appendMessage('Sorry, an error occurred.', 'bot');
      });
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
