#!/usr/bin/env python3
import asyncio
import json
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openai_mock_requests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenAI API Mock Server")

# Request/Response Models (matching OpenAI's structure)
class ChatCompletionMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str], List[int], List[List[int]]]
    suffix: Optional[str] = None
    max_tokens: Optional[int] = 16
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    best_of: Optional[int] = 1
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

def log_request(endpoint: str, request_data: Dict[str, Any]):
    """Log the incoming request details"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "request": request_data
    }
    logger.info(f"\n{'='*80}\nNEW REQUEST TO {endpoint}\n{'='*80}")
    logger.info(json.dumps(log_entry, indent=2))
    
    # Also save to a JSON file for easy parsing
    with open('request_log.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def get_user_response(prompt_info: str) -> str:
    """Get response from user via terminal"""
    print("\n" + "="*80)
    print("INTERCEPTED REQUEST - Please provide response")
    print("="*80)
    print(prompt_info)
    print("\n" + "-"*80)
    print("Enter your response (type 'END' on a new line when done):")
    
    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        lines.append(line)
    
    return '\n'.join(lines)

def count_tokens(text: str) -> int:
    """Simple token counter (approximation)"""
    return len(text.split()) * 1.3  # Rough approximation

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, raw_request: Request):
    """Handle chat completion requests"""
    request_dict = request.dict()
    log_request("/v1/chat/completions", request_dict)
    
    # Create prompt info for display
    prompt_info = f"Model: {request.model}\n"
    prompt_info += f"Temperature: {request.temperature}\n"
    prompt_info += f"Max Tokens: {request.max_tokens}\n"
    prompt_info += f"Stream: {request.stream}\n"
    prompt_info += "\nMessages:\n"
    for msg in request.messages:
        prompt_info += f"[{msg.role}]: {msg.content}\n"
    
    # Get user response
    user_response = get_user_response(prompt_info)
    
    # Calculate token usage
    prompt_tokens = sum(count_tokens(msg.content) for msg in request.messages)
    completion_tokens = count_tokens(user_response)
    
    if request.stream:
        # Streaming response
        async def generate_stream():
            # Send initial chunk
            chunk = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            
            # Send content in chunks
            words = user_response.split()
            for i in range(0, len(words), 3):  # Send 3 words at a time
                chunk_content = ' '.join(words[i:i+3])
                if i + 3 < len(words):
                    chunk_content += ' '
                
                chunk = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": chunk_content},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
            # Send final chunk
            final_chunk = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    else:
        # Non-streaming response
        response = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": user_response
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens)
            }
        }
        return response

@app.post("/v1/completions")
async def completions(request: CompletionRequest, raw_request: Request):
    """Handle completion requests"""
    request_dict = request.dict()
    log_request("/v1/completions", request_dict)
    
    # Create prompt info for display
    prompt_info = f"Model: {request.model}\n"
    prompt_info += f"Temperature: {request.temperature}\n"
    prompt_info += f"Max Tokens: {request.max_tokens}\n"
    prompt_info += f"Stream: {request.stream}\n"
    prompt_info += f"\nPrompt: {request.prompt}\n"
    
    # Get user response
    user_response = get_user_response(prompt_info)
    
    # Calculate token usage
    prompt_text = request.prompt if isinstance(request.prompt, str) else str(request.prompt)
    prompt_tokens = count_tokens(prompt_text)
    completion_tokens = count_tokens(user_response)
    
    if request.stream:
        # Streaming response
        async def generate_stream():
            words = user_response.split()
            text_so_far = ""
            
            for i in range(0, len(words), 3):  # Send 3 words at a time
                chunk_content = ' '.join(words[i:i+3])
                if i + 3 < len(words):
                    chunk_content += ' '
                text_so_far += chunk_content
                
                chunk = {
                    "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                    "object": "text_completion",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "text": chunk_content,
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
            # Send final chunk
            final_chunk = {
                "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                "object": "text_completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "text": "",
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    else:
        # Non-streaming response
        response = {
            "id": f"cmpl-{uuid.uuid4().hex[:8]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "text": user_response,
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens)
            }
        }
        return response

@app.get("/v1/models")
async def list_models():
    """List available models (mimicking OpenAI's response)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1687882411,
                "owned_by": "openai"
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai"
            },
            {
                "id": "text-davinci-003",
                "object": "model",
                "created": 1669599635,
                "owned_by": "openai-internal"
            }
        ]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenAI API Mock Server",
        "endpoints": [
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/models"
        ]
    }

if __name__ == "__main__":
    print("\n" + "="*80)
    print("OpenAI API Mock Server")
    print("="*80)
    print("This server mimics the OpenAI API for debugging purposes.")
    print("All requests will be logged to:")
    print("  - Console output")
    print("  - openai_mock_requests.log")
    print("  - request_log.json")
    print("\nYou will be prompted to provide responses for each request.")
    print("="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)