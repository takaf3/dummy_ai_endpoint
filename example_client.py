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
        
        test_chat_completion()
        time.sleep(1)
        
        test_streaming_chat()
        time.sleep(1)
        
        test_text_completion()
        time.sleep(1)

        test_chat_completion_minimal_params()
        time.sleep(1)

        test_text_completion_minimal_params()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the mock server is running!")