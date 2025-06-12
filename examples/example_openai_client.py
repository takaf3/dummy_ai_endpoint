#!/usr/bin/env python3
"""
Example client showing how to use the OpenAI API Mock Server
"""

from openai import OpenAI
import time
import base64
import os
import sys

def get_client():
    """Get OpenAI client with proper API key
    
    The OpenAI client automatically sends the API key as 'Authorization: Bearer <api-key>'
    which is compatible with our remote mode authentication.
    """
    api_key = os.environ.get('DUMMY_AI_API_KEY') or (sys.argv[1] if len(sys.argv) > 1 else "test-key")
    return OpenAI(
        api_key=api_key,
        base_url="http://localhost:8000/v1"
    )

def test_chat_completion():
    """Test chat completion endpoint"""
    print("\n=== Testing Chat Completion ===")
    
    # Configure client to use mock server
    client = get_client()
    
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
    
    client = get_client()
    
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
    
    client = get_client()
    
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
    client = get_client()

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

    client = get_client()

    # Make a completion request with only required parameters
    response = client.completions.create(
        model="text-davinci-minimal", # Using a distinct model name for clarity in logs
        prompt="Minimal legacy test: respond with your model name."
    )

    print(f"Response: {response.choices[0].text}")

def test_tool_use_basic():
    """Test basic tool use functionality"""
    print("\n=== Testing Basic Tool Use ===")
    
    client = get_client()
    
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
    
    client = get_client()
    
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
    
    client = get_client()
    
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
    
    client = get_client()
    
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
    
    client = get_client()
    
    # List available models
    models = client.models.list()
    
    print("Available models:")
    for model in models.data:
        print(f"  - {model.id}")

def test_multimodal_base64():
    """Test multimodal chat with base64 encoded image"""
    print("\n=== Testing Multimodal Chat (Base64 Image) ===")
    
    client = get_client()
    
    # Create a simple 1x1 red pixel PNG as base64
    # This is a minimal valid PNG image
    red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What color is this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{red_pixel_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=100
    )
    
    print(f"Response: {response.choices[0].message.content}")

def test_multimodal_url():
    """Test multimodal chat with image URL"""
    print("\n=== Testing Multimodal Chat (Image URL) ===")
    
    client = get_client()
    
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://example.com/sample-image.jpg"
                        }
                    }
                ]
            }
        ],
        max_tokens=200
    )
    
    print(f"Response: {response.choices[0].message.content}")

def test_multimodal_multiple():
    """Test multimodal chat with multiple images and text"""
    print("\n=== Testing Multimodal Chat (Multiple Images) ===")
    
    client = get_client()
    
    # Create two different colored pixels
    red_pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    blue_pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "I'm showing you two images. Compare the colors in these images."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{red_pixel}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "versus"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{blue_pixel}"
                        }
                    }
                ]
            }
        ],
        max_tokens=150
    )
    
    print(f"Response: {response.choices[0].message.content}")

if __name__ == "__main__":
    print("OpenAI API Mock Server - Example Client")
    print("Make sure the mock server is running on http://localhost:8000")
    print("\nUsage:")
    print("  python example_openai_client.py [API_KEY]")
    print("  DUMMY_AI_API_KEY=your-api-key python example_openai_client.py")
    print("\nNote: API key is required when server is running with --remote flag")
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
        time.sleep(1)
        
        # Multimodal functionality tests
        test_multimodal_base64()
        time.sleep(1)
        
        test_multimodal_url()
        time.sleep(1)
        
        test_multimodal_multiple()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the mock server is running!")