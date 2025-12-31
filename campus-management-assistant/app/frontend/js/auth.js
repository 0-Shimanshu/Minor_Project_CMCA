// Minimal auth stub; pages guard usage
window.auth = {
  requireAuth(roles) {
    // No-op stub; backend routes enforce auth and roles
    return true;
  }
};
