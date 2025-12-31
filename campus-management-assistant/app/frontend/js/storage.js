// Minimal storage helper to avoid 404s
window.storage = {
  get(key, defVal = null) {
    try { const v = localStorage.getItem(key); return v !== null ? JSON.parse(v) : defVal; } catch (_) { return defVal; }
  },
  set(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (_) {} },
  remove(key) { try { localStorage.removeItem(key); } catch (_) {} },
};
