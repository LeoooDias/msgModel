# Using `stream_panels()` for Chat Applications

> **Available in msgmodel v4.1.0+**

The `stream_panels()` function provides structured streaming events designed for building chat UIs. It exposes the `finish_reason` from LLM providers, enabling you to detect when responses are truncated due to token limits.

## Quick Start

```python
from msgmodel import stream_panels

for event in stream_panels("openai", "Tell me a story"):
    if event["event"] == "panel_delta":
        print(event["delta"], end="", flush=True)
    elif event["event"] == "panel_final":
        print(f"\n\nFinish reason: {event['finish_reason']}")
```

## Event Types

### `panel_delta` - Text Chunks

Emitted for each text chunk as it streams from the provider.

```python
{
    "event": "panel_delta",
    "panel_id": "a1b2c3d4",
    "delta": "Hello"  # The text chunk
}
```

### `panel_final` - Stream Complete

Emitted once when the stream completes successfully.

```python
{
    "event": "panel_final",
    "panel_id": "a1b2c3d4",
    "content": "Hello, world!",      # Full accumulated response
    "privacy": {                      # Provider privacy metadata
        "provider": "openai",
        "training_retention": False,
        ...
    },
    "finish_reason": "stop"           # Why the response ended
}
```

### `panel_error` - Error Occurred

Emitted if an error occurs during streaming (instead of raising an exception).

```python
{
    "event": "panel_error",
    "panel_id": "a1b2c3d4",
    "error": "Rate limit exceeded",
    "error_type": "APIError"
}
```

## Detecting Truncation

The primary use case for `finish_reason` is detecting when a response was cut off due to the `max_tokens` limit.

### Truncation Values by Provider

| Provider | Normal Completion | Truncated | Content Filtered |
|----------|-------------------|-----------|------------------|
| OpenAI | `"stop"` | `"length"` | `"content_filter"` |
| Anthropic | `"end_turn"` | `"max_tokens"` | — |
| Gemini | `"STOP"` | `"MAX_TOKENS"` | `"SAFETY"` |

### Example: Warn Users About Truncation

```python
from msgmodel import stream_panels

TRUNCATION_REASONS = {"length", "max_tokens", "MAX_TOKENS"}

def stream_with_truncation_warning(provider: str, prompt: str, max_tokens: int = 500):
    """Stream a response and warn if truncated."""
    content_parts = []
    
    for event in stream_panels(provider, prompt, max_tokens=max_tokens):
        if event["event"] == "panel_delta":
            content_parts.append(event["delta"])
            yield event["delta"]
            
        elif event["event"] == "panel_final":
            if event["finish_reason"] in TRUNCATION_REASONS:
                yield "\n\n⚠️ **Response truncated** - the model reached the token limit."
                
        elif event["event"] == "panel_error":
            yield f"\n\n❌ Error: {event['error']}"

# Usage
for chunk in stream_with_truncation_warning("openai", "Write a long essay", max_tokens=100):
    print(chunk, end="", flush=True)
```

## Async Support

Use `astream_panels()` for async applications:

```python
import asyncio
from msgmodel import astream_panels

async def chat_response(prompt: str):
    async for event in astream_panels("anthropic", prompt):
        if event["event"] == "panel_delta":
            print(event["delta"], end="", flush=True)
        elif event["event"] == "panel_final":
            if event["finish_reason"] == "max_tokens":
                print("\n[Response was truncated]")

asyncio.run(chat_response("Explain quantum computing"))
```

## Full Chat Application Example

Here's a more complete example for a chat application:

```python
from msgmodel import stream_panels
from dataclasses import dataclass
from typing import Generator

@dataclass
class ChatMessage:
    role: str
    content: str
    truncated: bool = False
    finish_reason: str | None = None

TRUNCATION_REASONS = {"length", "max_tokens", "MAX_TOKENS"}

def generate_response(
    provider: str,
    prompt: str,
    system_instruction: str | None = None,
    max_tokens: int = 1000,
) -> Generator[str, None, ChatMessage]:
    """
    Stream an LLM response, yielding chunks and returning final message.
    
    Usage:
        gen = generate_response("openai", "Hello!")
        for chunk in gen:
            display(chunk)  # Update UI with each chunk
        
        # After iteration, get the final message via .send(None) or next()
        # Or catch StopIteration to get the return value
    """
    content_parts = []
    finish_reason = None
    error = None
    
    for event in stream_panels(
        provider,
        prompt,
        system_instruction=system_instruction,
        max_tokens=max_tokens,
    ):
        match event["event"]:
            case "panel_delta":
                content_parts.append(event["delta"])
                yield event["delta"]
                
            case "panel_final":
                finish_reason = event["finish_reason"]
                
            case "panel_error":
                error = event["error"]
                yield f"\n\n[Error: {error}]"
    
    # Return the complete message
    return ChatMessage(
        role="assistant",
        content="".join(content_parts),
        truncated=finish_reason in TRUNCATION_REASONS,
        finish_reason=finish_reason,
    )


def chat_loop():
    """Simple interactive chat loop."""
    print("Chat started. Type 'quit' to exit.\n")
    
    history: list[ChatMessage] = []
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        
        history.append(ChatMessage(role="user", content=user_input))
        
        print("Assistant: ", end="", flush=True)
        
        gen = generate_response("openai", user_input, max_tokens=500)
        
        # Consume the generator to stream output
        try:
            while True:
                chunk = next(gen)
                print(chunk, end="", flush=True)
        except StopIteration as e:
            message: ChatMessage = e.value
            history.append(message)
            
            if message.truncated:
                print("\n⚠️  [Response was truncated due to token limit]", end="")
        
        print("\n")

if __name__ == "__main__":
    chat_loop()
```

## FastAPI/Starlette SSE Example

For web applications using Server-Sent Events:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from msgmodel import stream_panels
import json

app = FastAPI()

@app.post("/chat/stream")
async def stream_chat(prompt: str, provider: str = "openai"):
    """Stream chat response as Server-Sent Events."""
    
    async def event_generator():
        for event in stream_panels(provider, prompt, max_tokens=1000):
            # Format as SSE
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

Client-side JavaScript:

```javascript
const eventSource = new EventSource('/chat/stream?prompt=Hello');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.event) {
        case 'panel_delta':
            appendToChat(data.delta);
            break;
            
        case 'panel_final':
            if (['length', 'max_tokens', 'MAX_TOKENS'].includes(data.finish_reason)) {
                showTruncationWarning();
            }
            eventSource.close();
            break;
            
        case 'panel_error':
            showError(data.error);
            eventSource.close();
            break;
    }
};
```

## Custom Panel IDs

You can provide your own `panel_id` for tracking multiple concurrent streams:

```python
import uuid

panel_id = str(uuid.uuid4())

for event in stream_panels("openai", prompt, panel_id=panel_id):
    # All events will have this panel_id
    assert event["panel_id"] == panel_id
```

## API Reference

### `stream_panels()`

```python
def stream_panels(
    provider: str,                    # "openai", "anthropic", "gemini" (or "o", "a", "g")
    prompt: str,                      # User prompt
    api_key: str | None = None,       # API key (or use env var)
    system_instruction: str | None = None,
    file_like: BytesIO | None = None, # For file uploads
    filename: str | None = None,      # Filename hint for MIME detection
    config: ProviderConfig | None = None,
    max_tokens: int | None = None,    # Override max tokens
    model: str | None = None,         # Override model
    temperature: float | None = None, # Override temperature
    timeout: float = 300,             # Request timeout
    panel_id: str | None = None,      # Custom panel identifier
) -> Iterator[dict]
```

### `astream_panels()`

Same signature as `stream_panels()`, but returns `AsyncIterator[dict]`.

## Migration from `stream()`

If you're currently using `stream()` and want the panel events:

```python
# Before (stream)
for chunk in stream("openai", prompt):
    print(chunk, end="")

# After (stream_panels)
for event in stream_panels("openai", prompt):
    if event["event"] == "panel_delta":
        print(event["delta"], end="")
    elif event["event"] == "panel_final":
        # Now you have access to finish_reason!
        if event["finish_reason"] == "length":
            print("\n[Truncated]")
```

The original `stream()` function remains unchanged for backward compatibility.
