document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const error = params.get('error');
  const registered = params.get('registered');
  const box = document.querySelector('.login-box');
  if (!box) return;
  if (error || registered) {
    const msg = document.createElement('div');
    msg.className = 'notice';
    msg.textContent = error ? error : 'Registration successful. Please log in.';
    box.insertBefore(msg, box.firstChild);
  }
});
