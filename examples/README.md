# Example Clients

This directory contains example client implementations demonstrating how to interact with the Dummy AI Endpoint server.

## Available Examples

### OpenAI API Examples
- **`example_openai_client.py`** - Comprehensive examples of OpenAI API usage including:
  - Chat completions (with streaming)
  - Legacy completions API
  - Tool/function calling
  - Multimodal requests (with images)
  - Minimal parameter requests

### Anthropic API Examples  
- **`example_anthropic_client.py`** - Raw HTTP requests to Anthropic API including:
  - Basic message requests
  - System prompts
  - Tool use
  - Streaming responses
  - Multimodal content
  
- **`example_anthropic_sdk.py`** - Using the official Anthropic Python SDK

### Embeddings API
- **`example_embeddings_client.py`** - OpenAI embeddings API examples:
  - Single text embedding
  - Batch embeddings
  - Different embedding models
  - Similarity calculations

### Sample Data
- **`sample_embeddings.json`** - Example embeddings response file for testing file-based embedding responses

## Running the Examples

Make sure the dummy AI endpoint server is running first:
```bash
# From the project root
python dummy_ai_endpoint.py --mode web
```

Then run any example:
```bash
# From the project root
python examples/example_openai_client.py

# With API key (for remote mode)
python examples/example_openai_client.py YOUR_API_KEY
# or
DUMMY_AI_API_KEY=YOUR_API_KEY python examples/example_openai_client.py
```

## Authentication

When the server is running in remote mode (`--remote` flag), you need to provide the API key:

1. **Command line argument**: `python examples/example_openai_client.py YOUR_API_KEY`
2. **Environment variable**: `DUMMY_AI_API_KEY=YOUR_API_KEY python examples/example_openai_client.py`

The examples automatically handle both authentication methods:
- OpenAI style: `Authorization: Bearer <api-key>`
- Anthropic style: `x-api-key: <api-key>`