document.addEventListener('DOMContentLoaded', () => {
  const chatArea = document.getElementById('chatArea');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  if (!chatArea || !userInput || !sendBtn) return;

  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  });

  function appendMessage(text, who) {
    const div = document.createElement('div');
    div.className = `message ${who}`;
    div.textContent = text;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    appendMessage(text, 'user');
    userInput.value = '';

    // Optional: typing indicator (unstyled)
    const typing = document.createElement('div');
    typing.className = 'message bot';
    typing.textContent = '…';
    chatArea.appendChild(typing);
    chatArea.scrollTop = chatArea.scrollHeight;

    fetch('/chatbot/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text })
    })
      .then(r => r.json())
      .then(data => {
        typing.remove();
        if (data && data.ok) {
          appendMessage(data.answer, 'bot');
        } else {
          appendMessage('Sorry, I could not answer that.', 'bot');
        }
      })
      .catch(() => {
        typing.remove();
        appendMessage('Sorry, an error occurred.', 'bot');
      });
  }
});
