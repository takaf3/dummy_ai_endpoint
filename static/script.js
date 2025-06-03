let ws = null;
let currentRequestId = null;
let requestHistory = [];

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        updateServerStatus(true);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateServerStatus(false);
        setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function updateServerStatus(connected) {
    const statusEl = document.getElementById('server-status');
    statusEl.textContent = connected ? 'Connected' : 'Disconnected';
    statusEl.className = connected ? 'status-value status-connected' : 'status-value status-disconnected';
}

function handleMessage(data) {
    if (data.type === 'new_request') {
        displayRequest(data.request);
        addToHistory(data.request);
    }
}

function displayRequest(request) {
    currentRequestId = request.id;
    
    const requestInfo = document.getElementById('request-info');
    const responseControls = document.getElementById('response-controls');
    const waitingMessage = document.getElementById('waiting-for-request');
    
    // Show response controls, hide waiting message
    responseControls.classList.remove('hidden');
    waitingMessage.classList.add('hidden');
    
    // Build request display
    let html = '<div class="request-details">';
    html += `<div class="detail-item"><span class="label">Request ID:</span> <span class="value">${request.id}</span></div>`;
    html += `<div class="detail-item"><span class="label">Endpoint:</span> <span class="value">${request.endpoint}</span></div>`;
    html += `<div class="detail-item"><span class="label">Model:</span> <span class="value">${request.data.model}</span></div>`;
    html += `<div class="detail-item"><span class="label">Temperature:</span> <span class="value">${request.data.temperature || 1.0}</span></div>`;
    html += `<div class="detail-item"><span class="label">Max Tokens:</span> <span class="value">${request.data.max_tokens || 'None'}</span></div>`;
    html += `<div class="detail-item"><span class="label">Stream:</span> <span class="value">${request.data.stream || false}</span></div>`;
    
    // Display messages or prompt
    if (request.data.messages) {
        html += '<div class="messages"><div class="label">Messages:</div>';
        request.data.messages.forEach(msg => {
            html += `<div class="message">`;
            html += `<div class="message-role">${msg.role}:</div>`;
            html += `<div>${escapeHtml(msg.content)}</div>`;
            html += `</div>`;
        });
        html += '</div>';
    } else if (request.data.prompt) {
        html += `<div class="detail-item"><span class="label">Prompt:</span></div>`;
        html += `<div class="messages"><pre>${escapeHtml(request.data.prompt)}</pre></div>`;
    }
    
    html += '</div>';
    requestInfo.innerHTML = html;
    
    // Clear previous response
    document.getElementById('response-input').value = '';
    document.getElementById('stream-response').checked = request.data.stream || false;
}

function sendResponse() {
    if (!currentRequestId) return;
    
    const responseText = document.getElementById('response-input').value;
    const shouldStream = document.getElementById('stream-response').checked;
    
    if (!responseText.trim()) {
        alert('Please enter a response');
        return;
    }
    
    const message = {
        type: 'response',
        request_id: currentRequestId,
        response: responseText,
        stream: shouldStream
    };
    
    ws.send(JSON.stringify(message));
    
    // Reset UI
    resetResponseUI();
}

function sendError() {
    if (!currentRequestId) return;
    
    const message = {
        type: 'error',
        request_id: currentRequestId,
        error: 'Internal Server Error',
        message: 'The server encountered an error processing your request.'
    };
    
    ws.send(JSON.stringify(message));
    
    // Reset UI
    resetResponseUI();
}

function resetResponseUI() {
    currentRequestId = null;
    document.getElementById('request-info').innerHTML = '<p class="waiting-message">Waiting for requests...</p>';
    document.getElementById('response-controls').classList.add('hidden');
    document.getElementById('waiting-for-request').classList.remove('hidden');
}

function addToHistory(request) {
    const historyItem = {
        timestamp: new Date().toLocaleString(),
        endpoint: request.endpoint,
        model: request.data.model,
        preview: getRequestPreview(request)
    };
    
    requestHistory.unshift(historyItem);
    updateHistoryDisplay();
}

function getRequestPreview(request) {
    if (request.data.messages && request.data.messages.length > 0) {
        const lastMessage = request.data.messages[request.data.messages.length - 1];
        return lastMessage.content.substring(0, 100) + (lastMessage.content.length > 100 ? '...' : '');
    } else if (request.data.prompt) {
        return request.data.prompt.substring(0, 100) + (request.data.prompt.length > 100 ? '...' : '');
    }
    return 'No content';
}

function updateHistoryDisplay() {
    const historyList = document.getElementById('history-list');
    
    if (requestHistory.length === 0) {
        historyList.innerHTML = '<p class="no-history">No requests yet</p>';
        return;
    }
    
    let html = '';
    requestHistory.forEach((item, index) => {
        html += `<div class="history-item" onclick="viewHistoryItem(${index})">`;
        html += `<div class="history-timestamp">${item.timestamp}</div>`;
        html += `<div class="history-endpoint">${item.endpoint} - ${item.model}</div>`;
        html += `<div class="history-preview">${escapeHtml(item.preview)}</div>`;
        html += `</div>`;
    });
    
    historyList.innerHTML = html;
}

function viewHistoryItem(index) {
    // Could expand this to show full request details
    console.log('View history item:', requestHistory[index]);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    
    document.getElementById('send-response').addEventListener('click', sendResponse);
    document.getElementById('send-error').addEventListener('click', sendError);
    
    // Allow Ctrl+Enter to send response
    document.getElementById('response-input').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            sendResponse();
        }
    });
});