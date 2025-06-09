// Filter functionality
function toggleFilter() {
  const panel = document.getElementById("filterPanel");
  panel.classList.toggle("hidden");
}

function applyFilter() {
  const nameInput = document.getElementById("nameFilter").value.toLowerCase();
  const statusInput = document.getElementById("statusFilter").value.toLowerCase();
  const rows = document.querySelectorAll("table tbody tr");

  rows.forEach((row) => {
    const name = row.querySelector("td").textContent.toLowerCase();
    const status = row.querySelector(".status").classList[1].toLowerCase();

    const matchesName = name.includes(nameInput);
    const matchesStatus = !statusInput || status === statusInput;

    if (matchesName && matchesStatus) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}

// Modal elements and variables
let modal, credentialsModal, deleteModal;
let currentCredentialIndex = 0;
let credentialData = null;
let agentToDelete = null;

// Initialize modal elements when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  modal = document.getElementById("addAgentModal");
  credentialsModal = document.getElementById("agentCredentialsModal");
  deleteModal = document.getElementById("deleteAgentModal");
  
  // Setup modal click outside to close
  window.onclick = function (e) {
    if (e.target == modal) {
      closeModal();
    }
    if (e.target == credentialsModal) {
      closeCredentialsModal();
    }
    if (e.target == deleteModal) {
      closeDeleteModal();
    }
  }
});

// Add Agent Modal functions
function openModal() {
  modal.style.display = "block";
}

function closeModal() {
  modal.style.display = "none";
  // Clear input field
  document.getElementById("agentNameInput").value = "";
}

// Credentials Modal functions
function openCredentialsModal(data) {
  credentialData = typeof data === 'string' ? JSON.parse(data) : data;
  
  // Populate the credential items
  document.getElementById('agentPrivateKey').textContent = credentialData.agent_private_key;
  document.getElementById('serverPublicKey').textContent = credentialData.server_public_key;
  document.getElementById('agentUuid').textContent = credentialData.uuid;
  
  // Reset to first credential
  currentCredentialIndex = 0;
  showCredential(currentCredentialIndex);
  
  credentialsModal.style.display = 'block';
}

function closeCredentialsModal() {
  credentialsModal.style.display = 'none';
  currentCredentialIndex = 0;
  credentialData = null;
}

// Delete Agent Modal functions
function openDeleteModal(agentUuid, agentName) {
  agentToDelete = {
    uuid: agentUuid,
    name: agentName
  };
  
  document.getElementById("deleteAgentText").textContent = 
    `Are you sure you want to delete agent "${agentName}"? This action cannot be undone.`;
  document.getElementById("adminPasswordInput").value = "";
  
  deleteModal.style.display = "block";
}

function closeDeleteModal() {
  deleteModal.style.display = "none";
  agentToDelete = null;
  document.getElementById("adminPasswordInput").value = "";
}

async function confirmDeleteAgent() {
  if (!agentToDelete) {
    alert("No agent selected for deletion.");
    return;
  }
  
  const password = document.getElementById("adminPasswordInput").value;
  if (!password.trim()) {
    alert("Please enter your admin password.");
    return;
  }
  
  const deleteButton = document.querySelector(".delete-confirm-btn");
  const originalButtonText = deleteButton.textContent;
  
  try {
    // Disable button and show loading state
    deleteButton.disabled = true;
    deleteButton.textContent = "Deleting...";
    
    const response = await fetch(`/api/agents/${agentToDelete.uuid}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ password }),
    });

    const result = await response.json();
    if (response.ok) {
      alert(`Agent "${agentToDelete.name}" deleted successfully.`);
      closeDeleteModal();
      location.reload(); // Refresh the page
    } else {
      alert(result.msg); // Show error message
    }
  } catch (error) {
    alert("An error occurred: " + error.message);
  } finally {
    // Reset button state
    deleteButton.disabled = false;
    deleteButton.textContent = originalButtonText;
  }
}

// Credential navigation functions
function showCredential(index) {
  const items = document.querySelectorAll('.credential-item');
  const indicators = document.querySelectorAll('.indicator-dot');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');

  // Hide all items and deactivate indicators
  items.forEach(item => item.classList.remove('active'));
  indicators.forEach(indicator => indicator.classList.remove('active'));

  // Show current item and activate indicator
  items[index].classList.add('active');
  indicators[index].classList.add('active');

  // Update navigation buttons
  prevBtn.disabled = index === 0;
  
  if (index === items.length - 1) {
    nextBtn.textContent = 'Done';
    nextBtn.className = 'nav-btn done-btn';
  } else {
    nextBtn.textContent = 'Next';
    nextBtn.className = 'nav-btn';
  }
}

function previousCredential() {
  if (currentCredentialIndex > 0) {
    currentCredentialIndex--;
    showCredential(currentCredentialIndex);
  }
}

function nextCredential() {
  const items = document.querySelectorAll('.credential-item');
  
  if (currentCredentialIndex === items.length - 1) {
    // Done button clicked - refresh the page
    location.reload();
  } else if (currentCredentialIndex < items.length - 1) {
    currentCredentialIndex++;
    showCredential(currentCredentialIndex);
  }
}

// Copy to clipboard function
async function copyToClipboard(elementId, button) {
  try {
    const text = document.getElementById(elementId).textContent;
    await navigator.clipboard.writeText(text);
    
    // Visual feedback
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    button.classList.add('copied');
    
    setTimeout(() => {
      button.textContent = originalText;
      button.classList.remove('copied');
    }, 2000);
  } catch (err) {
    console.error('Failed to copy: ', err);
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = document.getElementById(elementId).textContent;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    button.textContent = 'Copied!';
    setTimeout(() => {
      button.textContent = 'Copy';
    }, 2000);
  }
}

// Submit agent function
async function submitAgent() {
  const name = document.getElementById("agentNameInput").value;
  const submitButton = document.querySelector(".submit-btn");
  const originalButtonText = submitButton.textContent;

  if (name.trim()) {
    // Disable button and show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = `
      <span class="spinner"></span>
      Generating Keys...
    `;
    submitButton.classList.add("loading");

    try {
      const response = await fetch("/api/agents/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name }),
      });

      const result = await response.json();
      if (response.ok) {
        closeModal();
        // Show the credentials modal with the result
        openCredentialsModal(result);
      } else {
        alert(result.msg); // Show error message
      }
    } catch (error) {
      alert("An error occurred: " + error.message);
    } finally {
      // Reset button state
      submitButton.disabled = false;
      submitButton.textContent = originalButtonText;
      submitButton.classList.remove("loading");
    }
  } else {
    alert("Please enter a name.");
  }
}