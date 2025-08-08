let ws = null;
let currentRequestId = null;
let requestHistory = [];
let toastTimeouts = [];

// Button loading state helper
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// Toast notifications
function showToast(message, type = 'success', durationMs = 2200) {
    const root = document.getElementById('toast-root');
    if (!root) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span><span class="close">✕</span>`;
    const close = () => {
        if (!toast.parentElement) return;
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 200);
    };
    toast.querySelector('.close').addEventListener('click', close);
    root.appendChild(toast);
    const t = setTimeout(close, durationMs);
    toastTimeouts.push(t);
}

// Fetch and display API key information
async function fetchApiKeyInfo() {
    try {
        const response = await fetch('/api_key_info');
        const data = await response.json();
        
        if (data.remote_mode && data.api_key) {
            document.getElementById('api-key-section').classList.remove('hidden');
            document.getElementById('api-key-value').textContent = data.api_key;
            
            // Setup copy button
            document.getElementById('copy-api-key').addEventListener('click', () => {
                navigator.clipboard.writeText(data.api_key).then(() => {
                    const button = document.getElementById('copy-api-key');
                    button.textContent = '✅ Copied!';
                    showToast('API key copied to clipboard');
                    setTimeout(() => { button.textContent = '📋 Copy'; }, 1600);
                }).catch(err => {
                    console.error('Failed to copy:', err);
                    showToast('Failed to copy API key', 'error');
                });
            });
        }
    } catch (error) {
        console.error('Failed to fetch API key info:', error);
        showToast('Failed to fetch API key info', 'error');
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        updateServerStatus(true);
        showToast('Connected to server');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateServerStatus(false);
        showToast('Disconnected. Reconnecting…', 'error', 3000);
        setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        showToast('WebSocket error', 'error');
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
    statusEl.className = connected ? 'status-chip status-connected' : 'status-chip status-disconnected';
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
    
    // Handle embeddings endpoint
    if (request.endpoint && request.endpoint.includes('/v1/embeddings')) {
        html += `<div class="detail-item"><span class="label">Dimensions:</span> <span class="value">${request.data.dimensions || 'Default'}</span></div>`;
        html += `<div class="detail-item"><span class="label">Encoding Format:</span> <span class="value">${request.data.encoding_format || 'float'}</span></div>`;
        
        if (request.data.inputs) {
            html += '<div class="messages"><div class="label">Inputs:</div>';
            if (Array.isArray(request.data.inputs)) {
                request.data.inputs.forEach((input, index) => {
                    const truncated = input.length > 100 ? input.substring(0, 100) + '...' : input;
                    html += `<div class="message"><div class="message-role">Input ${index + 1}:</div><div>${escapeHtml(truncated)}</div></div>`;
                });
            } else {
                html += `<div class="message"><div>${escapeHtml(request.data.inputs)}</div></div>`;
            }
            html += '</div>';
        } else if (request.data.input) {
            html += '<div class="messages"><div class="label">Input:</div>';
            if (Array.isArray(request.data.input)) {
                request.data.input.forEach((input, index) => {
                    const truncated = input.length > 100 ? input.substring(0, 100) + '...' : input;
                    html += `<div class="message"><div class="message-role">Input ${index + 1}:</div><div>${escapeHtml(truncated)}</div></div>`;
                });
            } else {
                const truncated = request.data.input.length > 100 ? request.data.input.substring(0, 100) + '...' : request.data.input;
                html += `<div class="message"><div>${escapeHtml(truncated)}</div></div>`;
            }
            html += '</div>';
        }
    }
    // Display messages or prompt
    else if (request.data.messages) {
        html += '<div class="messages"><div class="label">Messages:</div>';
        request.data.messages.forEach(msg => {
            html += `<div class="message">`;
            html += `<div class="message-role">${escapeHtml(msg.role)}:</div>`;
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
                            html += `<img src="data:${escapeHtml(item.source.media_type)};base64,${item.source.data}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                            html += `<div class="image-info">Image: ${escapeHtml(item.source.media_type)}</div>`;
                            html += `</div>`;
                        } else {
                            html += `<div class="unknown-content">Invalid image source in array: <pre>${escapeHtml(JSON.stringify(item.source, null, 2))}</pre></div>`;
                        }
                    } else if (item.type === 'image_url') {
                        // OpenAI format
                        const imageUrl = item.image_url && item.image_url.url ? item.image_url.url : item.image_url;
                        if (typeof imageUrl === 'string') {
                            if (imageUrl.startsWith('data:')) {
                                html += `<div class="image-content">`;
                                html += `<img src="${imageUrl}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                                const mediaType = imageUrl.split(';')[0].split(':')[1] || 'unknown';
                                html += `<div class="image-info">Image: ${escapeHtml(mediaType)}</div>`;
                                html += `</div>`;
                            } else {
                                html += `<div class="image-content">`;
                                html += `<img src="${escapeHtml(imageUrl)}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                                html += `<div class="image-info">Image URL: ${escapeHtml(imageUrl)}</div>`;
                                html += `</div>`;
                            }
                        } else {
                            html += `<div class="unknown-content">Invalid image_url format in array: <pre>${escapeHtml(JSON.stringify(item.image_url, null, 2))}</pre></div>`;
                        }
                    } else {
                        // Unknown content type
                        html += `<div class="unknown-content"><pre>${escapeHtml(JSON.stringify(item, null, 2))}</pre></div>`;
                    }
                });
                html += '</div>';
            } else if (typeof msg.content === 'object' && msg.content !== null && (msg.content.type === 'image' || msg.content.type === 'image_url')) {
                // Handle single image object (similar to items in multimodal array)
                html += '<div class="multimodal-content">'; // Keep consistent structure
                const item = msg.content; // Treat the single object as an item
                if (item.type === 'image') {
                    // Anthropic format
                    if (item.source && item.source.type === 'base64') {
                        html += `<div class="image-content">`;
                        // Data URLs should not be escaped in src attribute
                        html += `<img src="data:${escapeHtml(item.source.media_type)};base64,${item.source.data}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                        html += `<div class="image-info">Image: ${escapeHtml(item.source.media_type)}</div>`;
                        html += `</div>`;
                    } else {
                         html += `<div class="unknown-content">Invalid image source: <pre>${escapeHtml(JSON.stringify(item.source, null, 2))}</pre></div>`;
                    }
                } else if (item.type === 'image_url') {
                    // OpenAI format
                    const imageUrl = item.image_url && item.image_url.url ? item.image_url.url : item.image_url;
                    if (typeof imageUrl === 'string') {
                        if (imageUrl.startsWith('data:')) {
                            html += `<div class="image-content">`;
                            // Data URLs should not be escaped in src attribute
                            html += `<img src="${imageUrl}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                            const mediaType = imageUrl.split(';')[0].split(':')[1] || 'unknown';
                            html += `<div class="image-info">Image: ${escapeHtml(mediaType)}</div>`;
                            html += `</div>`;
                        } else {
                            html += `<div class="image-content">`;
                            // Regular URLs should be escaped in src attribute and when displayed
                            html += `<img src="${escapeHtml(imageUrl)}" alt="User provided image" style="max-width: 200px; max-height: 200px; margin: 10px 0;">`;
                            html += `<div class="image-info">Image URL: ${escapeHtml(imageUrl)}</div>`;
                            html += `</div>`;
                        }
                    } else {
                        html += `<div class="unknown-content">Invalid image_url format: <pre>${escapeHtml(JSON.stringify(item.image_url, null, 2))}</pre></div>`;
                    }
                }
                html += '</div>'; // Close multimodal-content
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
    
    // Show/hide embedding options based on endpoint
    const embeddingOptions = document.getElementById('embedding-options');
    const responseInput = document.getElementById('response-input');
    
    if (request.endpoint && request.endpoint.includes('/v1/embeddings')) {
        console.log('Showing embedding options for endpoint:', request.endpoint);
        embeddingOptions.classList.remove('hidden');
        responseInput.style.display = 'none';
        document.getElementById('stream-response').parentElement.style.display = 'none';
    } else {
        console.log('Hiding embedding options for endpoint:', request.endpoint);
        embeddingOptions.classList.add('hidden');
        responseInput.style.display = 'block';
        document.getElementById('stream-response').parentElement.style.display = 'block';
    }
}

function sendResponse() {
    if (!currentRequestId) return;
    
    const button = document.getElementById('send-response');
    setButtonLoading(button, true);
    
    try {
        // Check if it's an embeddings request
        const embeddingOptions = document.getElementById('embedding-options');
        if (!embeddingOptions.classList.contains('hidden')) {
        // Handle embeddings response
        const embeddingType = document.getElementById('embedding-type').value;
        let embeddingData = { type: embeddingType };
        
        if (embeddingType === 'file') {
            const filepath = document.getElementById('embedding-filepath').value.trim();
            if (!filepath) {
                showToast('Please enter a filepath', 'error');
                setButtonLoading(button, false);
                return;
            }
            embeddingData.filepath = filepath;
        } else if (embeddingType === 'custom') {
            const customJson = document.getElementById('embedding-custom-json').value.trim();
            if (!customJson) {
                showToast('Please enter custom JSON', 'error');
                setButtonLoading(button, false);
                return;
            }
            try {
                embeddingData.data = JSON.parse(customJson);
            } catch (e) {
                showToast('Invalid JSON: ' + e.message, 'error');
                setButtonLoading(button, false);
                return;
            }
        }
        
        const message = {
            type: 'response',
            request_id: currentRequestId,
            response: '',  // Empty for embeddings
            embedding_type: embeddingData
        };
        
        ws.send(JSON.stringify(message));
        } else {
            // Handle regular response
            const responseText = document.getElementById('response-input').value;
            const shouldStream = document.getElementById('stream-response').checked;
            
            if (!responseText.trim()) {
                showToast('Please enter a response', 'error');
                setButtonLoading(button, false);
                return;
            }
        
        const message = {
            type: 'response',
            request_id: currentRequestId,
            response: responseText,
            stream: shouldStream
        };
        
        ws.send(JSON.stringify(message));
        }
        
        // Reset UI
        resetResponseUI();
        setButtonLoading(button, false);
    } catch (error) {
        console.error('Error sending response:', error);
        showToast('Failed to send response', 'error');
        setButtonLoading(button, false);
    }
}

function sendError() {
    if (!currentRequestId) return;
    
    const button = document.getElementById('send-error');
    setButtonLoading(button, true);
    
    try {
        const message = {
            type: 'error',
            request_id: currentRequestId,
            error: 'Internal Server Error',
            message: 'The server encountered an error processing your request.'
        };
        
        ws.send(JSON.stringify(message));
        
        // Reset UI
        resetResponseUI();
        setButtonLoading(button, false);
    } catch (error) {
        console.error('Error sending error response:', error);
        showToast('Failed to send error response', 'error');
        setButtonLoading(button, false);
    }
}

function send429Error() {
    if (!currentRequestId) return;
    
    const button = document.getElementById('send-429');
    setButtonLoading(button, true);
    
    try {
        const message = {
            type: 'error',
            request_id: currentRequestId,
            error: 'Too Many Requests',
            message: 'Rate limit exceeded. Please try again later.',
            status_code: 429
        };
        
        ws.send(JSON.stringify(message));
        
        // Reset UI
        resetResponseUI();
        setButtonLoading(button, false);
    } catch (error) {
        console.error('Error sending 429 error:', error);
        showToast('Failed to send 429 error', 'error');
        setButtonLoading(button, false);
    }
}

function sendCustomError() {
    if (!currentRequestId) return;
    
    const button = document.getElementById('send-custom-error');
    setButtonLoading(button, true);
    
    try {
        const statusCode = parseInt(document.getElementById('custom-status-code').value);
        const errorMessage = document.getElementById('custom-error-message').value;
        const errorDetail = document.getElementById('custom-error-detail').value;
        
        // Validate status code
        if (isNaN(statusCode) || statusCode < 100 || statusCode > 599) {
            showToast('Enter a valid HTTP status code (100–599)', 'error');
            setButtonLoading(button, false);
            return;
        }
        
        // Validate required fields
        if (!errorMessage.trim()) {
            showToast('Please enter an error message', 'error');
            setButtonLoading(button, false);
            return;
        }
        
        const message = {
            type: 'error',
            request_id: currentRequestId,
            error: errorMessage,
            message: errorDetail,
            status_code: statusCode
        };
        
        ws.send(JSON.stringify(message));
        
        // Reset UI
        resetResponseUI();
        setButtonLoading(button, false);
    } catch (error) {
        console.error('Error sending custom error:', error);
        showToast('Failed to send custom error', 'error');
        setButtonLoading(button, false);
    }
}

function setPresetError(statusCode, errorMessage, errorDetail) {
    document.getElementById('custom-status-code').value = statusCode;
    document.getElementById('custom-error-message').value = errorMessage;
    document.getElementById('custom-error-detail').value = errorDetail;
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
                    html += `<span class="message-role">${escapeHtml(msg.role)}:</span> `;
                    if (typeof msg.content === 'string') {
                        html += `<span class="message-content">${escapeHtml(msg.content)}</span>`;
                    } else if (Array.isArray(msg.content)) {
                        // Handle multimodal content in history
                        html += '<div class="multimodal-content">';
                        msg.content.forEach(item => {
                            if (item.type === 'text') {
                                html += `<div class="text-content">${escapeHtml(item.text || item.content || '')}</div>`;
                            } else if (item.type === 'image') {
                                // Anthropic format
                                if (item.source && item.source.type === 'base64') {
                                    html += `<div class="image-content">`;
                                    html += `<img src="data:${escapeHtml(item.source.media_type)};base64,${item.source.data}" alt="History image" style="max-width: 150px; max-height: 150px; margin: 5px 0;">`; // Slightly smaller for history
                                    html += `<div class="image-info-history">Image: ${escapeHtml(item.source.media_type)}</div>`;
                                    html += `</div>`;
                                } else {
                                    html += `<div class="unknown-content-history">Invalid image source in history: <pre>${escapeHtml(JSON.stringify(item.source, null, 2))}</pre></div>`;
                                }
                            } else if (item.type === 'image_url') {
                                // OpenAI format
                                const imageUrl = item.image_url && item.image_url.url ? item.image_url.url : item.image_url;
                                if (typeof imageUrl === 'string') {
                                    if (imageUrl.startsWith('data:')) {
                                        html += `<div class="image-content">`;
                                        html += `<img src="${imageUrl}" alt="History image" style="max-width: 150px; max-height: 150px; margin: 5px 0;">`;
                                        const mediaType = imageUrl.split(';')[0].split(':')[1] || 'unknown';
                                        html += `<div class="image-info-history">Image: ${escapeHtml(mediaType)}</div>`;
                                        html += `</div>`;
                                    } else {
                                        html += `<div class="image-content">`;
                                        html += `<img src="${escapeHtml(imageUrl)}" alt="History image" style="max-width: 150px; max-height: 150px; margin: 5px 0;">`;
                                        html += `<div class="image-info-history">Image URL: ${escapeHtml(imageUrl)}</div>`;
                                        html += `</div>`;
                                    }
                                } else {
                                    html += `<div class="unknown-content-history">Invalid image_url format in history array: <pre>${escapeHtml(JSON.stringify(item.image_url, null, 2))}</pre></div>`;
                                }
                            } else {
                                // Fallback for other unknown item types within content array
                                html += `<div class="unknown-content-history"><pre>${escapeHtml(JSON.stringify(item, null, 2))}</pre></div>`;
                            }
                        });
                        html += '</div>';
                    } else if (typeof msg.content === 'object' && msg.content !== null && (msg.content.type === 'image' || msg.content.type === 'image_url')) {
                        // Handle single image object in history
                        html += '<div class="multimodal-content">'; // Keep consistent structure
                        const item = msg.content;
                        if (item.type === 'image') {
                            if (item.source && item.source.type === 'base64') {
                                html += `<div class="image-content">`;
                                html += `<img src="data:${escapeHtml(item.source.media_type)};base64,${item.source.data}" alt="History image" style="max-width: 150px; max-height: 150px; margin: 5px 0;">`;
                                html += `<div class="image-info-history">Image: ${escapeHtml(item.source.media_type)}</div>`;
                                html += `</div>`;
                            } else {
                                 html += `<div class="unknown-content-history">Invalid image source in history: <pre>${escapeHtml(JSON.stringify(item.source, null, 2))}</pre></div>`;
                            }
                        } else if (item.type === 'image_url') {
                            const imageUrl = item.image_url && item.image_url.url ? item.image_url.url : item.image_url;
                            if (typeof imageUrl === 'string') {
                                if (imageUrl.startsWith('data:')) {
                                    html += `<div class="image-content">`;
                                    html += `<img src="${imageUrl}" alt="History image" style="max-width: 150px; max-height: 150px; margin: 5px 0;">`;
                                    const mediaType = imageUrl.split(';')[0].split(':')[1] || 'unknown';
                                    html += `<div class="image-info-history">Image: ${escapeHtml(mediaType)}</div>`;
                                    html += `</div>`;
                                } else {
                                    html += `<div class="image-content">`;
                                    html += `<img src="${escapeHtml(imageUrl)}" alt="History image" style="max-width: 150px; max-height: 150px; margin: 5px 0;">`;
                                    html += `<div class="image-info-history">Image URL: ${escapeHtml(imageUrl)}</div>`;
                                    html += `</div>`;
                                }
                            } else {
                                html += `<div class="unknown-content-history">Invalid image_url format in history: <pre>${escapeHtml(JSON.stringify(item.image_url, null, 2))}</pre></div>`;
                            }
                        }
                        html += '</div>'; // Close multimodal-content
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
    
    const button = document.getElementById('send-default');
    setButtonLoading(button, true);
    
    try {
        // Check if it's an embeddings request
        const embeddingOptions = document.getElementById('embedding-options');
        if (!embeddingOptions.classList.contains('hidden')) {
            // Send default random embedding
            const message = {
                type: 'response',
                request_id: currentRequestId,
                response: '',
                embedding_type: { type: 'random' }
            };
            
            ws.send(JSON.stringify(message));
        } else {
            // Send default text response
            const defaultMessage = "Hello! I'm the AI assistant. How can I help you today?";
            const shouldStream = document.getElementById('stream-response').checked;
            
            const message = {
                type: 'response',
                request_id: currentRequestId,
                response: defaultMessage,
                stream: shouldStream
            };
            
            ws.send(JSON.stringify(message));
        }
        
        // Reset UI
        resetResponseUI();
        setButtonLoading(button, false);
    } catch (error) {
        console.error('Error sending default response:', error);
        showToast('Failed to send default response', 'error');
        setButtonLoading(button, false);
    }
}

// Theme management
function initTheme() {
    // Check for saved theme preference or default to system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Determine initial theme
    let theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
    
    // Apply theme
    setTheme(theme);
    
    // Listen for system theme changes if no manual preference is set
    if (!savedTheme) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeToggle(theme);
}

function updateThemeToggle(theme) {
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    
    if (theme === 'dark') {
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Light';
    } else {
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Dark';
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

// Export functions
function exportToJSON() {
    if (requestHistory.length === 0) {
        alert('No requests to export');
        return;
    }
    
    const exportData = requestHistory.map(item => ({
        timestamp: item.timestamp,
        endpoint: item.endpoint,
        model: item.model,
        requestId: item.fullRequest.id,
        requestData: item.fullRequest.data
    }));
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `ai_requests_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function exportToCSV() {
    if (requestHistory.length === 0) {
        alert('No requests to export');
        return;
    }
    
    // CSV headers
    const headers = ['Timestamp', 'Endpoint', 'Model', 'Request ID', 'Temperature', 'Max Tokens', 'Stream', 'Message Preview'];
    
    // Convert data to CSV rows
    const rows = requestHistory.map(item => {
        const messagePreview = getRequestPreview(item.fullRequest).replace(/"/g, '""'); // Escape quotes
        
        return [
            item.timestamp,
            item.endpoint,
            item.model,
            item.fullRequest.id,
            item.fullRequest.data.temperature ?? '',
            item.fullRequest.data.max_tokens || '',
            item.fullRequest.data.stream || false,
            `"${messagePreview}"`
        ].join(',');
    });
    
    // Combine headers and rows
    const csvContent = [headers.join(','), ...rows].join('\n');
    
    const dataBlob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `ai_requests_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();
    
    // Theme toggle event listener
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    
    // Fetch API key info
    fetchApiKeyInfo();
    
    // WebSocket connection
    connectWebSocket();
    
    // Button event listeners
    document.getElementById('send-response').addEventListener('click', sendResponse);
    document.getElementById('send-default').addEventListener('click', sendDefaultResponse);
    document.getElementById('send-error').addEventListener('click', sendError);
    document.getElementById('send-429').addEventListener('click', send429Error);
    document.getElementById('send-custom-error').addEventListener('click', sendCustomError);
    
    // Preset error button event listeners
    document.querySelectorAll('.btn-preset').forEach(button => {
        button.addEventListener('click', () => {
            const statusCode = button.getAttribute('data-status');
            const errorMessage = button.getAttribute('data-message');
            const errorDetail = button.getAttribute('data-detail');
            setPresetError(statusCode, errorMessage, errorDetail);
        });
    });
    
    // Export button event listeners
    document.getElementById('export-json').addEventListener('click', exportToJSON);
    document.getElementById('export-csv').addEventListener('click', exportToCSV);
    
    // Allow Ctrl+Enter to send response
    document.getElementById('response-input').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            sendResponse();
        }
    });

    // Auto-grow textarea
    const responseInput = document.getElementById('response-input');
    const autoGrow = () => {
        responseInput.classList.add('auto-grow');
        responseInput.style.height = 'auto';
        responseInput.style.height = (responseInput.scrollHeight) + 'px';
    };
    ['input', 'change'].forEach(evt => responseInput.addEventListener(evt, autoGrow));
    setTimeout(autoGrow, 0);
    
    // Embedding type change handler
    document.getElementById('embedding-type').addEventListener('change', (e) => {
        const fileInput = document.getElementById('embedding-file-input');
        const customInput = document.getElementById('embedding-custom-input');
        
        // Hide all optional inputs first
        fileInput.classList.add('hidden');
        customInput.classList.add('hidden');
        
        // Show relevant input based on selection
        if (e.target.value === 'file') {
            fileInput.classList.remove('hidden');
        } else if (e.target.value === 'custom') {
            customInput.classList.remove('hidden');
        }
    });
});