document.addEventListener('DOMContentLoaded', () => {
  const listContainer = document.querySelector('.card.list');
  const openAddModBtn = document.getElementById('openAddModerator');
  const closeAddModBtn = document.getElementById('closeAddModerator');
  const addModModal = document.getElementById('addModeratorModal');
  const searchInput = document.querySelector('.filter-bar input');
  const roleFilter = document.querySelector('.filter-bar select');

  let allUsers = [];
  let currentUserId = null;
  let currentUserData = null;

  async function loadUsers() {
    // Load current user first to mark the self row
    try {
      const rDash = await fetch('/api/admin/dashboard');
      const dataDash = await rDash.json().catch(() => ({}));
      if (rDash.ok && dataDash && dataDash.user) {
        currentUserId = dataDash.user.id || null;
        currentUserData = dataDash.user;
      }
    } catch {}

    fetch('/api/admin/users')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (!data || !data.ok) {
          console.error('API error:', data);
          return;
        }
         allUsers = Array.isArray(data.users) ? data.users : [];
         // Ensure current admin/self appears in the list even if API omits admin
         if (currentUserId && !allUsers.some(u => u && u.id === currentUserId)) {
           allUsers.unshift({
             id: currentUserId,
             login_id: currentUserData?.login_id || '',
             role: currentUserData?.role || 'admin',
             status: 'active',
             name: currentUserData?.name || '',
             email: currentUserData?.email || ''
           });
         }
        renderUsers(allUsers);
      })
      .catch(err => {
        console.error('Load users error:', err);
      });
  }

  function renderUsers(users) {
    // Keep header row
    const headerRow = listContainer.querySelector('.header-row');
    listContainer.innerHTML = '';
    listContainer.appendChild(headerRow.cloneNode(true));

    // Add user rows
    users.forEach(u => {
      const row = document.createElement('div');
      const isSelf = (currentUserId && u.id === currentUserId);
      row.className = 'user-row' + (isSelf ? ' disabled' : '');
      row.setAttribute('data-id', u.id);

      const isActive = String(u.status).toLowerCase() === 'active';
      const statusClass = isActive ? 'active' : 'inactive';
      const statusText = isActive ? 'Active' : 'Inactive';
      const actionBtn = (isSelf
        ? '<span class="self">Self</span>'
        : (isActive 
          ? '<button class="btn-warning" data-action="deactivate">Deactivate</button>'
          : '<button class="btn-primary" data-action="activate">Activate</button>'));

      const loginId = String(u.login_id || '').trim();
      const roleLower = String(u.role || '').toLowerCase();
      const displayId = (loginId && !['admin','moderator','student'].includes(loginId.toLowerCase()))
        ? loginId
        : (u.enrollment_no || loginId || '');

      row.innerHTML = `
        <span>${escapeHtml(displayId)}</span>
        <span>${escapeHtml(u.role || '')}</span>
        <span class="status ${statusClass}">${statusText}</span>
        <span class="actions">
          ${actionBtn}
          ${isSelf ? '' : '<button class="btn-delete" data-action="delete">Delete</button>'}
        </span>
      `;
      listContainer.appendChild(row);
    });

    wireActions();
  }

  function wireActions() {
    listContainer.querySelectorAll('[data-action="activate"]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const row = btn.closest('.user-row');
        const id = row.getAttribute('data-id');
        if (!id) return;
        try {
          const res = await fetch(`/api/admin/users/${id}/activate`, { method: 'POST' });
          const data = await res.json().catch(() => ({ ok: false }));
          if (res.ok && data && data.ok) {
            loadUsers();
          } else {
            alert(data?.message || 'Failed to activate user');
          }
        } catch (err) {
          console.error('Activate error:', err);
          alert('Network error');
        }
      });
    });

    listContainer.querySelectorAll('[data-action="deactivate"]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const row = btn.closest('.user-row');
        const id = row.getAttribute('data-id');
        if (!id) return;
        try {
          const res = await fetch(`/api/admin/users/${id}/deactivate`, { method: 'POST' });
          const data = await res.json().catch(() => ({ ok: false }));
          if (res.ok && data && data.ok) {
            loadUsers();
          } else {
            alert(data?.message || 'Failed to deactivate user');
          }
        } catch (err) {
          console.error('Deactivate error:', err);
          alert('Network error');
        }
      });
    });

    listContainer.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const row = btn.closest('.user-row');
        const id = row.getAttribute('data-id');
        if (!id) return;
        if (!confirm('Delete this user? This cannot be undone.')) return;
        try {
          const res = await fetch(`/api/admin/users/${id}/delete`, { method: 'POST' });
          const data = await res.json().catch(() => ({ ok: false }));
          if (res.ok && data && data.ok) {
            loadUsers();
          } else {
            alert(data?.message || 'Failed to delete user');
          }
        } catch (err) {
          console.error('Delete error:', err);
          alert('Network error');
        }
      });
    });
  }

  // Modal handlers
  if (openAddModBtn && addModModal) {
    openAddModBtn.addEventListener('click', () => {
      addModModal.style.display = 'flex';
    });
  }

  if (closeAddModBtn && addModModal) {
    closeAddModBtn.addEventListener('click', () => {
      addModModal.style.display = 'none';
    });
  }

  if (addModModal) {
    addModModal.addEventListener('click', (e) => {
      if (e.target === addModModal) {
        addModModal.style.display = 'none';
      }
    });

    const createBtn = addModModal.querySelector('.btn-primary');
    if (createBtn) {
      createBtn.addEventListener('click', async () => {
        const inputs = addModModal.querySelectorAll('input');
        const login_id = (inputs[0]?.value || '').trim();
        const sign_name = (inputs[1]?.value || '').trim();
        const password = (inputs[2]?.value || '').trim();

        if (!login_id || !sign_name || !password) {
          alert('Please fill in all fields');
          return;
        }

        try {
          const res = await fetch('/api/admin/users/create-moderator', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              login_id,
              sign_name,
              password,
              department: 'General',
              email: `${login_id}@example.edu`
            })
          });
          const data = await res.json().catch(() => ({ ok: false }));
          if (res.ok && data && data.ok) {
            addModModal.style.display = 'none';
            inputs.forEach(inp => inp.value = '');
            loadUsers();
          } else {
            alert(data?.message || 'Failed to create moderator');
          }
        } catch (err) {
          console.error('Create moderator error:', err);
          alert('Network error');
        }
      });
    }
  }

  // Search and filter
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      filterUsers();
    });
  }

  if (roleFilter) {
    roleFilter.addEventListener('change', () => {
      filterUsers();
    });
  }

  function filterUsers() {
    const searchTerm = (searchInput?.value || '').toLowerCase();
    const roleValue = roleFilter?.value || 'all';

    const filtered = allUsers.filter(u => {
      const matchSearch = String(u.login_id || '').toLowerCase().includes(searchTerm) ||
                         String(u.name || '').toLowerCase().includes(searchTerm) ||
                         String(u.email || '').toLowerCase().includes(searchTerm);
      const matchRole = roleValue === 'all' || String(u.role).toLowerCase() === roleValue;
      return matchSearch && matchRole;
    });

    renderUsers(filtered);
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  loadUsers();
});
