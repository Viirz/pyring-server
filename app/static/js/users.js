(function(){
  // Helpers to get API endpoints from data attributes
  function getConfig() {
    const root = document.getElementById('usersPage');
    return {
      listUrl: root?.dataset.listUrl || '/api/users/',
      createUrl: root?.dataset.createUrl || '/api/users/create',
      deleteUrlTemplate: root?.dataset.deleteUrlTemplate || '/api/users/__EMAIL__'
    };
  }

  async function loadUsers() {
    const cfg = getConfig();
    try {
      const resp = await fetch(cfg.listUrl, {
        method: 'GET',
        credentials: 'include'
      });
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.msg || 'Failed to load users');
        return;
      }
      const tbody = document.getElementById('usersTableBody');
      tbody.innerHTML = '';
      data.forEach(u => {
        const tr = document.createElement('tr');

        const nameTd = document.createElement('td');
        nameTd.textContent = u.name || '';
        tr.appendChild(nameTd);

        const emailTd = document.createElement('td');
        emailTd.textContent = u.email || '';
        tr.appendChild(emailTd);

        const roleTd = document.createElement('td');
        roleTd.textContent = u.role || 'user';
        tr.appendChild(roleTd);

        const actionTd = document.createElement('td');
        actionTd.style.textAlign = 'center';
        const delBtn = document.createElement('button');
        delBtn.className = 'btn-red';
        delBtn.textContent = 'Delete';
        delBtn.onclick = () => deleteUser(u.email);
        actionTd.appendChild(delBtn);
        tr.appendChild(actionTd);

        tbody.appendChild(tr);
      });
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  function toggleCreate() {
    const card = document.getElementById('createUserCard');
    card.classList.toggle('hidden');
  }

  async function createUser() {
    const cfg = getConfig();
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const repeat_password = document.getElementById('repeat_password').value;
    const role = document.getElementById('role').value;

    if (!name || !email || !password || !repeat_password || !role) {
      alert('All fields are required');
      return;
    }

    try {
      const resp = await fetch(cfg.createUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name, email, password, repeat_password, role })
      });
      const result = await resp.json();
      if (resp.ok) {
        alert('User created');
        // Reset form
        document.getElementById('name').value = '';
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
        document.getElementById('repeat_password').value = '';
        document.getElementById('role').value = 'user';
        // Hide card and refresh list
        document.getElementById('createUserCard').classList.add('hidden');
        loadUsers();
      } else {
        alert(result.msg || 'Failed to create user');
      }
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  async function deleteUser(email) {
    const cfg = getConfig();
    if (!confirm(`Delete user "${email}"? This action cannot be undone.`)) return;
    try {
      const url = cfg.deleteUrlTemplate.replace('__EMAIL__', encodeURIComponent(email));
      const resp = await fetch(url, {
        method: 'DELETE',
        credentials: 'include'
      });
      const result = await resp.json();
      if (resp.ok) {
        loadUsers();
      } else {
        alert(result.msg || 'Failed to delete user');
      }
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  // Expose functions for inline onclick handlers (keeps functionality unchanged)
  window.toggleCreate = toggleCreate;
  window.createUser = createUser;
  window.deleteUser = deleteUser;

  document.addEventListener('DOMContentLoaded', loadUsers);
})();
