"""Pytest configuration and fixtures for claif_cla tests."""

import sys
from unittest.mock import AsyncMock, MagicMock, Mock

# Mock external dependencies BEFORE any imports that might use them
# This needs to happen at module level, not in fixtures

# Create mock message classes with proper inheritance structure
class MockMessage:
    """Base mock message class."""
    pass

class MockUserMessage(MockMessage):
    """Mock UserMessage class."""
    def __init__(self, content=""):
        self.content = content

class MockAssistantMessage(MockMessage):
    """Mock AssistantMessage class."""
    def __init__(self, content=None):
        self.content = content or []

class MockSystemMessage(MockMessage):
    """Mock SystemMessage class."""
    def __init__(self, content=""):
        self.content = content

class MockResultMessage(MockMessage):
    """Mock ResultMessage class."""
    def __init__(self, content=""):
        self.content = content

class MockClaudeCodeOptions:
    """Mock ClaudeCodeOptions class."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# Create mock query function that returns an async iterator
class MockAsyncIterator:
    """Mock async iterator for claude_query."""
    
    def __init__(self, prompt: str, options=None):
        self.prompt = prompt
        self.options = options
        self.items = [
            MockUserMessage(content=prompt),
            MockAssistantMessage(content=[Mock(text="Mock response from Claude")])
        ]
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

def mock_query(prompt: str, options=None):
    """Mock query function that returns an async iterator."""
    return MockAsyncIterator(prompt, options)

# Create mock claude_code_sdk module
mock_sdk = MagicMock()
mock_sdk.query = mock_query
mock_sdk.ClaudeCodeOptions = MockClaudeCodeOptions
mock_sdk.Message = MockMessage
mock_sdk.UserMessage = MockUserMessage
mock_sdk.AssistantMessage = MockAssistantMessage
mock_sdk.SystemMessage = MockSystemMessage
mock_sdk.ResultMessage = MockResultMessage

# Install the mocks - mock both claude_code and claude_code_sdk
sys.modules["claude_code_sdk"] = mock_sdk

# Create mock claude_code module (used by wrapper.py)
mock_claude_code = MagicMock()
mock_claude_client = MagicMock()
mock_claude_client.query = AsyncMock()
mock_claude_client.close = AsyncMock()
mock_claude_code.ClaudeCodeClient = Mock(return_value=mock_claude_client)

# Create mock code_tools
mock_code_tools = MagicMock()
mock_code_tools.CodeToolFactory = MagicMock()
mock_claude_code.code_tools = mock_code_tools

sys.modules["claude_code"] = mock_claude_code
sys.modules["claude_code.code_tools"] = mock_code_tools

# Now we can import other modules
import asyncio
import json
import tempfile
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from claif.common import ClaifOptions, Message, MessageRole, TextBlock


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_claude_response() -> list[Any]:
    """Mock Claude response messages."""
    return [
        MockUserMessage(content="Test prompt"),
        MockAssistantMessage(
            content=[
                Mock(text="This is a test response"),
                Mock(text="With multiple parts"),
            ]
        ),
    ]


@pytest.fixture
def mock_claif_options() -> ClaifOptions:
    """Create mock Claif options."""
    return ClaifOptions(
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="You are a helpful assistant",
        timeout=30,
    )


@pytest.fixture
def mock_claude_query():
    """Mock the claude_query function."""

    async def _mock_query(prompt: str, options: Any) -> AsyncIterator[Any]:
        # Yield mock messages
        yield MockUserMessage(content=prompt)
        yield MockAssistantMessage(
            content=[
                Mock(text="Mock response"),
            ]
        )

    return _mock_query


@pytest.fixture
def mock_install_claude() -> Mock:
    """Mock the install_claude function."""
    return Mock(return_value={"installed": True, "failed": []})


@pytest.fixture
def mock_session_dir(temp_dir: Path) -> Path:
    """Create a mock session directory."""
    session_dir = temp_dir / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


@pytest.fixture
def mock_session_file(mock_session_dir: Path) -> tuple[Path, str]:
    """Create a mock session file."""
    session_id = "test-session-123"
    session_data = {
        "id": session_id,
        "created_at": "2024-01-01T00:00:00Z",
        "messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}],
        "metadata": {},
        "checkpoints": [],
    }

    session_file = mock_session_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session_data, f)

    return session_file, session_id


@pytest.fixture
def mock_approval_strategy() -> Mock:
    """Mock approval strategy."""
    strategy = Mock()
    strategy.should_approve.return_value = True
    strategy.get_description.return_value = "Mock Strategy"
    return strategy


@pytest.fixture
def mock_install_result() -> dict[str, Any]:
    """Mock installation result."""
    return {"installed": ["claude"], "failed": [], "message": "Success"}


@pytest.fixture
def mock_subprocess_run() -> Mock:
    """Mock subprocess.run for install tests."""
    mock = Mock()
    mock.return_value.returncode = 0
    mock.return_value.stdout = "Installation successful"
    mock.return_value.stderr = ""
    return mock


@pytest.fixture(autouse=True)
def mock_logger():
    """Mock logger to prevent log output during tests."""
    with patch("claif_cla.logger"):
        yield


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Create a mock configuration for tests."""
    from claif.common import Config, Provider
    
    return Config(
        default_provider=Provider.CLAUDE,
        verbose=False,
        providers={
            "claude": {
                "enabled": True,
                "model": "claude-3-sonnet",
                "extra": {"api_key": "test-key"}
            }
        }
    )

# Removed mock_claif_common fixture - using real claif.common module