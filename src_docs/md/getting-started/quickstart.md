---
# this_file: src_docs/md/getting-started/quickstart.md
title: Quick Start Guide
description: Get up and running with claif_cla in minutes
---

# Quick Start Guide

Get up and running with claif_cla in under 5 minutes! This guide covers the essential usage patterns you need to start using Claude through the OpenAI-compatible API.

## Prerequisites

- Python 3.10+
- claif_cla installed (`pip install claif_cla`)
- ANTHROPIC_API_KEY environment variable set

## Basic Python Usage

### 1. Your First Query

```python
from claif_cla import ClaudeClient

# Initialize the client
client = ClaudeClient()

# Send a message - just like OpenAI!
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Hello Claude! What can you help me with?"}
    ]
)

# Get the response
print(response.choices[0].message.content)
```

### 2. Streaming Responses

```python
from claif_cla import ClaudeClient

client = ClaudeClient()

# Stream responses in real-time
stream = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Write a haiku about programming"}
    ],
    stream=True
)

# Print chunks as they arrive
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 3. System Messages and Parameters

```python
from claif_cla import ClaudeClient

client = ClaudeClient()

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "system", "content": "You are a helpful Python coding assistant."},
        {"role": "user", "content": "Write a function to reverse a string"}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

## Basic CLI Usage

### 1. Quick Queries

```bash
# Simple question
claif-cla query "What is the capital of France?"

# With specific model
claif-cla query "Explain quantum computing" --model claude-3-opus-20240229

# With parameters
claif-cla query "Write a poem" --temperature 0.9 --max-tokens 200
```

### 2. Interactive Chat

```bash
# Start interactive mode
claif-cla chat

# With specific model
claif-cla chat --model claude-3-5-sonnet-20241022
```

### 3. Session Management

```bash
# Create a new session
claif-cla session create --metadata '{"project": "my-app"}'

# List all sessions
claif-cla session list

# Continue a session
claif-cla ask "Continue our discussion" --session SESSION_ID
```

## Common Patterns

### Working with Conversations

```python
from claif_cla import ClaudeClient

client = ClaudeClient()

# Build a conversation
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"},
]

# Get first response
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages
)

# Add response to conversation
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

print(response.choices[0].message.content)
```

### Error Handling

```python
from claif_cla import ClaudeClient
from openai import OpenAIError

client = ClaudeClient()

try:
    response = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)
    
except OpenAIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Using Different Models

```python
from claif_cla import ClaudeClient

client = ClaudeClient()

# Available models
models = [
    "claude-3-5-sonnet-20241022",  # Latest, most capable
    "claude-3-opus-20240229",     # Most intelligent
    "claude-3-sonnet-20240229",   # Balanced
    "claude-3-haiku-20240307"     # Fastest, cheapest
]

# Example with different models
for model in models:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=50
    )
    print(f"{model}: {response.choices[0].message.content}")
```

## Advanced Quick Examples

### 1. Custom Configuration

```python
from claif_cla import ClaudeClient

# Custom timeout and API key
client = ClaudeClient(
    api_key="your-custom-key",
    timeout=300  # 5 minutes
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Complex analysis task..."}]
)
```

### 2. Batch Processing

```python
from claif_cla import ClaudeClient

client = ClaudeClient()
questions = [
    "What is Python?",
    "What is JavaScript?", 
    "What is Rust?"
]

for question in questions:
    response = client.chat.completions.create(
        model="claude-3-haiku-20240307",  # Fast model for batch
        messages=[{"role": "user", "content": question}],
        max_tokens=100
    )
    print(f"Q: {question}")
    print(f"A: {response.choices[0].message.content}\n")
```

### 3. Response Metadata

```python
from claif_cla import ClaudeClient

client = ClaudeClient()

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Explain AI"}]
)

# Access response metadata
print(f"Model: {response.model}")
print(f"Usage: {response.usage}")
print(f"Finish reason: {response.choices[0].finish_reason}")
print(f"Content: {response.choices[0].message.content}")
```

## CLI Advanced Examples

### 1. Output Formats

```bash
# JSON output
claif-cla query "What is AI?" --json-output

# Markdown export
claif-cla session export SESSION_ID --format markdown --output chat.md

# Verbose debugging
claif-cla query "Debug this" --verbose
```

### 2. Session Templates

```bash
# Create coding session
claif-cla session create --template coding --metadata '{"language": "python"}'

# Create analysis session
claif-cla session create --template analysis --metadata '{"topic": "data"}'
```

### 3. Benchmarking

```bash
# Test response time
claif-cla benchmark "Simple math question" --iterations 5

# Compare models
claif-cla benchmark "Code review task" --models claude-3-haiku-20240307,claude-3-5-sonnet-20241022
```

## Integration Patterns

### Drop-in OpenAI Replacement

```python
# Replace this:
# from openai import OpenAI
# client = OpenAI()

# With this:
from claif_cla import ClaudeClient as OpenAI
client = OpenAI()

# Rest of your code stays the same!
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",  # Just change the model
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Async Usage (Future)

```python
# Note: Currently synchronous, async support planned
from claif_cla import ClaudeClient

client = ClaudeClient()

# Current synchronous usage
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Troubleshooting Quick Fixes

### Common Issues

```python
# Issue: API key not found
import os
print(os.getenv('ANTHROPIC_API_KEY'))  # Should not be None

# Issue: Import error
try:
    from claif_cla import ClaudeClient
    print("✅ Package imported successfully")
except ImportError:
    print("❌ Run: pip install claif_cla")

# Issue: Model not found
# Use exact model names from Anthropic's documentation
```

### CLI Issues

```bash
# Issue: Command not found
which claif-cla  # Should show path to executable

# Issue: No sessions found
claif-cla session list --verbose  # Check session directory

# Issue: Permission denied
ls -la ~/.claif/  # Check permissions
```

## Next Steps

Now that you're up and running:

1. **[Basic Examples](examples.md)** - Explore more practical examples
2. **[API Reference](../api/openai-compatibility.md)** - Understand all available methods
3. **[Session Management](../sessions/overview.md)** - Learn advanced conversation handling
4. **[CLI Usage](../cli/overview.md)** - Master the command-line interface
5. **[Tool Approval](../tools/strategies.md)** - Control tool usage securely

## Quick Reference Card

```python
# Essential imports
from claif_cla import ClaudeClient

# Basic query
client = ClaudeClient()
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Your question"}]
)
print(response.choices[0].message.content)

# Streaming
for chunk in client.chat.completions.create(..., stream=True):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# CLI basics
claif-cla query "Your question"
claif-cla chat  # Interactive mode
claif-cla session list  # Manage sessions
```

You're ready to build amazing things with Claude! 🚀