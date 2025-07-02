"""Pytest configuration and fixtures for claif_cla tests."""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Iterator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from claif.common import ClaifOptions, Message, MessageRole, TextBlock
from claude_code_sdk import AssistantMessage, ClaudeCodeOptions, UserMessage


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_claude_response() -> list[Any]:
    """Mock Claude response messages."""
    return [
        UserMessage(content="Test prompt"),
        AssistantMessage(
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
def mock_claude_query() -> AsyncMock:
    """Mock the claude_query function."""
    async def _mock_query(prompt: str, options: ClaudeCodeOptions) -> AsyncIterator[Any]:
        # Yield mock messages
        yield UserMessage(content=prompt)
        yield AssistantMessage(
            content=[
                Mock(text="Mock response"),
            ]
        )
    
    mock = AsyncMock(side_effect=_mock_query)
    return mock


@pytest.fixture
def mock_install_claude() -> Mock:
    """Mock the install_claude function."""
    mock = Mock(return_value={"installed": True, "failed": []})
    return mock


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
        "messages": [
            {
                "role": "user",
                "content": "Hello"
            },
            {
                "role": "assistant",
                "content": "Hi there!"
            }
        ],
        "metadata": {},
        "checkpoints": []
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
    return {
        "installed": ["claude"],
        "failed": [],
        "message": "Success"
    }


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


# Mock external dependencies that might not be installed
@pytest.fixture(autouse=True)
def mock_claude_code_sdk():
    """Mock claude-code-sdk if not installed."""
    import sys
    
    # Create mock modules
    mock_sdk = MagicMock()
    mock_sdk.query = AsyncMock()
    mock_sdk.ClaudeCodeOptions = Mock
    mock_sdk.Message = Mock
    mock_sdk.UserMessage = Mock
    mock_sdk.AssistantMessage = Mock
    mock_sdk.SystemMessage = Mock
    mock_sdk.ResultMessage = Mock
    
    # Only mock if not already imported
    if "claude_code_sdk" not in sys.modules:
        sys.modules["claude_code_sdk"] = mock_sdk
    
    yield
    
    # Clean up
    if "claude_code_sdk" in sys.modules and sys.modules["claude_code_sdk"] is mock_sdk:
        del sys.modules["claude_code_sdk"]


@pytest.fixture
def mock_claif_common():
    """Mock claif.common if not installed."""
    import sys
    
    # Create mock module structure
    mock_common = MagicMock()
    mock_common.ClaifOptions = Mock
    mock_common.Message = Mock
    mock_common.MessageRole = Mock
    mock_common.TextBlock = Mock
    mock_common.ResponseMetrics = Mock
    mock_common.format_response = Mock(return_value="Formatted response")
    mock_common.format_metrics = Mock(return_value="Formatted metrics")
    mock_common.config = MagicMock()
    mock_common.config.load_config = Mock(return_value=Mock(verbose=False, session_dir="/tmp/sessions"))
    mock_common.utils = MagicMock()
    mock_common.utils.prompt_tool_configuration = Mock()
    mock_common.install = MagicMock()
    
    # Only mock if not already imported
    if "claif.common" not in sys.modules:
        sys.modules["claif"] = MagicMock()
        sys.modules["claif.common"] = mock_common
        sys.modules["claif.common.config"] = mock_common.config
        sys.modules["claif.common.utils"] = mock_common.utils
        sys.modules["claif.install"] = mock_common.install
    
    yield
    
    # Clean up is handled by the test framework