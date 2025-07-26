# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based debugging tool that intercepts and mocks OpenAI and Anthropic API calls. It provides both CLI and web interfaces for crafting custom responses to AI API requests.

## Development Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies using uv
uv pip install -r requirements.txt
```

### Running the Server
```bash
# CLI mode (default) - respond to requests in terminal
python dummy_ai_endpoint.py

# Web UI mode - respond via browser interface
python dummy_ai_endpoint.py --mode web

# Remote mode with API authentication
python dummy_ai_endpoint.py --mode web --remote

# Custom port/host
python dummy_ai_endpoint.py --mode web --port 9000 --host 127.0.0.1
```

### Testing
```bash
# Test OpenAI compatibility
python examples/example_openai_client.py

# Test Anthropic compatibility
python examples/example_anthropic_client.py

# Test embeddings
python examples/example_embeddings_client.py

# Test export functionality
python tests/test_export.py
```

### Docker Operations
```bash
# Build image
docker build -t dummy-ai-endpoint .

# Run container
docker run -p 8000:8000 --name dummy-ai-app -d dummy-ai-endpoint

# View logs
docker logs dummy-ai-app
```

## Architecture

### Core Stack
- **Backend**: FastAPI with Uvicorn ASGI server
- **WebSocket**: Native FastAPI WebSocket support for real-time UI updates
- **Data Validation**: Pydantic v2 models
- **Frontend**: Vanilla JavaScript with WebSocket client (no build process)

### Key Files
- `dummy_ai_endpoint.py`: Main FastAPI application containing all server logic
- `static/`: Web UI files (index.html, script.js, style.css)
- `examples/`: Client implementations for testing different APIs

### API Endpoints
- `/v1/chat/completions` - OpenAI chat completions
- `/v1/completions` - OpenAI text completions  
- `/v1/embeddings` - OpenAI embeddings API
- `/v1/messages` - Anthropic messages API
- `/v1/models` - Model listing
- `/ws` - WebSocket endpoint for UI communication

### Response Modes
1. **CLI Mode**: Prompts for responses in terminal
2. **Web Mode**: Browser-based UI at http://localhost:8000
3. **Remote Mode**: Requires API key authentication for public deployment

### Important Implementation Details
- Supports both streaming (SSE) and non-streaming responses
- Handles multimodal inputs (text + images) for both OpenAI and Anthropic formats
- Tool/function calling support with proper schema validation
- Request logging to console, file, and JSON
- No database - all state is in-memory
- WebSocket handles UI state synchronization and export functionality