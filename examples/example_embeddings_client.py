#!/usr/bin/env python3
"""
Example client for testing OpenAI Embeddings API with the dummy endpoint.
This demonstrates how to use the /v1/embeddings endpoint.
"""

from openai import OpenAI
import numpy as np
import os
import sys
from typing import List

# Get API key from environment or command line
api_key = os.environ.get('DUMMY_AI_API_KEY') or (sys.argv[1] if len(sys.argv) > 1 else "dummy-key")

# Configure the OpenAI client to use our local endpoint
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=api_key  # Use real API key in remote mode
)

def get_embedding(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """Get embedding for a single text."""
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def get_embeddings_batch(texts: List[str], model: str = "text-embedding-ada-002") -> List[List[float]]:
    """Get embeddings for multiple texts in a batch."""
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [item.embedding for item in response.data]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def main():
    print("=== OpenAI Embeddings API Example ===")
    print("\nUsage:")
    print("  python example_embeddings_client.py [API_KEY]")
    print("  DUMMY_AI_API_KEY=your-api-key python example_embeddings_client.py")
    print("\nNote: API key is required when server is running with --remote flag\n")
    
    # Example 1: Single text embedding
    print("1. Getting embedding for a single text:")
    text1 = "The quick brown fox jumps over the lazy dog"
    embedding1 = get_embedding(text1)
    print(f"   Text: '{text1}'")
    print(f"   Embedding dimensions: {len(embedding1)}")
    print(f"   First 10 values: {embedding1[:10]}")
    print()
    
    # Example 2: Batch embeddings
    print("2. Getting embeddings for multiple texts:")
    texts = [
        "Machine learning is fascinating",
        "Artificial intelligence is the future",
        "I love pizza and pasta"
    ]
    embeddings = get_embeddings_batch(texts)
    for i, text in enumerate(texts):
        print(f"   Text {i+1}: '{text}'")
        print(f"   Embedding dimensions: {len(embeddings[i])}")
    print()
    
    # Example 3: Using different models
    print("3. Testing different embedding models:")
    models = ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
    test_text = "Testing different models"
    
    for model in models:
        try:
            embedding = get_embedding(test_text, model)
            print(f"   Model: {model}")
            print(f"   Dimensions: {len(embedding)}")
        except Exception as e:
            print(f"   Model: {model} - Error: {e}")
    print()
    
    # Example 4: Similarity comparison (if using hash-based embeddings)
    print("4. Comparing text similarity:")
    similar_texts = [
        "The weather is nice today",
        "Today's weather is pleasant",
        "I enjoy coding in Python"
    ]
    
    embeddings = get_embeddings_batch(similar_texts)
    
    print("   Cosine similarities:")
    for i in range(len(similar_texts)):
        for j in range(i+1, len(similar_texts)):
            similarity = cosine_similarity(embeddings[i], embeddings[j])
            print(f"   '{similar_texts[i]}' <-> '{similar_texts[j]}'")
            print(f"   Similarity: {similarity:.4f}")
    print()
    
    # Example 5: Custom dimensions (if supported)
    print("5. Testing custom dimensions:")
    try:
        response = client.embeddings.create(
            input="Custom dimension test",
            model="text-embedding-3-large",
            dimensions=1024  # Request specific dimensions
        )
        embedding = response.data[0].embedding
        print(f"   Requested dimensions: 1024")
        print(f"   Actual dimensions: {len(embedding)}")
    except Exception as e:
        print(f"   Error with custom dimensions: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure the dummy AI endpoint is running on http://localhost:8000")