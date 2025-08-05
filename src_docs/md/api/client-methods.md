---
# this_file: src_docs/md/api/client-methods.md
title: Client Methods Reference
description: Complete reference for all ClaudeClient methods and parameters
---

# Client Methods Reference

This page provides comprehensive documentation for all methods available in the `ClaudeClient` class.

## ClaudeClient Class

### Constructor

```python
ClaudeClient(
    api_key: str | None = None,
    timeout: int = 120,
    max_retries: int = 3,
    **kwargs
)
```

**Parameters:**

- `api_key` (str, optional): Anthropic API key. If not provided, uses `ANTHROPIC_API_KEY` environment variable.
- `timeout` (int, default=120): Request timeout in seconds.
- `max_retries` (int, default=3): Maximum number of retry attempts for failed requests.
- `**kwargs`: Additional parameters passed to the underlying client.

**Example:**

```python
from claif_cla import ClaudeClient

# Basic initialization
client = ClaudeClient()

# With custom configuration
client = ClaudeClient(
    api_key="your-api-key",
    timeout=300,
    max_retries=5
)
```

## Chat Completions

### chat.completions.create()

The primary method for generating chat completions using Claude models.

```python
client.chat.completions.create(
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stop: str | List[str] | None = None,
    stream: bool = False,
    user: str | None = None,
    tools: List[Dict[str, Any]] | None = None,
    tool_choice: str | Dict[str, Any] | None = None,
    **kwargs
) -> ChatCompletion | Iterator[ChatCompletionChunk]
```

#### Parameters

##### Required Parameters

**`model`** (str)
- The Claude model to use for completion
- Available models:
  - `claude-3-5-sonnet-20241022` - Latest and most capable
  - `claude-3-opus-20240229` - Most intelligent, best for complex tasks
  - `claude-3-sonnet-20240229` - Balanced performance
  - `claude-3-haiku-20240307` - Fastest and most economical

**`messages`** (List[Dict[str, Any]])
- Array of message objects representing the conversation
- Each message must have `role` and `content` fields
- Supported roles: `system`, `user`, `assistant`

##### Optional Parameters

**`temperature`** (float, default=0.7, range=0.0-1.0)
- Controls randomness in output generation
- Lower values = more deterministic
- Higher values = more creative/random

**`max_tokens`** (int, optional)
- Maximum number of tokens to generate
- If not specified, uses model's default limit
- Actual limit depends on model and context

**`top_p`** (float, default=1.0, range=0.0-1.0)
- Nucleus sampling parameter
- Controls diversity by filtering less likely tokens
- Lower values = more focused responses

**`frequency_penalty`** (float, default=0.0, range=-2.0-2.0)
- Reduces likelihood of repeating tokens based on frequency
- Positive values discourage repetition

**`presence_penalty`** (float, default=0.0, range=-2.0-2.0)
- Reduces likelihood of repeating topics
- Positive values encourage diverse topics

**`stop`** (str | List[str], optional)
- Sequences where generation should stop
- Can be a single string or list of strings
- Generation stops when any sequence is encountered

**`stream`** (bool, default=False)
- Whether to stream the response
- If True, returns an iterator of chunks
- If False, returns complete response

**`user`** (str, optional)
- Identifier for the user making the request
- Used for abuse monitoring and tracking

**`tools`** (List[Dict[str, Any]], optional)
- Array of tool definitions for function calling
- Each tool defines available functions the model can call

**`tool_choice`** (str | Dict[str, Any], optional)
- Controls which tools the model can use
- Options: `"auto"`, `"none"`, or specific tool selection

#### Examples

##### Basic Completion

```python
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(response.choices[0].message.content)
```

##### System Message with Parameters

```python
response = client.chat.completions.create(
    model="claude-3-opus-20240229",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to sort a list."}
    ],
    temperature=0.3,
    max_tokens=500,
    stop=["```", "END"]
)
```

##### Streaming Response

```python
stream = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Tell me a story."}
    ],
    stream=True,
    temperature=0.8
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

##### Conversation with History

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"},
]

# First response
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages
)

# Add response to history
messages.append({
    "role": "assistant", 
    "content": response.choices[0].message.content
})

# Continue conversation
messages.append({
    "role": "user", 
    "content": "Can you give me an example?"
})

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages
)
```

##### Tool/Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Handle tool calls in response
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        print(f"Tool called: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")
```

##### Multi-modal Input (Vision)

```python
# For models that support vision
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
                    }
                }
            ]
        }
    ]
)
```

## Response Handling

### Synchronous Responses

```python
response = client.chat.completions.create(...)

# Access response content
content = response.choices[0].message.content
role = response.choices[0].message.role
finish_reason = response.choices[0].finish_reason

# Access metadata
model_used = response.model
response_id = response.id
created_timestamp = response.created

# Access usage information
prompt_tokens = response.usage.prompt_tokens
completion_tokens = response.usage.completion_tokens
total_tokens = response.usage.total_tokens
```

### Streaming Responses

```python
stream = client.chat.completions.create(..., stream=True)

full_content = ""
for chunk in stream:
    # Check if chunk has content
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        full_content += content
        print(content, end="", flush=True)
    
    # Check for completion
    if chunk.choices[0].finish_reason:
        print(f"\nFinished: {chunk.choices[0].finish_reason}")
        break
```

## Error Handling

### Exception Types

All exceptions follow OpenAI's error hierarchy:

```python
from openai import (
    OpenAIError,           # Base exception
    APIError,              # API-related errors
    AuthenticationError,   # Invalid API key
    PermissionDeniedError, # Insufficient permissions
    RateLimitError,        # Rate limit exceeded
    BadRequestError,       # Invalid request
    ConflictError,         # Request conflicts
    NotFoundError,         # Resource not found
    UnprocessableEntityError, # Invalid parameters
    InternalServerError,   # Server errors
    APIConnectionError,    # Connection issues
    APITimeoutError       # Request timeout
)
```

### Error Handling Patterns

```python
from openai import OpenAIError, RateLimitError, AuthenticationError

try:
    response = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # Implement backoff strategy
except APIError as e:
    print(f"API error: {e.status_code} - {e.message}")
except OpenAIError as e:
    print(f"OpenAI error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Advanced Usage Patterns

### Retry Logic with Backoff

```python
import time
import random
from openai import RateLimitError, APIError

def create_with_retry(client, max_retries=3, **kwargs):
    """Create completion with exponential backoff retry"""
    
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError:
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limited, retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if attempt < max_retries - 1 and e.status_code >= 500:
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"Server error, retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                raise

# Usage
response = create_with_retry(
    client,
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}],
    max_retries=5
)
```

### Batch Processing

```python
def process_batch(client, prompts, model="claude-3-haiku-20240307"):
    """Process multiple prompts efficiently"""
    
    results = []
    for i, prompt in enumerate(prompts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            results.append({
                "index": i,
                "prompt": prompt,
                "response": response.choices[0].message.content,
                "tokens": response.usage.total_tokens
            })
        except Exception as e:
            results.append({
                "index": i,
                "prompt": prompt,
                "error": str(e),
                "response": None
            })
    
    return results

# Usage
prompts = [
    "What is Python?",
    "What is JavaScript?",
    "What is machine learning?"
]

results = process_batch(client, prompts)
for result in results:
    if result["response"]:
        print(f"Q: {result['prompt']}")
        print(f"A: {result['response'][:100]}...")
        print(f"Tokens: {result['tokens']}\n")
```

### Response Validation

```python
def validate_and_extract(response, expected_format="text"):
    """Validate response and extract content safely"""
    
    # Check response structure
    if not response.choices:
        raise ValueError("No choices in response")
    
    choice = response.choices[0]
    
    # Check for errors
    if choice.finish_reason == "content_filter":
        raise ValueError("Content filtered by safety system")
    
    # Extract content
    content = choice.message.content
    if not content:
        raise ValueError("Empty response content")
    
    # Validate format if specified
    if expected_format == "json":
        try:
            import json
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("Response is not valid JSON")
    
    return content

# Usage
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Return a JSON object with name and age"}]
)

try:
    data = validate_and_extract(response, expected_format="json")
    print(f"Parsed data: {data}")
except ValueError as e:
    print(f"Validation error: {e}")
```

## Performance Optimization

### Model Selection Strategy

```python
def select_optimal_model(task_type, complexity, budget="medium"):
    """Select best model for task requirements"""
    
    if budget == "low" or task_type == "simple":
        return "claude-3-haiku-20240307"
    
    if complexity == "high" or task_type in ["analysis", "reasoning", "creative"]:
        return "claude-3-opus-20240229"
    
    # Default balanced choice
    return "claude-3-5-sonnet-20241022"

# Usage
model = select_optimal_model("analysis", "high", "medium")
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Analyze this complex data..."}]
)
```

### Streaming for Long Responses

```python
def stream_long_response(client, messages, **kwargs):
    """Handle long responses with streaming"""
    
    # Force streaming for better UX
    kwargs["stream"] = True
    
    stream = client.chat.completions.create(
        messages=messages,
        **kwargs
    )
    
    chunks = []
    full_response = ""
    
    try:
        for chunk in stream:
            chunks.append(chunk)
            
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                
                # Process content in real-time
                yield content
                
            if chunk.choices[0].finish_reason:
                break
                
    except Exception as e:
        print(f"Streaming error: {e}")
        raise
    
    # Return final response info
    if chunks:
        last_chunk = chunks[-1]
        return {
            "content": full_response,
            "finish_reason": last_chunk.choices[0].finish_reason,
            "model": last_chunk.model,
            "chunks": len(chunks)
        }

# Usage
for content_chunk in stream_long_response(
    client,
    messages=[{"role": "user", "content": "Write a long essay..."}],
    model="claude-3-5-sonnet-20241022"
):
    print(content_chunk, end="", flush=True)
```

## Next Steps

- **[Response Types](response-types.md)** - Detailed response object reference
- **[Error Handling](error-handling.md)** - Comprehensive error management
- **[Session Management](../sessions/overview.md)** - Stateful conversation handling

This reference covers all available methods and patterns for using the ClaudeClient effectively! 🚀