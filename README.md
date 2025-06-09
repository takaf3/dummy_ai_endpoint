# dummy ai endpoint

A debugging tool that mimics both OpenAI and Anthropic APIs, allowing you to intercept requests, log prompts, and manually control responses for testing LLM-powered applications.

Perfect for debugging applications where you don't have access to the source code but need to understand what prompts are being sent and test different response scenarios.

## 🚀 Features

- **Dual API compatibility**: Supports both OpenAI and Anthropic APIs
  - OpenAI: `/v1/chat/completions` and `/v1/completions` endpoints
  - Anthropic: `/v1/messages` endpoint
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
- **Dual mode**: Choose between CLI prompts or web UI for response management

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

### Configure Your Application

Configure your application to use `http://localhost:8000` as the API base URL:

**For OpenAI:**
```python
# Using OpenAI Python library
from openai import OpenAI

client = OpenAI(
    api_key="dummy-key",  # Any string works
    base_url="http://localhost:8000/v1"
)

# Or with older openai library
import openai
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "dummy-key"
```

**For Anthropic:**
```python
# Using Anthropic Python library
from anthropic import Anthropic

client = Anthropic(
    api_key="dummy-key",  # Any string works
    base_url="http://localhost:8000"
)
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
3. Click "Send Response", "Send Default", or "Send Error"
4. View request history and details

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

## 📊 Logging

All requests are automatically logged to:

| File | Description |
|------|-------------|
| **Console** | Real-time colored output |
| **`dummy_ai_endpoint_requests.log`** | Detailed text logs |
| **`request_log.json`** | JSON format for parsing |

## 🔌 API Endpoints

| Endpoint | Method | Description | API |
|----------|--------|-------------|-----|
| `/` | GET | Server info | - |
| `/v1/models` | GET | List available models | OpenAI |
| `/v1/chat/completions` | POST | Chat completions (GPT-3.5/4) | OpenAI |
| `/v1/completions` | POST | Text completions (GPT-3) | OpenAI |
| `/v1/messages` | POST | Messages (Claude) | Anthropic |

## 🎯 Command Line Options

### Server Script
```bash
python dummy_ai_endpoint.py [OPTIONS]

Options:
  --mode {cli,web}  Response mode: 'cli' for terminal, 'web' for browser UI (default: cli)
  --port PORT       Port to run the server on (default: 8000)
  --host HOST       Host to bind the server to (default: 0.0.0.0)
```

## 💡 Use Cases

- **Debug black-box applications**: See what prompts third-party apps are sending
- **Test edge cases**: Simulate specific responses, errors, or timeouts
- **Analyze usage**: Log and analyze prompt patterns and costs
- **Development**: Test your app without burning API credits
- **Security auditing**: Inspect what data is being sent to LLMs

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Project guidance and architecture overview for Claude Code

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for debugging and development purposes only. Ensure you comply with the terms of service of any applications you're debugging.