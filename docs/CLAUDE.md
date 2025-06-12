# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running the Server
```bash
# Start in CLI mode (default)
python dummy_ai_endpoint.py

# Start in web UI mode
python dummy_ai_endpoint.py --mode web

# Start in remote mode with API key authentication
python dummy_ai_endpoint.py --mode web --remote

# Custom port and host
python dummy_ai_endpoint.py --port 9000 --host 127.0.0.1

# Remote mode on custom port
python dummy_ai_endpoint.py --mode web --remote --port 9000
```

### Testing the Server
```bash
# Install dependencies
pip install -r requirements.txt

# Test OpenAI API compatibility (requires server to be running)
python example_openai_client.py

# Test Anthropic API compatibility (requires server to be running)
python example_anthropic_client.py

# Test OpenAI Embeddings API (requires server to be running)
python example_embeddings_client.py
```

### Docker Deployment
```bash
# Build the Docker image
docker build -t dummy-ai-endpoint .

# Run in default mode (web UI without authentication)
docker run -p 8000:8000 --name dummy-ai-app -d dummy-ai-endpoint

# Run in remote mode with API key authentication
docker run -p 8000:8000 --name dummy-ai-app dummy-ai-endpoint \
  python dummy_ai_endpoint.py --mode web --host 0.0.0.0 --port 8000 --remote

# View the API key from container logs
docker logs dummy-ai-app | grep "API Key:"

# Run interactively to see the API key immediately
docker run -it -p 8000:8000 dummy-ai-endpoint \
  python dummy_ai_endpoint.py --mode web --host 0.0.0.0 --port 8000 --remote
```

## Architecture Overview

This is a FastAPI-based mock server that mimics both OpenAI and Anthropic APIs, intercepting requests and allowing manual response control. The application operates in two modes: CLI and Web UI.

### Core Components

- **`dummy_ai_endpoint.py`**: Main server file containing all API endpoints and response handling logic
- **`static/`**: Web UI assets (HTML, CSS, JS) for the web mode interface with dark mode support
- **`examples/`**: Directory containing all example client implementations
  - `example_openai_client.py`: Demonstration client for OpenAI API
  - `example_anthropic_client.py`: Demonstration client for Anthropic API  
  - `example_anthropic_sdk.py`: Example using official Anthropic SDK
  - `example_embeddings_client.py`: Demonstration of embeddings API
  - `sample_embeddings.json`: Example file for testing file-based embeddings

### Key Features

#### Remote Mode
When running with the `--remote` flag, the server operates in remote mode:
- **API Key Authentication**: A secure API key is generated on startup and must be included in all requests
- **Disabled Endpoints**: The `/server_info` endpoint is disabled for security
- **Compatible Authentication**: Accepts both authentication styles:
  - **OpenAI style**: `Authorization: Bearer <api-key>` (used by OpenAI Python SDK)
  - **Anthropic style**: `x-api-key: <api-key>` (used by Anthropic Python SDK)
- **Web UI Display**: The API key is prominently displayed in the web UI with a copy button
- **Security**: Prevents unauthorized access when running on public networks

Example requests with API key:
```bash
# OpenAI style (Bearer token)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}'

# Anthropic style (x-api-key header)
curl -X POST http://localhost:8000/v1/messages \
  -H "x-api-key: YOUR_API_KEY_HERE" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-opus-20240229", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 1024}'
```

Using with official SDKs:
```python
# OpenAI SDK (automatically uses Bearer token)
from openai import OpenAI
client = OpenAI(api_key="YOUR_API_KEY", base_url="http://localhost:8000/v1")

# Anthropic SDK (automatically uses x-api-key header)
from anthropic import Anthropic
client = Anthropic(api_key="YOUR_API_KEY", base_url="http://localhost:8000/v1")
```

#### Embeddings Support
The server now supports OpenAI's embeddings API with multiple response modes:
- **Random**: Generates normalized random vectors
- **Zero**: Returns zero vectors for testing edge cases
- **Sequential**: Creates sequential pattern embeddings
- **Hash-based**: Generates deterministic embeddings based on input text
- **File-based**: Loads pre-defined embeddings from JSON files
- **Custom**: Allows manual JSON input for specific test cases

Supported models with appropriate dimensions:
- text-embedding-ada-002 (1536 dimensions)
- text-embedding-3-small (1536 dimensions)
- text-embedding-3-large (3072 dimensions)

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