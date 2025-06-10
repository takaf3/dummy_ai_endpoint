# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running the Server
```bash
# Start in CLI mode (default)
python dummy_ai_endpoint.py

# Start in web UI mode
python dummy_ai_endpoint.py --mode web

# Custom port and host
python dummy_ai_endpoint.py --port 9000 --host 127.0.0.1
```

### Testing the Server
```bash
# Install dependencies
pip install -r requirements.txt

# Test OpenAI API compatibility (requires server to be running)
python example_openai_client.py

# Test Anthropic API compatibility (requires server to be running)
python example_anthropic_client.py
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t dummy-ai-endpoint .
docker run -p 8000:8000 --name dummy-ai-app -d dummy-ai-endpoint
```

## Architecture Overview

This is a FastAPI-based mock server that mimics both OpenAI and Anthropic APIs, intercepting requests and allowing manual response control. The application operates in two modes: CLI and Web UI.

### Core Components

- **`dummy_ai_endpoint.py`**: Main server file containing all API endpoints and response handling logic
- **`static/`**: Web UI assets (HTML, CSS, JS) for the web mode interface with dark mode support
- **`example_openai_client.py`**: Demonstration client showing how to interact with the OpenAI API mock
- **`example_anthropic_client.py`**: Demonstration client showing how to interact with the Anthropic API mock

### Key Features

#### Multimodal Support
The server handles images in both OpenAI and Anthropic formats:
- **OpenAI**: Uses `image_url` format with base64 data URLs or external URLs
- **Anthropic**: Uses `image` content blocks with base64 source data
- Images are properly displayed in the web UI and truncated in logs (dummy_ai_endpoint.py:108-157)

#### Tool/Function Calling
Both APIs support tool use:
- **OpenAI**: `tools` and `tool_choice` parameters in chat completions
- **Anthropic**: `tools` and `tool_choice` parameters in messages API
- Properly formatted in web UI for easy debugging

#### Response Modes

1. **CLI Mode (`--mode cli`)**: 
   - Default mode where responses are entered via terminal
   - Quick default response with just ENTER key
   - Multi-line responses with 'END' delimiter

2. **Web Mode (`--mode web`)**: 
   - Browser-based UI with WebSocket real-time updates
   - Dark mode support with system preference detection
   - Request history tracking
   - Three response options: Send Response, Send Default, Send Error

### Request Processing Pipeline

1. **Request Reception**: FastAPI endpoints receive requests at `/v1/chat/completions`, `/v1/completions`, or `/v1/messages`
2. **Request Logging**: `log_request()` function logs to console, file, and JSON with base64 truncation
3. **Response Handling**: 
   - CLI: `get_cli_response()` prompts for terminal input
   - Web: `get_web_response()` creates pending request and waits for WebSocket response
4. **Token Counting**: Simple approximation using word count * 1.3
5. **Response Formatting**: Matches exact OpenAI/Anthropic response structures including streaming

### WebSocket Communication (Web Mode)

- **Connection**: Clients connect to `/ws` endpoint
- **Request Notification**: New requests broadcast to all connected clients
- **Response Flow**: Client sends response → Server updates pending request → Original request receives response
- **State Management**: `pending_requests` dict and `websocket_clients` list track active connections

### Streaming Implementation

Both APIs support Server-Sent Events (SSE) streaming:
- **OpenAI**: Sends chat completion chunks with `data:` prefix
- **Anthropic**: Sends typed events (message_start, content_block_delta, etc.)
- Simulated delays between chunks for realistic streaming behavior

### Error Handling

- Invalid requests return proper API-formatted error responses
- WebSocket disconnections are gracefully handled
- Web UI can send custom error responses for testing error handling