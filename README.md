# dummy ai endpoint

A debugging tool that mimics both OpenAI and Anthropic APIs, allowing you to intercept requests, log prompts, and manually control responses for testing LLM-powered applications.

Perfect for debugging applications where you don't have access to the source code but need to understand what prompts are being sent and test different response scenarios.

## 🚀 Features

- **Dual API compatibility**: Supports both OpenAI and Anthropic APIs
  - OpenAI: `/v1/chat/completions`, `/v1/completions`, and `/v1/embeddings` endpoints
  - Anthropic: `/v1/messages` endpoint
- **Embeddings Support**: Full OpenAI embeddings API compatibility with multiple response modes
  - Random normalized vectors for general testing
  - Zero vectors for edge case testing
  - Sequential patterns for debugging
  - Hash-based deterministic embeddings
  - File-based responses from JSON
  - Custom JSON input for specific test cases
- **Multimodal Support**: Full support for images in both OpenAI and Anthropic formats
  - Base64 encoded images
  - Image URLs (OpenAI format)
  - Multiple images per message
  - Proper image display in web UI
- **Tool Use Support**: Function calling capabilities for both OpenAI and Anthropic APIs
- **Request logging**: All requests are logged to console, file, and JSON format
- **Interactive response control**: Manually input responses for each request
- **Default responses**: Quick testing with one-click/enter default responses
- **Streaming support**: Supports both streaming and non-streaming responses for both APIs
- **Token counting**: Approximates token usage similar to OpenAI and Anthropic
- **Zero configuration**: Works as a drop-in replacement for both APIs
- **Web UI**: Beautiful web interface for managing responses with proper Anthropic tool display
- **Dark Mode**: Automatic dark mode support with system preference detection and manual toggle
- **Dual mode**: Choose between CLI prompts or web UI for response management
- **Remote Mode**: Secure API key authentication for running on public networks
  - Auto-generated secure API keys
  - Compatible with both OpenAI and Anthropic authentication styles
  - API key displayed in console and web UI
- **Custom Error Responses**: Send custom HTTP error codes and messages
  - Preset error buttons for common errors (429, 500, 502, 503)
  - Custom status codes, error messages, and details
  - Perfect for testing error handling and resilience

## 📁 Project Structure

```
dummy_ai_endpoint/
├── dummy_ai_endpoint.py    # Main server application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── README.md             # This file
├── LICENSE               # MIT license
├── .gitignore           # Git ignore rules
├── static/              # Web UI assets
│   ├── index.html
│   ├── script.js
│   └── style.css
├── examples/            # Example client implementations
│   ├── example_openai_client.py
│   ├── example_anthropic_client.py
│   ├── example_anthropic_sdk.py
│   ├── example_embeddings_client.py
│   └── sample_embeddings.json
├── tests/              # Test files
│   └── test_export.py
└── test_custom_errors.py # Script to test custom error responses
```

## 📋 Requirements

- Python 3.8+
- pip

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/takaf3/dummy_ai_endpoint.git
cd dummy_ai_endpoint

# Install dependencies
pip install -r requirements.txt
```

## 🚦 Quick Start

### Running with Docker (Recommended)
1.  **Build the Docker image:**
    ```bash
    docker build -t dummy-ai-endpoint .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 --name dummy-ai-app -d dummy-ai-endpoint
    ```
    This starts the server in "web" mode. Access the UI at `http://localhost:8000`.

### Running Locally

#### CLI Mode (Default)
1. **Start the server:**
```bash
python dummy_ai_endpoint.py
```

#### Web UI Mode
1. **Start the server with web UI:**
```bash
python dummy_ai_endpoint.py --mode web
```

2. **Open your browser** to `http://localhost:8000` to access the web interface

#### Remote Mode (Secure API)
For running the server on remote/public networks with API key authentication:

1. **Start the server with remote mode:**
```bash
python dummy_ai_endpoint.py --mode web --remote
```

2. **Copy the API key** displayed in the console:
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REMOTE MODE - API KEY REQUIRED
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
API Key: YOUR_GENERATED_API_KEY_HERE

Use this API key in the Authorization header:
Authorization: Bearer YOUR_GENERATED_API_KEY_HERE
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

3. **Use the API key in your requests:**
   - The server accepts both authentication formats:
     - OpenAI style: `Authorization: Bearer <api-key>`
     - Anthropic style: `x-api-key: <api-key>`
   - The API key is also displayed in the web UI

**Docker with Remote Mode:**
```bash
# Build and run with remote mode enabled
docker build -t dummy-ai-endpoint .
docker run -p 8000:8000 dummy-ai-endpoint \
  python dummy_ai_endpoint.py --mode web --host 0.0.0.0 --port 8000 --remote

# View the API key from logs
docker logs <container-name> | grep "API Key:"
```

### Configure Your Application

Configure your application to use `http://localhost:8000` as the API base URL:

**For OpenAI:**
```python
# Using OpenAI Python library
from openai import OpenAI

client = OpenAI(
    api_key="dummy-key",  # Any string works (use real API key in remote mode)
    base_url="http://localhost:8000/v1"
)

# Or with older openai library
import openai
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "dummy-key"  # Use real API key in remote mode
```

**For Anthropic:**
```python
# Using Anthropic Python library
from anthropic import Anthropic

client = Anthropic(
    api_key="dummy-key",  # Any string works (use real API key in remote mode)
    base_url="http://localhost:8000/v1"  # Note: use /v1 for Anthropic SDK
)

# Or using raw requests (supports both auth styles in remote mode)
import requests

# OpenAI style auth
headers = {"Authorization": "Bearer YOUR_API_KEY"}

# Anthropic style auth  
headers = {"x-api-key": "YOUR_API_KEY"}
```

### Response Management

**In CLI Mode**, you'll see:
```
================================================================================
NEW REQUEST TO /v1/chat/completions
================================================================================
{
  "timestamp": "2025-01-03T10:30:45",
  "endpoint": "/v1/chat/completions",
  "request": {
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "What is the weather?"}
    ]
  }
}

Enter your response (type 'END' on a new line when done):
Or press ENTER to use default message: 'Hello! I'm the AI assistant. How can I help you today?'
```

**In Web UI Mode**, you'll:
1. See incoming requests in real-time on the web interface
2. Type your response in the text area
3. Click "Send Response", "Send Default", "Send Error", or use custom error options
4. For custom errors:
   - Enter HTTP status code (100-599)
   - Specify error message and details
   - Use preset buttons for common errors (429, 500, 502, 503)
5. View request history and details
6. Toggle between light and dark mode with the 🌙/☀️ button

### 🧪 Testing with Example Clients

The repository includes example clients to test all supported endpoints:

```bash
# Test OpenAI Chat Completions API
python examples/example_openai_client.py

# Test Anthropic Messages API  
python examples/example_anthropic_client.py

# Test OpenAI Embeddings API
python examples/example_embeddings_client.py

# Test Custom Error Responses
python test_custom_errors.py

# When using remote mode, provide the API key:
python examples/example_openai_client.py YOUR_API_KEY_HERE
# Or use environment variable:
DUMMY_AI_API_KEY=YOUR_API_KEY_HERE python examples/example_openai_client.py
```

## 📝 Example Usage

**OpenAI Example:**
```python
# example_openai_client.py
from openai import OpenAI

# Point to your mock server
client = OpenAI(api_key="test", base_url="http://localhost:8000/v1")

# Make a request - this will be intercepted
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's 2+2?"}
    ],
    stream=True  # Streaming is supported!
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

**Anthropic Example:**
```python
# example_anthropic_client.py
from anthropic import Anthropic

# Point to your mock server
client = Anthropic(api_key="test", base_url="http://localhost:8000")

# Make a request - this will be intercepted
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What's 2+2?"}
    ],
    stream=True  # Streaming is supported!
)

for chunk in response:
    if chunk.type == "content_block_delta":
        print(chunk.delta.text, end="")
```

**OpenAI Tool Use Example:**
```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1"
)

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Make request with tools
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "What's the weather in Tokyo?"}
    ],
    tools=tools,
    tool_choice="auto"
)
```

**Anthropic Tool Use Example:**
```python
from anthropic import Anthropic

client = Anthropic(
    api_key="test-key",
    base_url="http://localhost:8000"
)

# Define tools
tools = [
    {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    }
]

# Make request with tools
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "What's the weather in Tokyo?"}
    ],
    tools=tools,
    tool_choice={"type": "tool", "name": "get_weather"}
)
```

**OpenAI Multimodal Example:**
```python
from openai import OpenAI
import base64

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1"
)

# Load and encode an image
with open("image.jpg", "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    max_tokens=300
)
```

**Anthropic Multimodal Example:**
```python
from anthropic import Anthropic
import base64

client = Anthropic(
    api_key="test-key",
    base_url="http://localhost:8000"
)

# Load and encode an image
with open("image.jpg", "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in detail."
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }
    ]
)
```

**OpenAI Embeddings Example:**
```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1"
)

# Single text embedding
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="The quick brown fox jumps over the lazy dog"
)
embedding = response.data[0].embedding
print(f"Embedding dimensions: {len(embedding)}")

# Batch embeddings
texts = [
    "Machine learning is fascinating",
    "Artificial intelligence is the future",
    "I love pizza and pasta"
]
response = client.embeddings.create(
    model="text-embedding-3-large",
    input=texts
)

# When using the mock server, you can choose different response types:
# - Random: Normalized random vectors
# - Zero: All zeros (for edge case testing)
# - Sequential: Incrementing pattern
# - Hash-based: Deterministic based on input text
# - From file: Load from JSON (e.g., sample_embeddings.json)
# - Custom: Manual vector input in Web UI
```

## 📊 Logging

All requests are automatically logged to:

| File | Description |
|------|-------------|
| **Console** | Real-time colored output |
| **`dummy_ai_endpoint_requests.log`** | Detailed text logs |
| **`request_log.json`** | JSON format for parsing |

Base64 image data is automatically truncated in logs to keep them readable while still showing the media type and first few characters for identification.

## 🔌 API Endpoints

| Endpoint | Method | Description | API |
|----------|--------|-------------|-----|
| `/` | GET | Server info | - |
| `/v1/models` | GET | List available models | OpenAI |
| `/v1/chat/completions` | POST | Chat completions (GPT-3.5/4) | OpenAI |
| `/v1/completions` | POST | Text completions (GPT-3) | OpenAI |
| `/v1/embeddings` | POST | Text embeddings | OpenAI |
| `/v1/messages` | POST | Messages (Claude) | Anthropic |
| `/server_info` | GET | Detailed server information (disabled in remote mode) | - |
| `/api_key_info` | GET | API key info for web UI (web mode only) | - |
| `/ws` | WebSocket | Real-time UI communication | - |

## 🎯 Command Line Options

### Server Script
```bash
python dummy_ai_endpoint.py [OPTIONS]

Options:
  --mode {cli,web}  Response mode: 'cli' for terminal, 'web' for browser UI (default: cli)
  --port PORT       Port to run the server on (default: 8000)
  --host HOST       Host to bind the server to (default: 0.0.0.0)
  --remote          Enable remote mode with API key authentication
```

## 💡 Use Cases

- **Debug black-box applications**: See what prompts third-party apps are sending
- **Test edge cases**: Simulate specific responses, errors, or timeouts
- **Analyze usage**: Log and analyze prompt patterns and costs
- **Development**: Test your app without burning API credits
- **Security auditing**: Inspect what data is being sent to LLMs

## 📚 Additional Features

### Custom Error Responses

The web UI includes a dedicated section for sending custom error responses:

1. **Custom Status Code**: Enter any HTTP status code (100-599)
2. **Error Message**: Specify a custom error message
3. **Error Details**: Provide detailed error description
4. **Preset Error Buttons**: Quick access to common errors:
   - 503 Service Unavailable
   - 502 Bad Gateway
   - 500 Internal Server Error
   - 429 Rate Limit (via dedicated button)

This feature is perfect for:
- Testing application error handling
- Simulating rate limits and service outages
- Debugging retry logic and fallback mechanisms
- Stress testing error recovery

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Project guidance and architecture overview for Claude Code

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for debugging and development purposes only. Ensure you comply with the terms of service of any applications you're debugging.