---
# this_file: src_docs/md/testing/running.md
title: Chapter 7 - Testing & Development
description: Comprehensive testing framework, development setup, and contribution guidelines
---

# Chapter 7: Testing & Development

claif_cla includes a comprehensive testing framework to ensure robust functionality across all components.

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uvx hatch test

# Run specific test file
uvx hatch test -- tests/test_client.py

# Run with verbose output
uvx hatch test -- -v

# Run with coverage
uvx hatch test -- --cov=src/claif_cla --cov-report=html
```

### Test Categories

```bash
# Unit tests only
uvx hatch test -- -m unit

# Integration tests only
uvx hatch test -- -m integration

# Performance benchmarks
uvx hatch test -- -m benchmark
```

## Test Structure

The test suite is organized into:

- `test_client.py` - Client API tests
- `test_session.py` - Session management tests  
- `test_approval.py` - Tool approval tests
- `test_wrapper.py` - Caching and wrapper tests
- `test_cli.py` - CLI interface tests
- `test_integration.py` - End-to-end tests

## Writing Tests

### Basic Test Pattern

```python
import pytest
from unittest.mock import Mock, patch
from claif_cla import ClaudeClient

@patch('claif_cla.client.ClaudeCodeClient')
def test_client_creation(mock_client):
    """Test client initialization"""
    client = ClaudeClient(api_key="test-key")
    
    assert client.api_key == "test-key"
    mock_client.assert_called_once()
```

### Mock Responses

```python
from claif_cla.testing import MockResponse

def test_completion_response():
    """Test completion response handling"""
    mock_response = MockResponse(
        content="Hello, world!",
        model="claude-3-5-sonnet-20241022",
        usage={"total_tokens": 10}
    )
    
    # Test response processing
    assert mock_response.choices[0].message.content == "Hello, world!"
```

For detailed testing patterns, see [Test Structure](structure.md) and [Development Setup](development.md).