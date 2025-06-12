#!/usr/bin/env python3
"""
Example client for testing the Anthropic API mock endpoint.
This demonstrates how to make requests to the Anthropic Messages API.
"""

import json
import requests
import base64
import os
import sys
from typing import Optional, List, Dict, Any, Union

# Configuration
BASE_URL = "http://localhost:8000"
ANTHROPIC_API_KEY = os.environ.get('DUMMY_AI_API_KEY') or (sys.argv[1] if len(sys.argv) > 1 else "mock-api-key")


def create_message(
    messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]],
    model: str = "claude-3-opus-20240229",
    max_tokens: int = 1024,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    stream: bool = False,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[Dict[str, Any]] = None,
) -> Union[Dict[str, Any], None]:
    """Send a message to the Anthropic Messages API."""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,  # Standard Anthropic header - works with remote mode
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    # Note: Our server accepts both 'x-api-key' (Anthropic style) and 
    # 'Authorization: Bearer' (OpenAI style) in remote mode
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    
    if system:
        data["system"] = system
    if temperature is not None:
        data["temperature"] = temperature
    if stream:
        data["stream"] = stream
    if tools:
        data["tools"] = tools
    if tool_choice:
        data["tool_choice"] = tool_choice
    
    try:
        if stream:
            # Streaming response
            response = requests.post(
                f"{BASE_URL}/v1/messages",
                headers=headers,
                json=data,
                stream=True
            )
            response.raise_for_status()
            
            print("Streaming response:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        try:
                            event_data = json.loads(data_str)
                            if event_data.get("type") == "content_block_delta":
                                print(event_data["delta"]["text"], end='', flush=True)
                        except json.JSONDecodeError:
                            pass
            print("\n")
            return None
        else:
            # Non-streaming response
            response = requests.post(
                f"{BASE_URL}/v1/messages",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {e.response.text}")
        return None


def main():
    """Run example requests."""
    print("=" * 80)
    print("Anthropic API Mock Client Example")
    print("=" * 80)
    print(f"Using endpoint: {BASE_URL}/v1/messages")
    print("Make sure the mock server is running!")
    print("\nUsage:")
    print("  python example_anthropic_client.py [API_KEY]")
    print("  DUMMY_AI_API_KEY=your-api-key python example_anthropic_client.py")
    print("\nNote: API key is required when server is running with --remote flag")
    print("=" * 80)
    
    # Example 1: Simple message
    print("\n1. Simple message example:")
    print("-" * 40)
    
    response = create_message(
        messages=[
            {"role": "user", "content": "Hello, Claude! How are you today?"}
        ],
        max_tokens=150,
        temperature=0.7
    )
    
    if response:
        print("Response received:")
        print(f"ID: {response['id']}")
        print(f"Model: {response['model']}")
        print(f"Content: {response['content'][0]['text']}")
        print(f"Input tokens: {response['usage']['input_tokens']}")
        print(f"Output tokens: {response['usage']['output_tokens']}")
    
    # Example 2: Message with system prompt
    print("\n\n2. Message with system prompt:")
    print("-" * 40)
    
    response = create_message(
        messages=[
            {"role": "user", "content": "Write a haiku about Python programming."}
        ],
        system="You are a helpful AI assistant who loves poetry and programming.",
        max_tokens=100,
        temperature=0.9
    )
    
    if response:
        print("Response received:")
        print(f"Content: {response['content'][0]['text']}")
    
    # Example 3: Multi-turn conversation
    print("\n\n3. Multi-turn conversation:")
    print("-" * 40)
    
    conversation = [
        {"role": "user", "content": "What's the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What's the population of that city?"}
    ]
    
    response = create_message(
        messages=conversation,
        max_tokens=200,
        temperature=0.3
    )
    
    if response:
        print("Response received:")
        print(f"Content: {response['content'][0]['text']}")
    
    # Example 4: Streaming response
    print("\n\n4. Streaming response example:")
    print("-" * 40)
    
    create_message(
        messages=[
            {"role": "user", "content": "Tell me a short story about a robot learning to paint."}
        ],
        max_tokens=300,
        temperature=0.8,
        stream=True
    )
    
    # Example 5: Tool use - Weather function
    print("\n\n5. Tool use example - Weather function:")
    print("-" * 40)
    
    # Define a weather tool
    weather_tool = {
        "name": "get_weather",
        "description": "Get the current weather for a specific location. This tool provides temperature, conditions, and other weather information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state/country for the weather query (e.g., 'San Francisco, CA' or 'London, UK')"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit preference",
                    "default": "fahrenheit"
                }
            },
            "required": ["location"]
        }
    }
    
    response = create_message(
        messages=[
            {"role": "user", "content": "What's the weather like in Tokyo, Japan?"}
        ],
        tools=[weather_tool],
        max_tokens=300
    )
    
    if response:
        print("Response received:")
        print(f"Content: {response['content']}")
        
        # Check if Claude wants to use a tool
        for content_block in response['content']:
            if content_block.get('type') == 'tool_use':
                print(f"\nTool call detected:")
                print(f"Tool: {content_block['name']}")
                print(f"Input: {content_block['input']}")
                print(f"Tool ID: {content_block['id']}")
    
    # Example 6: Tool use with forced tool choice
    print("\n\n6. Tool use with forced tool choice:")
    print("-" * 40)
    
    # Define a calculator tool
    calculator_tool = {
        "name": "calculate",
        "description": "Perform mathematical calculations. Supports basic arithmetic operations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')"
                }
            },
            "required": ["expression"]
        }
    }
    
    response = create_message(
        messages=[
            {"role": "user", "content": "What is 15 * 23 + 7?"}
        ],
        tools=[calculator_tool],
        tool_choice={"type": "tool", "name": "calculate"},
        max_tokens=200
    )
    
    if response:
        print("Response received:")
        for content_block in response['content']:
            if content_block.get('type') == 'tool_use':
                print(f"Forced tool call:")
                print(f"Tool: {content_block['name']}")
                print(f"Expression: {content_block['input']['expression']}")
    
    # Example 7: Multiple tools available
    print("\n\n7. Multiple tools example:")
    print("-" * 40)
    
    # Define multiple tools
    search_tool = {
        "name": "web_search",
        "description": "Search the web for current information on any topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find information"
                }
            },
            "required": ["query"]
        }
    }
    
    file_tool = {
        "name": "read_file",
        "description": "Read the contents of a file from the local filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["file_path"]
        }
    }
    
    response = create_message(
        messages=[
            {"role": "user", "content": "I need to find information about the latest Python version. Can you help?"}
        ],
        tools=[weather_tool, calculator_tool, search_tool, file_tool],
        max_tokens=300
    )
    
    if response:
        print("Response received:")
        for content_block in response['content']:
            if content_block.get('type') == 'tool_use':
                print(f"\nSelected tool: {content_block['name']}")
                print(f"Input: {content_block['input']}")
            elif content_block.get('type') == 'text':
                print(f"Text response: {content_block['text']}")
    
    # Example 8: Tool use conversation with tool results
    print("\n\n8. Tool use conversation with results:")
    print("-" * 40)
    
    # Simulate a conversation where we provide tool results
    conversation_with_tools = [
        {"role": "user", "content": "What's the weather in Paris and what's 25 * 4?"},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I'll help you get the weather in Paris and calculate 25 * 4. Let me use the appropriate tools."
                },
                {
                    "type": "tool_use",
                    "id": "toolu_01A09q90qw90lkasdjfl",
                    "name": "get_weather",
                    "input": {"location": "Paris, France", "unit": "celsius"}
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01A09q90qw90lkasdjfl",
                    "content": "Weather in Paris, France: 18°C, partly cloudy with light winds"
                }
            ]
        }
    ]
    
    response = create_message(
        messages=conversation_with_tools,
        tools=[weather_tool, calculator_tool],
        max_tokens=300
    )
    
    if response:
        print("Response after tool result:")
        for content_block in response['content']:
            if content_block.get('type') == 'tool_use':
                print(f"Next tool call: {content_block['name']}")
                print(f"Input: {content_block['input']}")
            elif content_block.get('type') == 'text':
                print(f"Text: {content_block['text']}")
    
    # Example 9: Multimodal with base64 image
    print("\n\n9. Multimodal example - Base64 image:")
    print("-" * 40)
    
    # Create a simple 1x1 red pixel PNG as base64
    red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    response = create_message(
        messages=[
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": "What color is this image?"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": red_pixel_base64
                        }
                    }
                ]
            }
        ],
        model="claude-3-opus-20240229",
        max_tokens=100
    )
    
    if response:
        print("Response received:")
        print(f"Content: {response['content'][0]['text']}")
    
    # Example 10: Multiple images and text
    print("\n\n10. Multimodal example - Multiple images:")
    print("-" * 40)
    
    # Create two different colored pixels
    blue_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    response = create_message(
        messages=[
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": "I'm showing you two images. The first image is:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": red_pixel_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "And the second image is:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": blue_pixel_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Can you compare the colors in these two images?"
                    }
                ]
            }
        ],
        model="claude-3-opus-20240229",
        max_tokens=150
    )
    
    if response:
        print("Response received:")
        print(f"Content: {response['content'][0]['text']}")
    
    # Example 11: Multimodal conversation
    print("\n\n11. Multimodal conversation example:")
    print("-" * 40)
    
    # Create a green pixel
    green_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    multimodal_conversation = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I'm going to show you some colored pixels. Here's the first one:"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": red_pixel_base64
                    }
                }
            ]
        },
        {
            "role": "assistant",
            "content": "I can see a red pixel in the image you've shown me."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Good! Now here's another one. What color is this?"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": green_pixel_base64
                    }
                }
            ]
        }
    ]
    
    response = create_message(
        messages=multimodal_conversation,
        model="claude-3-sonnet-20240229",
        max_tokens=100
    )
    
    if response:
        print("Response received:")
        print(f"Content: {response['content'][0]['text']}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("\nTool use examples demonstrate:")
    print("- Basic tool definition and usage")
    print("- Forced tool choice")
    print("- Multiple tools selection")
    print("- Tool result handling in conversations")
    print("\nMultimodal examples demonstrate:")
    print("- Single image with text")
    print("- Multiple images in one message")
    print("- Multimodal conversations")
    print("=" * 80)


if __name__ == "__main__":
    main()