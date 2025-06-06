#!/usr/bin/env python3
"""
Example client for testing the Anthropic API mock endpoint.
This demonstrates how to make requests to the Anthropic Messages API.
"""

import json
import requests
from typing import Optional, List, Dict, Any, Union

# Configuration
BASE_URL = "http://localhost:8000"
ANTHROPIC_API_KEY = "mock-api-key"  # Not validated by mock server


def create_message(
    messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]],
    model: str = "claude-3-opus-20240229",
    max_tokens: int = 1024,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    stream: bool = False,
) -> Union[Dict[str, Any], None]:
    """Send a message to the Anthropic Messages API."""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    
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
    
    # Example 5: Structured content (multimodal placeholder)
    print("\n\n5. Structured content example:")
    print("-" * 40)
    
    response = create_message(
        messages=[
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": "What do you see in this image?"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": "base64_encoded_image_data_here"
                        }
                    }
                ]
            }
        ],
        max_tokens=200
    )
    
    if response:
        print("Response received:")
        print(f"Content: {response['content'][0]['text']}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()