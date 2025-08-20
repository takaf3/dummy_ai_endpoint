#!/usr/bin/env python3
"""Test web mode with advanced flag"""

from openai import OpenAI
import time

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8002/v1"
)

print("Making a test request to web mode with advanced flag...")
print("Check the web UI at http://localhost:8002 to see the raw HTTP request")
print("Waiting 3 seconds before sending request...")
time.sleep(3)

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test message for web UI with advanced mode"}
        ],
        temperature=0.5,
        max_tokens=50,
        timeout=10  # Set timeout to avoid hanging
    )
    print(f"Response received: {response.choices[0].message.content}")
except Exception as e:
    print(f"Request timed out or error: {e}")
    print("Please check the web UI to respond to the request")