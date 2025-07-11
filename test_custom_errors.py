#!/usr/bin/env python3
"""
Test script to demonstrate the custom error functionality
"""

import requests
import json
import time

def test_custom_error():
    """Test the custom error functionality"""
    
    print("🚀 Testing Custom Error Functionality")
    print("=" * 50)
    
    # Test 1: Make a request that will be intercepted
    print("\n1. Making a test request to trigger the web UI...")
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello, this is a test"}],
                "max_tokens": 50
            },
            timeout=10
        )
        
        print(f"✅ Request sent successfully!")
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Body: {response.text[:200]}...")
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (expected - waiting for web UI response)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Open your browser and go to: http://localhost:8000")
    print("2. You should see the incoming request in the web UI")
    print("3. In the 'Custom Error Response' section:")
    print("   - Enter any HTTP status code (e.g., 503, 502, 429)")
    print("   - Enter an error message (e.g., 'Service Unavailable')")
    print("   - Enter error details")
    print("   - Click 'Send Custom Error' or use the preset buttons")
    print("4. The client will receive your custom error response!")
    print("\n💡 Try these examples:")
    print("   - 503 Service Unavailable")
    print("   - 429 Rate Limit Exceeded") 
    print("   - 502 Bad Gateway")
    print("   - 404 Not Found")
    print("   - 403 Forbidden")
    print("=" * 50)

if __name__ == "__main__":
    test_custom_error()