#!/usr/bin/env python3
"""
Example client showing how to use the OpenAI API Mock Server
"""

from openai import OpenAI
import time

def test_chat_completion():
    """Test chat completion endpoint"""
    print("\n=== Testing Chat Completion ===")
    
    # Configure client to use mock server
    client = OpenAI(
        api_key="test-key",  # Any string works
        base_url="http://localhost:8000/v1"
    )
    
    # Make a chat completion request
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the capital of France?"}
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}")

def test_streaming_chat():
    """Test streaming chat completion"""
    print("\n=== Testing Streaming Chat ===")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )
    
    # Make a streaming request
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Tell me a short joke"}
        ],
        stream=True
    )
    
    print("Streaming response: ", end="")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
    print("\n")

def test_text_completion():
    """Test legacy text completion endpoint"""
    print("\n=== Testing Text Completion ===")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )
    
    # Make a completion request
    response = client.completions.create(
        model="text-davinci-003",
        prompt="The meaning of life is",
        max_tokens=50,
        temperature=0.9
    )
    
    print(f"Response: {response.choices[0].text}")

def test_chat_completion_minimal_params():
    """Test chat completion endpoint with minimal parameters"""
    print("\n=== Testing Chat Completion (Minimal Params) ===")

    # Configure client to use mock server
    client = OpenAI(
        api_key="test-key",  # Any string works
        base_url="http://localhost:8000/v1"
    )

    # Make a chat completion request with only required parameters
    response = client.chat.completions.create(
        model="gpt-4-minimal",  # Using a distinct model name for clarity in logs
        messages=[
            {"role": "user", "content": "Minimal test: What is your model name?"}
        ]
    )

    print(f"Response: {response.choices[0].message.content}")
    # Usage data might not be fully populated if not sent, server dependent
    if response.usage:
        print(f"Tokens used: {response.usage.total_tokens}")
    else:
        print("Usage data not available in response.")

def test_text_completion_minimal_params():
    """Test legacy text completion endpoint with minimal parameters"""
    print("\n=== Testing Text Completion (Minimal Params) ===")

    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )

    # Make a completion request with only required parameters
    response = client.completions.create(
        model="text-davinci-minimal", # Using a distinct model name for clarity in logs
        prompt="Minimal legacy test: respond with your model name."
    )

    print(f"Response: {response.choices[0].text}")

def test_tool_use_basic():
    """Test basic tool use functionality"""
    print("\n=== Testing Basic Tool Use ===")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )
    
    # Define a simple weather tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "What's the weather like in Tokyo?"}
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    print(f"Response: {response.choices[0].message.content}")
    if response.choices[0].message.tool_calls:
        print(f"Tool calls: {len(response.choices[0].message.tool_calls)}")
        for tool_call in response.choices[0].message.tool_calls:
            print(f"  - Function: {tool_call.function.name}")
            print(f"  - Arguments: {tool_call.function.arguments}")

def test_tool_use_forced():
    """Test forced tool choice"""
    print("\n=== Testing Forced Tool Choice ===")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )
    
    # Define a calculator tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform basic arithmetic calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Calculate 15 * 23"}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "calculate"}}
    )
    
    print(f"Response: {response.choices[0].message.content}")
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            print(f"Forced tool call - Function: {tool_call.function.name}")
            print(f"Arguments: {tool_call.function.arguments}")

def test_tool_use_multiple():
    """Test multiple tools available"""
    print("\n=== Testing Multiple Tools ===")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )
    
    # Define multiple tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "Get the current time for a timezone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone name (e.g., 'America/New_York')"
                        }
                    },
                    "required": ["timezone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "What time is it in New York?"}
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    print(f"Response: {response.choices[0].message.content}")
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            print(f"Selected tool: {tool_call.function.name}")
            print(f"Arguments: {tool_call.function.arguments}")

def test_tool_use_conversation():
    """Test tool use in a conversation flow"""
    print("\n=== Testing Tool Use in Conversation ===")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )
    
    # Define a file operations tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Name of the file to read"
                        }
                    },
                    "required": ["filename"]
                }
            }
        }
    ]
    
    # Initial request
    messages = [
        {"role": "user", "content": "Can you read the config.json file?"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    # Add assistant's response to conversation
    messages.append(response.choices[0].message)
    
    # Simulate tool result
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            print(f"Tool called: {tool_call.function.name}")
            print(f"Arguments: {tool_call.function.arguments}")
            
            # Add tool result to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": '{"database_url": "localhost:5432", "api_key": "secret123"}'
            })
    
    # Continue conversation with tool result
    final_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    
    print(f"Final response: {final_response.choices[0].message.content}")

def test_models_endpoint():
    """Test models listing endpoint"""
    print("\n=== Testing Models Endpoint ===")
    
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000/v1"
    )
    
    # List available models
    models = client.models.list()
    
    print("Available models:")
    for model in models.data:
        print(f"  - {model.id}")

if __name__ == "__main__":
    print("OpenAI API Mock Server - Example Client")
    print("Make sure the mock server is running on http://localhost:8000")
    print("="*50)
    
    try:
        # Test different endpoints
        test_models_endpoint()
        time.sleep(1)
        
        # Basic functionality tests
        test_chat_completion()
        time.sleep(1)
        
        test_streaming_chat()
        time.sleep(1)
        
        test_text_completion()
        time.sleep(1)

        test_chat_completion_minimal_params()
        time.sleep(1)

        test_text_completion_minimal_params()
        time.sleep(1)
        
        # Tool use functionality tests
        test_tool_use_basic()
        time.sleep(1)
        
        test_tool_use_forced()
        time.sleep(1)
        
        test_tool_use_multiple()
        time.sleep(1)
        
        test_tool_use_conversation()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the mock server is running!")