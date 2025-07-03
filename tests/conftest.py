"""Pytest configuration and fixtures for claif_cla tests."""

import asyncio
import json
import tempfile
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from claif.common import ClaifOptions, Message, MessageRole, TextBlock
from loguru import logger


@pytest.fixture(autouse=True)
def mock_loguru_logger():
    """Mock loguru.logger to prevent log output during tests."""
    with (
        patch.object(logger, "debug") as mock_debug,
        patch.object(logger, "info") as mock_info,
        patch.object(logger, "warning") as mock_warning,
        patch.object(logger, "error") as mock_error,
        patch.object(logger, "exception") as mock_exception,
    ):
        yield {
            "debug": mock_debug,
            "info": mock_info,
            "warning": mock_warning,
            "error": mock_error,
            "exception": mock_exception,
        }


# Mock message classes for backward compatibility
class MockUserMessage:
    def __init__(self, content):
        self.role = "user"
        self.content = content


class MockAssistantMessage:
    def __init__(self, content):
        self.role = "assistant"
        self.content = content


@pytest.fixture
def mock_claude_response() -> list[Message]:
    """Mock Claude response messages using claif.common.Message."""
    return [
        Message(role=MessageRole.USER, content="Test prompt"),
        Message(role=MessageRole.ASSISTANT, content=[TextBlock(text="This is a test response")]),
        Message(role=MessageRole.ASSISTANT, content=[TextBlock(text="With multiple parts")]),
    ]


@pytest.fixture
def mock_claude_query():
    """Mock the claif_cla.query function to yield claif.common.Message objects."""

    async def _mock_query(prompt: str, options: ClaifOptions) -> AsyncIterator[Message]:
        yield Message(role=MessageRole.USER, content=prompt)
        yield Message(role=MessageRole.ASSISTANT, content=[TextBlock(text="Mock response from Claude")])

    return _mock_query


# Mock claude_code_sdk and claude_code modules
# These mocks are placed here to ensure they are set up before any module
# that might import them is loaded during test collection.

# Mock claude_code_sdk
mock_claude_code_sdk = MagicMock()
mock_claude_code_sdk.Message = Message
mock_claude_code_sdk.TextBlock = TextBlock

# Mock claude_code
mock_claude_code = MagicMock()
mock_claude_code.ClaudeCodeClient = MagicMock()
mock_claude_code.code_tools = MagicMock()

# Patch sys.modules to inject our mocks
import sys

sys.modules["claude_code_sdk"] = mock_claude_code_sdk
sys.modules["claude_code"] = mock_claude_code
sys.modules["claude_code.code_tools"] = mock_claude_code.code_tools


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


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
def mock_install_claude() -> Mock:
    """Mock the install_claude function."""
    return Mock(return_value={"installed": True, "failed": []})


@pytest.fixture
def mock_session_dir(temp_dir: Path) -> Path:
    """
    Create a mock session directory.

    Args:
        temp_dir: A pytest fixture providing a temporary directory.

    Returns:
        A Path object representing the created session directory.
    """
    session_dir = temp_dir / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


@pytest.fixture
def mock_session_file(mock_session_dir: Path) -> tuple[Path, str]:
    """
    Create a mock session file within the mock session directory.

    Args:
        mock_session_dir: A pytest fixture providing a mock session directory.

    Returns:
        A tuple containing the Path to the created session file and its session ID.
    """
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
    """
    Mock approval strategy.

    Returns:
        A MagicMock object configured to behave as an ApprovalStrategy.
    """
    strategy = MagicMock()
    strategy.should_approve.return_value = True
    strategy.get_description.return_value = "Mock Strategy"
    return strategy


@pytest.fixture
def mock_install_result() -> dict[str, Any]:
    """
    Mock installation result dictionary.

    Returns:
        A dictionary simulating the output of an installation function.
    """
    return {"installed": ["claude"], "failed": [], "message": "Success"}


@pytest.fixture
def mock_subprocess_run() -> Mock:
    """
    Mock subprocess.run for install tests.

    Returns:
        A Mock object configured to simulate a successful subprocess execution.
    """
    mock = Mock()
    mock.return_value.returncode = 0
    mock.return_value.stdout = "Installation successful"
    mock.return_value.stderr = ""
    return mock


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
        providers={"claude": {"enabled": True, "model": "claude-3-sonnet", "extra": {"api_key": "test-key"}}},
    )
