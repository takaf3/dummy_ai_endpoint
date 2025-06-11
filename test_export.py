#!/usr/bin/env python3
"""
Test script to send a few sample requests to the dummy AI endpoint
to verify the export functionality in the web UI.
"""

import requests
import time

BASE_URL = "http://localhost:8001"

# Test requests
test_requests = [
    {
        "endpoint": "/v1/chat/completions",
        "data": {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            "temperature": 0.7,
            "max_tokens": 100,
            "stream": False
        }
    },
    {
        "endpoint": "/v1/messages",
        "data": {
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": "Explain quantum computing in simple terms."}
            ],
            "system": "You are a physics teacher.",
            "max_tokens": 200,
            "temperature": 0.5
        }
    },
    {
        "endpoint": "/v1/chat/completions",
        "data": {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="}}
                ]}
            ],
            "max_tokens": 150,
            "stream": True
        }
    }
]

def send_test_requests():
    print("Sending test requests to dummy AI endpoint...")
    print("Please respond to these requests in the Web UI to test export functionality.\n")
    
    for i, test in enumerate(test_requests, 1):
        print(f"Sending request {i}/{len(test_requests)}...")
        try:
            response = requests.post(
                f"{BASE_URL}{test['endpoint']}",
                json=test["data"],
                headers={"Content-Type": "application/json"},
                timeout=30  # Allow time for manual response
            )
            print(f"  Response status: {response.status_code}")
            if response.status_code == 200:
                print("  Response received successfully!")
            else:
                print(f"  Error: {response.text}")
        except requests.exceptions.Timeout:
            print("  Request timed out (this is expected if you didn't respond in the UI)")
        except Exception as e:
            print(f"  Error: {str(e)}")
        
        # Brief pause between requests
        if i < len(test_requests):
            time.sleep(2)
    
    print("\nAll test requests sent!")
    print("You can now test the export functionality in the Web UI:")
    print("1. Click 'Export JSON' to download requests as JSON")
    print("2. Click 'Export CSV' to download requests as CSV")

if __name__ == "__main__":
    send_test_requests()