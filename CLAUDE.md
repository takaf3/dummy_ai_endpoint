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

### macOS Menu Bar App
```bash
# Run the menu bar application
python menubar_app.py
```

The menu bar app provides:
- Server start/stop control with visual status indicator
- Mode switching between CLI and Web UI
- Quick access to the web interface
- Log file viewing
- Server configuration (port, host)

## Architecture Overview

This is a FastAPI-based mock server that mimics both OpenAI and Anthropic APIs, intercepting requests and allowing manual response control. The application operates in two modes:

### Core Components

- **`dummy_ai_endpoint.py`**: Main server file containing all API endpoints and response handling logic
- **`menubar_app.py`**: macOS menu bar application for controlling the server
- **`static/`**: Web UI assets (HTML, CSS, JS) for the web mode interface
- **`example_openai_client.py`**: Demonstration client showing how to interact with the OpenAI API mock
- **`example_anthropic_client.py`**: Demonstration client showing how to interact with the Anthropic API mock

### Dual Response Modes

The server supports two response modes controlled by the `--mode` flag:

1. **CLI Mode (`--mode cli`)**: Default mode where responses are entered via terminal input
2. **Web Mode (`--mode web`)**: Browser-based UI for managing responses via WebSocket communication

### API Compatibility

The server mimics both OpenAI and Anthropic API structures:

**OpenAI API Endpoints:**
- `/v1/chat/completions` - Chat completion endpoint (GPT-3.5/4 style)
- `/v1/completions` - Legacy text completion endpoint (GPT-3 style)
- `/v1/models` - Model listing endpoint

**Anthropic API Endpoints:**
- `/v1/messages` - Messages endpoint (Claude style)

Both APIs support:
- Streaming and non-streaming responses
- Token counting approximation
- All standard parameters for each API

### Request Flow

1. Client makes request to mock server
2. Request is logged to console, file (`dummy_ai_endpoint_requests.log`), and JSON (`request_log.json`)
3. Server waits for manual response input (CLI or web UI)
4. Server returns formatted response matching OpenAI's structure

### Global State Management

- `pending_requests`: Dictionary storing active web UI requests awaiting responses
- `websocket_clients`: List of connected WebSocket clients for real-time updates
- `response_mode`: Current mode ("cli" or "web")

### Logging System

All requests are automatically logged in multiple formats:
- Console output with colored formatting
- Text file: `dummy_ai_endpoint_requests.log`
- JSON file: `request_log.json` for programmatic parsing

The server uses Python's standard logging module with both file and console handlers configured.