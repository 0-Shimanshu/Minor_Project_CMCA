// Minimal UI helpers
window.toast = {
  show(msg, type) {
    console.log(`[${type||'info'}] ${msg}`);
  }
};
