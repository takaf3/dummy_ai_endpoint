#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from queue import Queue
import threading

import uvicorn
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dummy_ai_endpoint_requests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dummy AI Endpoint")

# Global state
pending_requests = {}
websocket_clients = []
response_mode = "cli"  # "cli" or "web"

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

def get_cli_response(prompt_info: str) -> str:
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

async def get_web_response(request_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get response from web UI"""
    # Store request in pending
    pending_requests[request_id] = {
        "data": request_data,
        "response": None,
        "event": asyncio.Event()
    }
    
    # Notify all connected WebSocket clients
    message = {
        "type": "new_request",
        "request": {
            "id": request_id,
            "endpoint": request_data["endpoint"],
            "data": request_data["data"]
        }
    }
    
    disconnected_clients = []
    for client in websocket_clients:
        try:
            await client.send_json(message)
        except:
            disconnected_clients.append(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        websocket_clients.remove(client)
    
    # Wait for response
    await pending_requests[request_id]["event"].wait()
    
    response = pending_requests[request_id]["response"]
    del pending_requests[request_id]
    
    return response

def count_tokens(text: str) -> int:
    """Simple token counter (approximation)"""
    return int(len(text.split()) * 1.3)  # Rough approximation

async def handle_request(endpoint: str, request_data: Dict[str, Any], stream: bool) -> Any:
    """Handle request with appropriate response mode"""
    # Create prompt info for display
    prompt_info = f"Model: {request_data.get('model', 'unknown')}\n"
    prompt_info += f"Temperature: {request_data.get('temperature', 1.0)}\n"
    prompt_info += f"Max Tokens: {request_data.get('max_tokens', 'None')}\n"
    prompt_info += f"Stream: {stream}\n"
    
    if "messages" in request_data:
        prompt_info += "\nMessages:\n"
        for msg in request_data["messages"]:
            prompt_info += f"[{msg['role']}]: {msg['content']}\n"
    elif "prompt" in request_data:
        prompt_info += f"\nPrompt: {request_data['prompt']}\n"
    
    # Get response based on mode
    if response_mode == "cli":
        user_response = get_cli_response(prompt_info)
    else:
        request_id = str(uuid.uuid4())
        web_response = await get_web_response(request_id, {
            "endpoint": endpoint,
            "data": request_data
        })
        
        if web_response.get("type") == "error":
            raise Exception(web_response.get("message", "Unknown error"))
        
        user_response = web_response.get("response", "")
    
    return user_response

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, raw_request: Request):
    """Handle chat completion requests"""
    request_dict = request.dict()
    log_request("/v1/chat/completions", request_dict)
    
    try:
        user_response = await handle_request("/v1/chat/completions", request_dict, request.stream)
    except Exception as e:
        return Response(
            content=json.dumps({"error": {"message": str(e), "type": "server_error"}}),
            status_code=500,
            media_type="application/json"
        )
    
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
    
    try:
        user_response = await handle_request("/v1/completions", request_dict, request.stream)
    except Exception as e:
        return Response(
            content=json.dumps({"error": {"message": str(e), "type": "server_error"}}),
            status_code=500,
            media_type="application/json"
        )
    
    # Calculate token usage
    prompt_text = request.prompt if isinstance(request.prompt, str) else str(request.prompt)
    prompt_tokens = count_tokens(prompt_text)
    completion_tokens = count_tokens(user_response)
    
    if request.stream:
        # Streaming response
        async def generate_stream():
            words = user_response.split()
            
            for i in range(0, len(words), 3):  # Send 3 words at a time
                chunk_content = ' '.join(words[i:i+3])
                if i + 3 < len(words):
                    chunk_content += ' '
                
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
    if response_mode == "web":
        # Redirect to web UI
        return HTMLResponse(content=open("static/index.html", "r").read())
    else:
        return {
            "message": "OpenAI API Mock Server",
            "endpoints": [
                "/v1/chat/completions",
                "/v1/completions",
                "/v1/models"
            ],
            "mode": response_mode
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication with web UI"""
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "response" and data["request_id"] in pending_requests:
                # Store the response
                pending_requests[data["request_id"]]["response"] = {
                    "type": "success",
                    "response": data["response"],
                    "stream": data.get("stream", False)
                }
                # Signal that response is ready
                pending_requests[data["request_id"]]["event"].set()
            
            elif data["type"] == "error" and data["request_id"] in pending_requests:
                # Store the error
                pending_requests[data["request_id"]]["response"] = {
                    "type": "error",
                    "message": data.get("message", "Unknown error")
                }
                # Signal that response is ready
                pending_requests[data["request_id"]]["event"].set()
    
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenAI API Mock Server")
    parser.add_argument("--mode", choices=["cli", "web"], default="cli",
                        help="Response mode: 'cli' for terminal input, 'web' for web UI")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port to run the server on")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host to bind the server to")
    
    args = parser.parse_args()
    response_mode = args.mode
    
    print("\n" + "="*80)
    print("OpenAI API Mock Server")
    print("="*80)
    print(f"Mode: {response_mode.upper()}")
    print(f"Server: http://localhost:{args.port}")
    if response_mode == "web":
        print(f"Web UI: http://localhost:{args.port}")
    print("\nThis server mimics the OpenAI API for debugging purposes.")
    print("All requests will be logged to:")
    print("  - Console output")
    print("  - openai_mock_requests.log")
    print("  - request_log.json")
    if response_mode == "cli":
        print("\nYou will be prompted to provide responses for each request.")
    else:
        print("\nOpen the web UI to manage responses.")
    print("="*80 + "\n")
    
    uvicorn.run(app, host=args.host, port=args.port)