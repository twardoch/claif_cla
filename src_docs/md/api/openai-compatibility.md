---
# this_file: src_docs/md/api/openai-compatibility.md
title: Chapter 2 - OpenAI Client Compatibility
description: Deep dive into OpenAI API compatibility, method mappings, and migration strategies
---

# Chapter 2: OpenAI Client Compatibility

claif_cla provides full compatibility with the OpenAI Python client API, allowing you to use Claude models with the same familiar interface you're already using for OpenAI models.

## Overview

The OpenAI compatibility layer is designed as a **drop-in replacement** that:

- ✅ Maintains identical method signatures
- ✅ Returns compatible response objects
- ✅ Preserves error handling patterns
- ✅ Supports all common parameters
- ✅ Enables easy migration from OpenAI

## Core Compatibility

### Method Mapping

| OpenAI Method | claif_cla Equivalent | Status |
|---------------|---------------------|---------|
| `client.chat.completions.create()` | `client.chat.completions.create()` | ✅ Full |
| `client.chat.completions.create(stream=True)` | `client.chat.completions.create(stream=True)` | ✅ Full |
| Response objects | Compatible `ChatCompletion` objects | ✅ Full |
| Error types | OpenAI-compatible exceptions | ✅ Full |

### Parameter Support

| Parameter | OpenAI | claif_cla | Notes |
|-----------|---------|-----------|-------|
| `model` | ✅ | ✅ | Maps to Claude model names |
| `messages` | ✅ | ✅ | Full message format support |
| `temperature` | ✅ | ✅ | 0.0-1.0 range |
| `max_tokens` | ✅ | ✅ | Controls response length |
| `stream` | ✅ | ✅ | Real-time streaming |
| `top_p` | ✅ | ✅ | Nucleus sampling |
| `frequency_penalty` | ✅ | ⚠️ | Mapped to Claude equivalents |
| `presence_penalty` | ✅ | ⚠️ | Mapped to Claude equivalents |
| `stop` | ✅ | ✅ | Stop sequences |
| `logit_bias` | ✅ | ❌ | Not supported by Claude |
| `user` | ✅ | ✅ | For tracking/abuse monitoring |

## Client Initialization

### Basic Setup

```python
from claif_cla import ClaudeClient

# Standard initialization
client = ClaudeClient()

# With custom API key
client = ClaudeClient(api_key="your-api-key")

# With custom configuration
client = ClaudeClient(
    api_key="your-api-key",
    timeout=300,  # 5 minutes
    max_retries=3
)
```

### Drop-in Replacement Pattern

```python
# Replace this OpenAI code:
# from openai import OpenAI
# client = OpenAI(api_key="sk-...")

# With this claif_cla code:
from claif_cla import ClaudeClient as OpenAI
client = OpenAI(api_key="your-anthropic-key")

# All your existing code works unchanged!
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",  # Just change the model
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Import Alias Pattern

```python
# For cleaner migration
try:
    from openai import OpenAI
    USE_OPENAI = True
except ImportError:
    from claif_cla import ClaudeClient as OpenAI
    USE_OPENAI = False

# Universal client initialization
if USE_OPENAI:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    client = OpenAI(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Same code works for both!
response = client.chat.completions.create(...)
```

## Message Format Compatibility

### Standard Message Structure

```python
# Both OpenAI and claif_cla support this format
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    },
    {
        "role": "user", 
        "content": "What is machine learning?"
    },
    {
        "role": "assistant",
        "content": "Machine learning is..."
    },
    {
        "role": "user",
        "content": "Can you give an example?"
    }
]

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages
)
```

### Advanced Message Features

```python
# Multi-modal messages (if supported by model)
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,..."}
            }
        ]
    }
]

# Function calling (mapped to Claude's tool use)
messages = [
    {
        "role": "user",
        "content": "What's the weather like in San Francisco?"
    }
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }
]

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages,
    tools=tools
)
```

## Response Object Compatibility

### ChatCompletion Object

```python
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Standard OpenAI response structure
print(response.id)                           # Unique response ID
print(response.object)                       # "chat.completion"
print(response.created)                      # Unix timestamp
print(response.model)                        # Model used
print(response.choices[0].message.role)      # "assistant"
print(response.choices[0].message.content)   # Response text
print(response.choices[0].finish_reason)     # "stop", "length", etc.
print(response.usage.prompt_tokens)          # Input tokens
print(response.usage.completion_tokens)      # Output tokens
print(response.usage.total_tokens)           # Total tokens
```

### Streaming Response Compatibility

```python
stream = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True
)

# Process streaming chunks
for chunk in stream:
    # Standard OpenAI streaming format
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    
    # Access chunk metadata
    print(f"Chunk ID: {chunk.id}")
    print(f"Created: {chunk.created}")
    print(f"Model: {chunk.model}")
    print(f"Finish reason: {chunk.choices[0].finish_reason}")
```

## Model Name Mapping

### Claude Model Names

```python
# Available Claude models through OpenAI interface
CLAUDE_MODELS = {
    # Latest and most capable
    "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (Latest)",
    
    # High intelligence
    "claude-3-opus-20240229": "Claude 3 Opus (Most Intelligent)",
    
    # Balanced performance
    "claude-3-sonnet-20240229": "Claude 3 Sonnet (Balanced)",
    
    # Fast and economical
    "claude-3-haiku-20240307": "Claude 3 Haiku (Fastest)"
}

# Usage patterns
fast_model = "claude-3-haiku-20240307"      # For simple tasks
balanced_model = "claude-3-5-sonnet-20241022"  # For most tasks
smart_model = "claude-3-opus-20240229"      # For complex reasoning
```

### Model Selection Guidelines

```python
def select_model(task_complexity: str, speed_priority: bool = False) -> str:
    """Select appropriate Claude model based on task requirements"""
    
    if speed_priority:
        return "claude-3-haiku-20240307"
    
    if task_complexity == "simple":
        return "claude-3-haiku-20240307"
    elif task_complexity == "moderate":
        return "claude-3-5-sonnet-20241022"
    elif task_complexity == "complex":
        return "claude-3-opus-20240229"
    else:
        return "claude-3-5-sonnet-20241022"  # Default

# Example usage
model = select_model("complex", speed_priority=False)
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
```

## Error Handling Compatibility

### Exception Types

```python
from openai import OpenAIError, APIError, RateLimitError, AuthenticationError

try:
    response = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded")
except APIError as e:
    print(f"API error: {e}")
except OpenAIError as e:
    print(f"OpenAI error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

```python
import time
from openai import RateLimitError, APIError

def robust_completion(client, **kwargs):
    """Completion with built-in retry logic"""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"Rate limited, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
        except APIError as e:
            if attempt < max_retries - 1 and e.status_code >= 500:
                delay = base_delay * (2 ** attempt)
                print(f"Server error, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise

# Usage
response = robust_completion(
    client,
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Parameter Translation

### Temperature and Sampling

```python
# OpenAI-style parameters work directly
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Be creative!"}],
    temperature=0.9,    # Higher = more creative
    top_p=0.95,        # Nucleus sampling
    max_tokens=500     # Response length limit
)
```

### Stop Sequences

```python
# Multiple stop sequences
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Count to 5"}],
    stop=["6", "seven", "\n\n"]  # Stop at any of these
)
```

### Advanced Parameters

```python
# All supported parameters
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages,
    
    # Sampling parameters
    temperature=0.7,
    top_p=0.95,
    max_tokens=1000,
    
    # Control parameters
    stop=["END", "STOP"],
    
    # Metadata
    user="user-123",  # For tracking
    
    # Streaming
    stream=False,
    
    # Function calling (if supported)
    tools=tools,
    tool_choice="auto"
)
```

## Migration Strategies

### Gradual Migration

```python
# Step 1: Add claif_cla alongside OpenAI
try:
    from openai import OpenAI as OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from claif_cla import ClaudeClient

class UniversalClient:
    def __init__(self, provider="auto"):
        if provider == "openai" and OPENAI_AVAILABLE:
            self.client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
            self.provider = "openai"
        else:
            self.client = ClaudeClient(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.provider = "claude"
    
    def chat_completion(self, **kwargs):
        # Adjust model names based on provider
        if self.provider == "claude" and "model" in kwargs:
            # Use Claude models
            kwargs["model"] = "claude-3-5-sonnet-20241022"
        
        return self.client.chat.completions.create(**kwargs)

# Usage
client = UniversalClient(provider="claude")
response = client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Feature Detection

```python
def get_client_capabilities(client):
    """Detect client capabilities"""
    capabilities = {
        "streaming": True,
        "function_calling": False,
        "vision": False,
        "json_mode": False
    }
    
    # Test for function calling
    try:
        # Try a simple function call
        response = client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "What time is it?"}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "Get current time"
                }
            }],
            max_tokens=10
        )
        capabilities["function_calling"] = True
    except:
        pass
    
    return capabilities

# Usage
caps = get_client_capabilities(client)
print(f"Client capabilities: {caps}")
```

## Best Practices

### 1. Model Selection

```python
# Choose models based on task requirements
def smart_model_selection(prompt: str, budget: str = "medium") -> str:
    """Select model based on prompt complexity and budget"""
    
    # Simple heuristics
    if len(prompt) < 100 and budget == "low":
        return "claude-3-haiku-20240307"
    elif "analyze" in prompt.lower() or "complex" in prompt.lower():
        return "claude-3-opus-20240229"
    else:
        return "claude-3-5-sonnet-20241022"

model = smart_model_selection("Analyze this complex data pattern")
```

### 2. Error Handling

```python
def safe_completion(client, **kwargs):
    """Safe completion with comprehensive error handling"""
    try:
        return client.chat.completions.create(**kwargs)
    except AuthenticationError:
        raise ValueError("Invalid API key - check ANTHROPIC_API_KEY")
    except RateLimitError:
        raise ValueError("Rate limit exceeded - try again later")
    except Exception as e:
        raise ValueError(f"API call failed: {e}")
```

### 3. Response Validation

```python
def validate_response(response):
    """Validate response completeness"""
    if not response.choices:
        raise ValueError("No response choices returned")
    
    if not response.choices[0].message.content:
        raise ValueError("Empty response content")
    
    if response.choices[0].finish_reason == "length":
        print("Warning: Response may be truncated")
    
    return response
```

## Limitations and Differences

### Current Limitations

1. **Function Calling**: Limited compared to OpenAI's implementation
2. **Logit Bias**: Not supported by Claude API
3. **JSON Mode**: Different implementation approach
4. **Batch API**: Not yet available for Claude

### Key Differences

| Feature | OpenAI | claif_cla/Claude |
|---------|---------|------------------|
| Model names | `gpt-4`, `gpt-3.5-turbo` | `claude-3-*` |
| Max tokens | Up to 128k | Up to 200k |
| Function calling | Native support | Mapped to tool use |
| Vision | GPT-4V models | Claude 3 models |
| Fine-tuning | Supported | Not available |

## Next Steps

- **[Client Methods](client-methods.md)** - Detailed method reference
- **[Response Types](response-types.md)** - Complete response object documentation
- **[Error Handling](error-handling.md)** - Comprehensive error management
- **[Session Management](../sessions/overview.md)** - Stateful conversations

The OpenAI compatibility layer makes migrating to Claude seamless while preserving all your existing code patterns! 🚀