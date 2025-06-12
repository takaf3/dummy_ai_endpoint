#\!/usr/bin/env python3
"""
Example showing how to use the official Anthropic SDK with the dummy endpoint in remote mode.
"""

from anthropic import Anthropic
import os
import sys

# Get API key from environment or command line
api_key = os.environ.get("DUMMY_AI_API_KEY") or (sys.argv[1] if len(sys.argv) > 1 else "test-key")

# Initialize the Anthropic client
# The Anthropic SDK sends the API key as "x-api-key" header, which is supported by our remote mode
client = Anthropic(
    api_key=api_key,
    base_url="http://localhost:8000/v1"  # Point to our mock server
)

def test_anthropic_sdk():
    """Test using the official Anthropic SDK"""
    print("=== Testing with Official Anthropic SDK ===")
    print("Note: The Anthropic SDK sends API key as 'x-api-key' header")
    print("Our server accepts both 'x-api-key' and 'Authorization: Bearer' formats\n")
    
    try:
        # Create a message using the SDK
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "Hello, Claude\!"}
            ]
        )
        
        print(f"Response: {response.content[0].text}")
        print(f"\nModel: {response.model}")
        print(f"Usage: {response.usage}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. The dummy server is running")
        print("2. If using --remote mode, provide the correct API key")

if __name__ == "__main__":
    print("\nUsage:")
    print("  python example_anthropic_sdk.py [API_KEY]")
    print("  DUMMY_AI_API_KEY=your-api-key python example_anthropic_sdk.py")
    print("\nNote: Install the Anthropic SDK first: pip install anthropic")
    print("=" * 60)
    
    test_anthropic_sdk()

