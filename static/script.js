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

// Helper function to escape HTML
function escapeHtml(text) {
    if (typeof text !== 'string') {
        if (text === null || typeof text === 'undefined') {
            text = '';
        } else {
            text = String(text);
        }
    }
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTools(toolsArray) {
    if (!Array.isArray(toolsArray)) {
        return `<div class="tool-item">Invalid tools data: Expected an array. Received: <pre>${escapeHtml(JSON.stringify(toolsArray, null, 2))}</pre></div>`;
    }
    let html = '';
    toolsArray.forEach(tool => {
        // Handle both OpenAI format (tool.function) and Anthropic format (direct properties)
        if (tool) {
            html += '<div class="tool-item">';
            
            // Check if it's OpenAI format
            if (tool.function && typeof tool.function.name === 'string') {
                html += `<div><strong>Type:</strong> ${escapeHtml(tool.type || 'function')}</div>`;
                html += `<div><strong>Name:</strong> ${escapeHtml(tool.function.name)}</div>`;
                if (tool.function.description) {
                    html += `<div><strong>Description:</strong> ${escapeHtml(tool.function.description)}</div>`;
                }
                if (tool.function.parameters) {
                    html += `<div><strong>Parameters:</strong> <pre>${escapeHtml(JSON.stringify(tool.function.parameters, null, 2))}</pre></div>`;
                }
            }
            // Check if it's Anthropic format
            else if (tool.name && typeof tool.name === 'string') {
                html += `<div><strong>Name:</strong> ${escapeHtml(tool.name)}</div>`;
                if (tool.description) {
                    html += `<div><strong>Description:</strong> ${escapeHtml(tool.description)}</div>`;
                }
                if (tool.input_schema) {
                    html += `<div><strong>Input Schema:</strong> <pre>${escapeHtml(JSON.stringify(tool.input_schema, null, 2))}</pre></div>`;
                }
            }
            // Unknown format
            else {
                html += `<div>Unknown tool format: <pre>${escapeHtml(JSON.stringify(tool, null, 2))}</pre></div>`;
            }
            
            html += '</div>';
        } else {
            html += `<div class="tool-item">Invalid tool object: null or undefined</div>`;
        }
    });
    return html;
}

function formatToolChoice(toolChoice) {
    if (typeof toolChoice === 'string') {
        return `<div><strong>Tool Choice:</strong> ${escapeHtml(toolChoice)}</div>`;
    }
    if (toolChoice && typeof toolChoice === 'object') {
        let html = '<div><strong>Tool Choice:</strong></div>';
        
        // Handle both OpenAI and Anthropic formats
        if (toolChoice.type) {
            html += `<div><strong>Type:</strong> ${escapeHtml(toolChoice.type)}</div>`;
        }
        
        // OpenAI format: { type: "function", function: { name: "..." } }
        if (toolChoice.function && toolChoice.function.name) {
            html += `<div><strong>Function Name:</strong> ${escapeHtml(toolChoice.function.name)}</div>`;
        }
        // Anthropic format: { type: "tool", name: "..." }
        else if (toolChoice.name) {
            html += `<div><strong>Tool Name:</strong> ${escapeHtml(toolChoice.name)}</div>`;
        }
        // Show raw data for other structures
        else if (Object.keys(toolChoice).length > 1 || (Object.keys(toolChoice).length === 1 && !toolChoice.type)) {
            html += `<pre>${escapeHtml(JSON.stringify(toolChoice, null, 2))}</pre>`;
        }
        
        return html;
    }
    return `<div><strong>Tool Choice:</strong> Invalid data <pre>${escapeHtml(JSON.stringify(toolChoice, null, 2))}</pre></div>`;
}

// Assuming formatFunctions is similar to formatTools for now
function formatFunctions(functionsArray) {
    return formatTools(functionsArray); // Reusing formatTools
}

// Assuming formatFunctionCall is similar to formatToolChoice (for function calls)
// For actual function call results, the structure might be different (e.g. name, arguments, content/result)
// This is for the *request* part if it specifies a function_call.
function formatFunctionCall(functionCall) {
     if (functionCall && typeof functionCall === 'object') {
        let html = '';
        if (functionCall.name) {
             html += `<div><strong>Name:</strong> ${escapeHtml(functionCall.name)}</div>`;
        }
        if (functionCall.arguments) {
             html += `<div><strong>Arguments:</strong> <pre>${escapeHtml(functionCall.arguments)}</pre></div>`; // Arguments are often stringified JSON
        }
        if (!html) { // If no name or arguments, show raw
            return `<pre>${escapeHtml(JSON.stringify(functionCall, null, 2))}</pre>`;
        }
        return html;
    }
    return `<pre>${escapeHtml(JSON.stringify(functionCall, null, 2))}</pre>`;
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
    html += `<div class="detail-item"><span class="label">Temperature:</span> <span class="value">${(request.data.temperature === undefined || request.data.temperature === null) ? 'None' : request.data.temperature}</span></div>`;
    html += `<div class="detail-item"><span class="label">Max Tokens:</span> <span class="value">${request.data.max_tokens || 'None'}</span></div>`;
    html += `<div class="detail-item"><span class="label">Stream:</span> <span class="value">${request.data.stream || false}</span></div>`;
    
    // Display Anthropic-specific fields
    if (request.endpoint.includes('Anthropic')) {
        if (request.data.system) {
            html += `<div class="detail-item"><span class="label">System:</span> <span class="value">${escapeHtml(request.data.system)}</span></div>`;
        }
        if (request.data.top_p !== undefined && request.data.top_p !== null) {
            html += `<div class="detail-item"><span class="label">Top P:</span> <span class="value">${request.data.top_p}</span></div>`;
        }
        if (request.data.top_k !== undefined && request.data.top_k !== null) {
            html += `<div class="detail-item"><span class="label">Top K:</span> <span class="value">${request.data.top_k}</span></div>`;
        }
        if (request.data.stop_sequences && request.data.stop_sequences.length > 0) {
            html += `<div class="detail-item"><span class="label">Stop Sequences:</span> <span class="value">${escapeHtml(JSON.stringify(request.data.stop_sequences))}</span></div>`;
        }
    }
    
    // Display messages or prompt
    if (request.data.messages) {
        html += '<div class="messages"><div class="label">Messages:</div>';
        request.data.messages.forEach(msg => {
            html += `<div class="message">`;
            html += `<div class="message-role">${msg.role}:</div>`;
            // Handle both string and structured content
            if (typeof msg.content === 'string') {
                html += `<div>${escapeHtml(msg.content)}</div>`;
            } else if (Array.isArray(msg.content)) {
                // Handle multimodal content
                html += '<div class="multimodal-content">';
                msg.content.forEach(item => {
                    if (item.type === 'text') {
                        html += `<div class="text-content">${escapeHtml(item.text || item.content || '')}</div>`;
                    } else if (item.type === 'image') {
                        // Anthropic format
                        if (item.source && item.source.type === 'base64') {
                            html += `<div class="image-content">`;
                            html += `<img src="data:${item.source.media_type};base64,${item.source.data}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                            html += `<div class="image-info">Image: ${item.source.media_type}</div>`;
                            html += `</div>`;
                        }
                    } else if (item.type === 'image_url') {
                        // OpenAI format
                        const imageUrl = item.image_url.url || item.image_url;
                        if (imageUrl.startsWith('data:')) {
                            html += `<div class="image-content">`;
                            html += `<img src="${imageUrl}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                            const mediaType = imageUrl.split(';')[0].split(':')[1] || 'unknown';
                            html += `<div class="image-info">Image: ${mediaType}</div>`;
                            html += `</div>`;
                        } else {
                            html += `<div class="image-content">`;
                            // For non-data URLs, we can keep them larger or also constrain them
                            html += `<img src="${imageUrl}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                            html += `<div class="image-info">Image URL: ${imageUrl}</div>`;
                            html += `</div>`;
                        }
                    } else {
                        // Unknown content type
                        html += `<div class="unknown-content"><pre>${escapeHtml(JSON.stringify(item, null, 2))}</pre></div>`;
                    }
                });
                html += '</div>';
            } else {
                // Other object format
                html += `<div><pre>${escapeHtml(JSON.stringify(msg.content, null, 2))}</pre></div>`;
            }
            html += `</div>`;
        });
        html += '</div>';
    } else if (request.data.prompt) {
        html += `<div class="detail-item"><span class="label">Prompt:</span></div>`;
        html += `<div class="messages"><pre>${escapeHtml(request.data.prompt)}</pre></div>`;
    }

    // Specific formatting for tools, tool_choice, functions, function_call
    if (request.data.tools) {
        html += '<div class="detail-section"><div class="label">Tools:</div>' + formatTools(request.data.tools) + '</div>';
    }
    if (request.data.tool_choice) {
        html += '<div class="detail-section"><div class="label">Tool Choice:</div>' + formatToolChoice(request.data.tool_choice) + '</div>';
    }
    if (request.data.functions) { // Assuming 'functions' has similar structure to 'tools'
        html += '<div class="detail-section"><div class="label">Functions:</div>' + formatFunctions(request.data.functions) + '</div>';
    }
    if (request.data.function_call) { // This is for *requesting* a function call
        html += '<div class="detail-section"><div class="label">Function Call (Request):</div>' + formatFunctionCall(request.data.function_call) + '</div>';
    }

    // Iterate over all keys in request.data and display them if not already handled
    const PRE_HANDLED_KEYS = ['model', 'temperature', 'max_tokens', 'stream', 'messages', 'prompt', 'tools', 'tool_choice', 'functions', 'function_call'];
    let additionalParamsHtml = '';
    for (const key in request.data) {
        if (request.data.hasOwnProperty(key) && !PRE_HANDLED_KEYS.includes(key)) {
            let value = request.data[key];
            if (typeof value === 'object' || Array.isArray(value)) {
                value = JSON.stringify(value);
            }
            additionalParamsHtml += `<div class="detail-item"><span class="label">${escapeHtml(key)}:</span> <span class="value">${escapeHtml(String(value))}</span></div>`;
        }
    }

    if (additionalParamsHtml) {
        html += '<div class="other-details">';
        html += '<div class="label">Additional Parameters:</div>';
        html += additionalParamsHtml;
        html += '</div>';
    }
    
    html += '</div>'; // close request-details
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
        preview: getRequestPreview(request),
        fullRequest: request,
        expanded: false
    };
    
    requestHistory.unshift(historyItem);
    updateHistoryDisplay();
}

function getRequestPreview(request) {
    if (request.data.messages && request.data.messages.length > 0) {
        const lastMessage = request.data.messages[request.data.messages.length - 1];
        if (typeof lastMessage.content === 'string') {
            return lastMessage.content.substring(0, 100) + (lastMessage.content.length > 100 ? '...' : '');
        } else if (Array.isArray(lastMessage.content)) {
            // Handle multimodal content
            let preview = '';
            let hasImage = false;
            lastMessage.content.forEach(item => {
                if (item.type === 'text') {
                    preview += (item.text || item.content || '');
                } else if (item.type === 'image' || item.type === 'image_url') {
                    hasImage = true;
                }
            });
            if (hasImage) {
                preview = '[Contains image] ' + preview;
            }
            return preview.substring(0, 100) + (preview.length > 100 ? '...' : '');
        }
        return 'Complex content';
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
        const expandedClass = item.expanded ? 'expanded' : '';
        html += `<div class="history-item ${expandedClass}" onclick="toggleHistoryItem(${index})">`;
        html += `<div class="history-header">`;
        html += `<div class="history-timestamp">${item.timestamp}</div>`;
        html += `<div class="history-endpoint">${item.endpoint} - ${item.model}</div>`;
        html += `<div class="history-preview">${escapeHtml(item.preview)}</div>`;
        html += `<div class="expand-icon">${item.expanded ? '▼' : '▶'}</div>`;
        html += `</div>`;
        
        if (item.expanded) {
            html += `<div class="history-details">`;
            html += `<div class="detail-section">`;
            html += `<strong>Request ID:</strong> ${item.fullRequest.id}<br>`;
            html += `<strong>Model:</strong> ${item.fullRequest.data.model}<br>`;
            html += `<strong>Temperature:</strong> ${(item.fullRequest.data.temperature === undefined || item.fullRequest.data.temperature === null) ? 'None' : item.fullRequest.data.temperature}<br>`;
            html += `<strong>Max Tokens:</strong> ${item.fullRequest.data.max_tokens || 'None'}<br>`;
            html += `<strong>Stream:</strong> ${item.fullRequest.data.stream || false}<br>`;
            
            if (item.fullRequest.data.messages) {
                html += `<div class="messages-section">`;
                html += `<strong>Messages:</strong>`;
                item.fullRequest.data.messages.forEach(msg => {
                    html += `<div class="message-detail">`;
                    html += `<span class="message-role">${msg.role}:</span> `;
                    if (typeof msg.content === 'string') {
                        html += `<span class="message-content">${escapeHtml(msg.content)}</span>`;
                    } else if (Array.isArray(msg.content)) {
                        // Handle multimodal content in history
                        html += '<div class="multimodal-content">';
                        msg.content.forEach(item => {
                            if (item.type === 'text') {
                                html += `<div class="text-content">${escapeHtml(item.text || item.content || '')}</div>`;
                            } else if (item.type === 'image' || item.type === 'image_url') {
                                html += `<div class="image-content">[Image content]</div>`;
                            }
                        });
                        html += '</div>';
                    } else {
                        html += `<span class="message-content"><pre>${escapeHtml(JSON.stringify(msg.content, null, 2))}</pre></span>`;
                    }
                    html += `</div>`;
                });
                html += `</div>`;
            } else if (item.fullRequest.data.prompt) {
                html += `<div class="prompt-section">`;
                html += `<strong>Prompt:</strong>`;
                html += `<pre class="prompt-content">${escapeHtml(item.fullRequest.data.prompt)}</pre>`;
                html += `</div>`;
            }

            // Specific formatting for tools, tool_choice, functions, function_call in history
            if (item.fullRequest.data.tools) {
                html += `<strong>Tools:</strong><br>${formatTools(item.fullRequest.data.tools)}`;
            }
            if (item.fullRequest.data.tool_choice) {
                html += `<strong>Tool Choice:</strong><br>${formatToolChoice(item.fullRequest.data.tool_choice)}`;
            }
            if (item.fullRequest.data.functions) {
                html += `<strong>Functions:</strong><br>${formatFunctions(item.fullRequest.data.functions)}`;
            }
            if (item.fullRequest.data.function_call) {
                html += `<strong>Function Call (Request):</strong><br>${formatFunctionCall(item.fullRequest.data.function_call)}`;
            }

            // Display other data from item.fullRequest.data
            const PRE_HANDLED_HISTORY_KEYS = ['model', 'temperature', 'max_tokens', 'stream', 'messages', 'prompt', 'tools', 'tool_choice', 'functions', 'function_call'];
            let additionalParamsHtml = '';
            for (const key in item.fullRequest.data) {
                if (item.fullRequest.data.hasOwnProperty(key) && !PRE_HANDLED_HISTORY_KEYS.includes(key)) {
                    let value = item.fullRequest.data[key];
                    if (typeof value === 'object' || Array.isArray(value)) {
                        value = JSON.stringify(value);
                    }
                    additionalParamsHtml += `<strong>${escapeHtml(key)}:</strong> ${escapeHtml(String(value))}<br>`;
                }
            }

            if (additionalParamsHtml) {
                html += `<strong>Additional Parameters:</strong><br>`;
                html += additionalParamsHtml;
            }
            
            html += `</div>`; // close detail-section
            html += `</div>`; // close history-details
        }
        
        html += `</div>`;
    });
    
    historyList.innerHTML = html;
}

function toggleHistoryItem(index) {
    requestHistory[index].expanded = !requestHistory[index].expanded;
    updateHistoryDisplay();
}

function sendDefaultResponse() {
    if (!currentRequestId) return;
    
    const defaultMessage = "Hello! I'm the AI assistant. How can I help you today?";
    const shouldStream = document.getElementById('stream-response').checked;
    
    const message = {
        type: 'response',
        request_id: currentRequestId,
        response: defaultMessage,
        stream: shouldStream
    };
    
    ws.send(JSON.stringify(message));
    
    // Reset UI
    resetResponseUI();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    
    document.getElementById('send-response').addEventListener('click', sendResponse);
    document.getElementById('send-default').addEventListener('click', sendDefaultResponse);
    document.getElementById('send-error').addEventListener('click', sendError);
    
    // Allow Ctrl+Enter to send response
    document.getElementById('response-input').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            sendResponse();
        }
    });
});