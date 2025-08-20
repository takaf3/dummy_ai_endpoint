#!/usr/bin/env python3
"""Simple test for advanced mode"""

from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8001/v1"
)

print("Making a test request to see raw HTTP output...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, test message"}
    ],
    temperature=0.7,
    max_tokens=100
)

print(f"Response received: {response.choices[0].message.content}")