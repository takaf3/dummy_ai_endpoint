#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import sys
import copy
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

app = FastAPI(title="Dummy AI Endpoint - OpenAI & Anthropic Compatible")

# Global state
pending_requests = {}
websocket_clients = []
response_mode = "cli"  # "cli" or "web"

# Request/Response Models (matching OpenAI's structure)
class ChatCompletionMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]  # Support both text and multimodal content
    name: Optional[str] = None

# Anthropic API Models
class AnthropicMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

class AnthropicRequest(BaseModel):
    model: str
    messages: List[AnthropicMessage]
    max_tokens: int
    system: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    stream: Optional[bool] = None
    stop_sequences: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Dict[str, Any]] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = None
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, Any]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, str]] = None
    seed: Optional[int] = None

class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str], List[int], List[List[int]]]
    suffix: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = None
    logprobs: Optional[int] = None
    echo: Optional[bool] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    best_of: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    seed: Optional[int] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

def log_request(endpoint: str, request_data: Dict[str, Any]):
    """Log the incoming request details, truncating base64 data in logs."""
    # Create a deep copy to avoid modifying the original request data
    request_data_copy = copy.deepcopy(request_data)

    # Truncate base64 data in the copy
    if "messages" in request_data_copy:
        for message in request_data_copy["messages"]:
            if isinstance(message.get("content"), list):
                for content_item in message["content"]:
                    if not isinstance(content_item, dict):
                        continue

                    # OpenAI image_url format
                    if content_item.get("type") == "image_url":
                        image_url_dict = content_item.get("image_url", {})
                        if isinstance(image_url_dict, dict):
                            url = image_url_dict.get("url", "")
                            if url.startswith("data:") and ";base64," in url:
                                parts = url.split(";base64,", 1)
                                if len(parts) == 2:
                                    media_type_part = parts[0]
                                    base64_string = parts[1]
                                    if len(base64_string) > 30:
                                        truncated_base64 = base64_string[:30] + "... (truncated)"
                                        image_url_dict["url"] = f"{media_type_part};base64,{truncated_base64}"

                    # Anthropic image format
                    elif content_item.get("type") == "image":
                        source = content_item.get("source", {})
                        if isinstance(source, dict) and source.get("type") == "base64":
                            base64_string = source.get("data", "")
                            if len(base64_string) > 30:
                                source["data"] = base64_string[:30] + "... (truncated)"

    log_entry_copy = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "request": request_data_copy  # Use the modified copy for logging
    }
    logger.info(f"\n{'='*80}\nNEW REQUEST TO {endpoint}\n{'='*80}")
    logger.info(json.dumps(log_entry_copy, indent=2))
    
    # Also save to a JSON file for easy parsing, using the modified copy
    with open('request_log.json', 'a') as f:
        f.write(json.dumps(log_entry_copy) + '\n')

def get_cli_response(prompt_info: str) -> str:
    """Get response from user via terminal"""
    print("\n" + "="*80)
    print("INTERCEPTED REQUEST - Please provide response")
    print("="*80)
    print(prompt_info)
    print("\n" + "-"*80)
    print("Enter your response (type 'END' on a new line when done):")
    print("Or press ENTER to use default message: 'Hello! I'm the AI assistant. How can I help you today?'")
    
    lines = []
    first_line = True
    while True:
        line = input()
        if first_line and line.strip() == '':
            # User pressed enter immediately - use default message
            return "Hello! I'm the AI assistant. How can I help you today?"
        first_line = False
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

async def handle_request(endpoint: str, request_data: Dict[str, Any], stream: Optional[bool]) -> Any:
    """Handle request with appropriate response mode"""
    # Create prompt info for display
    prompt_info = f"Endpoint: {endpoint}\n"
    prompt_info += f"Model: {request_data.get('model', 'unknown')}\n"
    prompt_info += f"Temperature: {request_data.get('temperature', 1.0)}\n"
    prompt_info += f"Max Tokens: {request_data.get('max_tokens', 'None')}\n"
    prompt_info += f"Stream: {stream}\n"
    
    # Handle Anthropic-specific fields
    if "Anthropic" in endpoint:
        if "system" in request_data and request_data["system"]:
            prompt_info += f"\nSystem: {request_data['system']}\n"
        if "top_k" in request_data and request_data["top_k"] is not None:
            prompt_info += f"Top K: {request_data['top_k']}\n"
        if "stop_sequences" in request_data and request_data["stop_sequences"]:
            prompt_info += f"Stop Sequences: {request_data['stop_sequences']}\n"
    
    if "messages" in request_data:
        prompt_info += "\nMessages:\n"
        for msg in request_data["messages"]:
            content = msg['content']
            # Handle structured content (multimodal)
            if isinstance(content, list):
                formatted_content = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            formatted_content.append(item.get('text', ''))
                        elif item.get('type') == 'image':
                            # Handle Anthropic format
                            source = item.get('source', {})
                            if source.get('type') == 'base64':
                                base64_data = source.get('data', '')
                                truncated_base64 = base64_data[:30]
                                formatted_content.append(f"[IMAGE: {source.get('media_type', 'unknown')} - base64 data: {truncated_base64}... (truncated)]")
                            else:
                                formatted_content.append(f"[IMAGE: {item}]")
                        elif item.get('type') == 'image_url':
                            # Handle OpenAI format
                            image_url = item.get('image_url', {})
                            if isinstance(image_url, dict):
                                url = image_url.get('url', '')
                                if url.startswith('data:'):
                                    # Base64 image
                                    media_type = url.split(';')[0].split(':')[1] if ';' in url else 'unknown'
                                    base64_data = url.split(',')[-1] if ',' in url else ''
                                    truncated_base64 = base64_data[:30]
                                    formatted_content.append(f"[IMAGE: {media_type} - base64 data: {truncated_base64}... (truncated)]")
                                else:
                                    formatted_content.append(f"[IMAGE URL: {url}]")
                            else:
                                formatted_content.append(f"[IMAGE URL: {image_url}]")
                        else:
                            formatted_content.append(str(item))
                    else:
                        formatted_content.append(str(item))
                content = '\n'.join(formatted_content)
            prompt_info += f"[{msg['role']}]: {content}\n"
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
        stream_param = request.stream if request.stream is not None else False
        user_response = await handle_request("/v1/chat/completions", request_dict, stream_param)
    except Exception as e:
        return Response(
            content=json.dumps({"error": {"message": str(e), "type": "server_error"}}),
            status_code=500,
            media_type="application/json"
        )
    
    # Calculate token usage
    prompt_tokens = 0
    for msg in request.messages:
        if isinstance(msg.content, str):
            prompt_tokens += count_tokens(msg.content)
        elif isinstance(msg.content, list):
            # Handle multimodal content
            for item in msg.content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        prompt_tokens += count_tokens(item.get('text', ''))
                    elif item.get('type') in ['image', 'image_url']:
                        # Approximate tokens for images (OpenAI typically uses ~85 tokens per image)
                        prompt_tokens += 85
                else:
                    prompt_tokens += count_tokens(str(item))
    completion_tokens = count_tokens(user_response)
    
    if stream_param:
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
        stream_param = request.stream if request.stream is not None else False
        user_response = await handle_request("/v1/completions", request_dict, stream_param)
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
    
    if stream_param:
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

@app.post("/v1/messages")
async def anthropic_messages(request: AnthropicRequest, raw_request: Request):
    """Handle Anthropic messages API requests"""
    request_dict = request.dict()
    log_request("/v1/messages (Anthropic)", request_dict)
    
    try:
        stream_param = request.stream if request.stream is not None else False
        user_response = await handle_request("/v1/messages (Anthropic)", request_dict, stream_param)
    except Exception as e:
        return Response(
            content=json.dumps({"error": {"type": "error", "message": str(e)}}),
            status_code=400,
            media_type="application/json"
        )
    
    # Calculate token usage (approximation)
    prompt_tokens = 0
    if request.system:
        prompt_tokens += count_tokens(request.system)
    for msg in request.messages:
        if isinstance(msg.content, str):
            prompt_tokens += count_tokens(msg.content)
        elif isinstance(msg.content, list):
            # Handle structured content (multimodal)
            for item in msg.content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        prompt_tokens += count_tokens(item.get('text', ''))
                    elif item.get('type') == 'image':
                        # Approximate tokens for images
                        prompt_tokens += 85
                else:
                    prompt_tokens += count_tokens(str(item))
    
    completion_tokens = count_tokens(user_response)
    
    if stream_param:
        # Streaming response for Anthropic
        async def generate_anthropic_stream():
            # Send initial message_start event
            start_event = {
                "type": "message_start",
                "message": {
                    "id": f"msg_{uuid.uuid4().hex[:24]}",
                    "type": "message",
                    "role": "assistant",
                    "content": [],
                    "model": request.model,
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {
                        "input_tokens": int(prompt_tokens),
                        "output_tokens": 0
                    }
                }
            }
            yield f"event: message_start\ndata: {json.dumps(start_event)}\n\n"
            
            # Send content_block_start
            content_start = {
                "type": "content_block_start",
                "index": 0,
                "content_block": {
                    "type": "text",
                    "text": ""
                }
            }
            yield f"event: content_block_start\ndata: {json.dumps(content_start)}\n\n"
            
            # Send content in chunks
            words = user_response.split()
            output_tokens = 0
            for i in range(0, len(words), 3):  # Send 3 words at a time
                chunk_content = ' '.join(words[i:i+3])
                if i + 3 < len(words):
                    chunk_content += ' '
                
                output_tokens += count_tokens(chunk_content)
                
                delta_event = {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {
                        "type": "text_delta",
                        "text": chunk_content
                    }
                }
                yield f"event: content_block_delta\ndata: {json.dumps(delta_event)}\n\n"
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
            # Send content_block_stop
            content_stop = {
                "type": "content_block_stop",
                "index": 0
            }
            yield f"event: content_block_stop\ndata: {json.dumps(content_stop)}\n\n"
            
            # Send message_delta with final usage
            delta_event = {
                "type": "message_delta",
                "delta": {
                    "stop_reason": "end_turn",
                    "stop_sequence": None
                },
                "usage": {
                    "output_tokens": int(completion_tokens)
                }
            }
            yield f"event: message_delta\ndata: {json.dumps(delta_event)}\n\n"
            
            # Send message_stop
            stop_event = {"type": "message_stop"}
            yield f"event: message_stop\ndata: {json.dumps(stop_event)}\n\n"
        
        return StreamingResponse(generate_anthropic_stream(), media_type="text/event-stream")
    else:
        # Non-streaming response
        response = {
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": user_response
                }
            ],
            "model": request.model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": int(prompt_tokens),
                "output_tokens": int(completion_tokens)
            }
        }
        return response

@app.get("/")
async def root():
    """Root endpoint"""
    if response_mode == "web":
        # Redirect to web UI
        return HTMLResponse(content=open("static/index.html", "r").read())
    else:
        return {
            "message": "OpenAI & Anthropic API Mock Server",
            "endpoints": [
                "/v1/chat/completions (OpenAI)",
                "/v1/completions (OpenAI)",
                "/v1/models (OpenAI)",
                "/v1/messages (Anthropic)"
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
    print("OpenAI & Anthropic API Mock Server")
    print("="*80)
    print(f"Mode: {response_mode.upper()}")
    print(f"Server: http://localhost:{args.port}")
    if response_mode == "web":
        print(f"Web UI: http://localhost:{args.port}")
    print("\nThis server mimics OpenAI and Anthropic APIs for debugging purposes.")
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