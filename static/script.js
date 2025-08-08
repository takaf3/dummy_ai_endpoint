let ws;
let currentRequestId = null;

function connect() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

  ws.onopen = () => {
    showToast('Connected to server');
  };

  ws.onclose = () => {
    showToast('Disconnected. Reconnecting…', 'error');
    setTimeout(connect, 2000);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'new_request') {
      currentRequestId = data.request.id;
      const display = document.getElementById('request-display');
      display.textContent = JSON.stringify(data.request, null, 2);
    }
  };
}

function sendMessage(payload) {
  if (!currentRequestId) return;
  ws.send(JSON.stringify(payload));
  resetUI();
}

function sendResponse() {
  const text = document.getElementById('response-input').value;
  const stream = document.getElementById('stream-response').checked;
  sendMessage({ type: 'response', request_id: currentRequestId, response: text, stream });
}

function sendDefault() {
  const stream = document.getElementById('stream-response').checked;
  const msg = "Hello! I'm the AI assistant. How can I help you today?";
  sendMessage({ type: 'response', request_id: currentRequestId, response: msg, stream });
}

function sendError() {
  sendMessage({ type: 'error', request_id: currentRequestId, error: 'Internal Server Error', message: 'The server encountered an error processing your request.' });
}

function send429() {
  sendMessage({ type: 'error', request_id: currentRequestId, error: 'Too Many Requests', message: 'Rate limit exceeded. Please try again later.', status_code: 429 });
}

function sendCustomError() {
  const code = parseInt(document.getElementById('custom-status-code').value);
  const err = document.getElementById('custom-error-message').value;
  const detail = document.getElementById('custom-error-detail').value;
  if (isNaN(code)) {
    showToast('Enter a valid status code', 'error');
    return;
  }
  sendMessage({ type: 'error', request_id: currentRequestId, error: err, message: detail, status_code: code });
}

function resetUI() {
  currentRequestId = null;
  document.getElementById('request-display').textContent = 'Waiting for requests...';
  document.getElementById('response-input').value = '';
}

function showToast(message, type = 'info', duration = 2000) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  toast.style.background = type === 'error' ? '#dc2626' : 'var(--accent)';
  setTimeout(() => toast.classList.remove('show'), duration);
}

function toggleTheme() {
  document.body.classList.toggle('dark');
}

document.addEventListener('DOMContentLoaded', () => {
  connect();
  document.getElementById('send-response').onclick = sendResponse;
  document.getElementById('send-default').onclick = sendDefault;
  document.getElementById('send-error').onclick = sendError;
  document.getElementById('send-429').onclick = send429;
  document.getElementById('send-custom-error').onclick = sendCustomError;
  document.getElementById('theme-toggle').onclick = toggleTheme;
});
