#!/usr/bin/env python3
"""
Quick test script to verify Anthropic tool display in web UI
"""

import requests
import json

# Simple weather tool test
weather_tool = {
    "name": "get_weather",
    "description": "Get the current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and state/country"
            }
        },
        "required": ["location"]
    }
}

# Make request with tool
headers = {
    "x-api-key": "test-key",
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

data = {
    "model": "claude-3-opus-20240229",
    "messages": [
        {"role": "user", "content": "What's the weather in Tokyo?"}
    ],
    "max_tokens": 100,
    "tools": [weather_tool],
    "tool_choice": {"type": "tool", "name": "get_weather"}
}

print("Sending Anthropic API request with tools...")
print("Check the web UI to see if tools display correctly!")
print("\nRequest data:")
print(json.dumps(data, indent=2))

try:
    response = requests.post(
        "http://localhost:8000/v1/messages",
        headers=headers,
        json=data
    )
    print(f"\nResponse status: {response.status_code}")
except Exception as e:
    print(f"\nError: {e}")
    print("Make sure the server is running in web mode: python dummy_ai_endpoint.py --mode web")