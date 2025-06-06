# dummy ai endpoint

A debugging tool that mimics both OpenAI and Anthropic APIs, allowing you to intercept requests, log prompts, and manually control responses for testing LLM-powered applications.

Perfect for debugging applications where you don't have access to the source code but need to understand what prompts are being sent and test different response scenarios.

**Now with a macOS menu bar app for easy control!** 🎉

## 🚀 Features

- **Dual API compatibility**: Supports both OpenAI and Anthropic APIs
  - OpenAI: `/v1/chat/completions` and `/v1/completions` endpoints
  - Anthropic: `/v1/messages` endpoint
- **Request logging**: All requests are logged to console, file, and JSON format
- **Interactive response control**: Manually input responses for each request
- **Streaming support**: Supports both streaming and non-streaming responses for both APIs
- **Token counting**: Approximates token usage similar to OpenAI and Anthropic
- **Zero configuration**: Works as a drop-in replacement for both APIs
- **Web UI**: Beautiful web interface for managing responses (optional)
- **Dual mode**: Choose between CLI prompts or web UI for response management
- **macOS Menu Bar App**: Control the server directly from your menu bar (start/stop, mode selection, log viewing)

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

### macOS Menu Bar App (Recommended for macOS)
1. **Run the menu bar app:**
```bash
python menubar_app.py
```

2. **Control from your menu bar:**
   - Click the 🤖 icon in your menu bar
   - Select "Start Server" to begin
   - Choose between CLI or Web UI mode
   - Access logs and settings directly from the menu

### CLI Mode (Default)
1. **Start the server:**
```bash
python dummy_ai_endpoint.py
```

### Web UI Mode
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
```

**In Web UI Mode**, you'll:
1. See incoming requests in real-time on the web interface
2. Type your response in the text area
3. Click "Send Response" or "Send Error"
4. View request history and details

## 📝 Example Usage

**OpenAI Example:**
```python
# example_client.py
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

### Menu Bar App (macOS)
```bash
python menubar_app.py
```

The menu bar app provides:
- **Server Control**: Start/stop the server with one click
- **Mode Selection**: Switch between CLI and Web UI modes
- **Status Indicator**: Green ✅ when running, red 🔴 when stopped
- **Quick Web UI Access**: Open the web interface directly
- **Log Viewer**: View recent logs or open in Console.app
- **Port Configuration**: Change the server port from the menu
- **About Info**: View app information and version

## 💡 Use Cases

- **Debug black-box applications**: See what prompts third-party apps are sending
- **Test edge cases**: Simulate specific responses, errors, or timeouts
- **Analyze usage**: Log and analyze prompt patterns and costs
- **Development**: Test your app without burning API credits
- **Security auditing**: Inspect what data is being sent to LLMs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for debugging and development purposes only. Ensure you comply with the terms of service of any applications you're debugging.