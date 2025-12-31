document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const error = params.get('error');
  const box = document.querySelector('.register-box');
  if (!box) return;
  if (error) {
    const msg = document.createElement('div');
    msg.className = 'notice';
    msg.textContent = error;
    box.insertBefore(msg, box.firstChild);
  }
});
