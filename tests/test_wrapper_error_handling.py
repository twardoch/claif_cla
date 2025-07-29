"""Additional tests for wrapper error handling and edge cases."""

from unittest.mock import Mock, patch

import pytest
from claif.common.errors import ClaifTimeoutError, ProviderError
from claif.common.types import ClaifOptions
from claude_code_sdk import Message as ClaudeMessage

from claif_cla.wrapper import ClaudeWrapper


@pytest.mark.unit
class TestClaudeWrapperErrorHandling:
    """Test error handling in ClaudeWrapper."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        from claif.common import Provider
        from claif.common.config import ProviderConfig

        config = Mock()
        config.cache_ttl = 3600
        config.retry_config = {"count": 3, "delay": 1.0, "backoff": 2.0}
        config.providers = {
            Provider.CLAUDE: ProviderConfig(
                enabled=True,
                model="claude-3-sonnet",
                api_key_env="ANTHROPIC_API_KEY",
                timeout=120,
                extra={"api_key": "test-key"},
            )
        }
        return config

    @pytest.fixture
    def wrapper(self, mock_config, temp_dir):
        """Create wrapper instance."""
        with (
            patch("claif_cla.wrapper.ClaudeCodeClient"),
            patch("claif_cla.wrapper.CodeToolFactory"),
            patch("pathlib.Path.home", return_value=temp_dir),
        ):
            return ClaudeWrapper(mock_config)

    @pytest.mark.asyncio
    async def test_message_to_dict_with_tool_use_block(self, wrapper):
        """Test message serialization with ToolUseBlock."""
        from claif_cla.wrapper import ClaudeMessage, ClaudeToolUseBlock

        # Create a message with ToolUseBlock
        tool_block = ClaudeToolUseBlock(type="tool_use", id="test-id", name="test_tool", input={"param": "value"})
        message = ClaudeMessage(role="user", content=[tool_block])

        result = wrapper._message_to_dict(message)

        assert result["role"] == "user"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "tool_use"
        assert result["content"][0]["id"] == "test-id"
        assert result["content"][0]["name"] == "test_tool"
        assert result["content"][0]["input"] == {"param": "value"}

    @pytest.mark.asyncio
    async def test_message_to_dict_with_tool_result_block(self, wrapper):
        """Test message serialization with ToolResultBlock."""
        from claif_cla.wrapper import ClaudeMessage, ClaudeTextBlock, ClaudeToolResultBlock

        # Create a message with ToolResultBlock
        text_block = ClaudeTextBlock(type="text", text="Tool output")
        tool_result_block = ClaudeToolResultBlock(type="tool_result", content=[text_block])
        message = ClaudeMessage(role="assistant", content=[tool_result_block])

        result = wrapper._message_to_dict(message)

        assert result["role"] == "assistant"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "tool_result"
        assert len(result["content"][0]["content"]) == 1
        assert result["content"][0]["content"][0]["type"] == "text"
        assert result["content"][0]["content"][0]["text"] == "Tool output"

    @pytest.mark.asyncio
    async def test_message_to_dict_with_unknown_block_type(self, wrapper):
        """Test message serialization with unknown block type."""
        from claif_cla.wrapper import ClaudeMessage

        # Create a message with unknown block type
        unknown_block = Mock()
        unknown_block.type = "unknown"
        message = ClaudeMessage(role="user", content=[unknown_block])

        result = wrapper._message_to_dict(message)

        assert result["role"] == "user"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "unknown"
        assert result["content"][0]["data"] == str(unknown_block)

    @pytest.mark.asyncio
    async def test_dict_to_message_with_tool_use_block(self, wrapper):
        """Test message deserialization with ToolUseBlock."""
        from claif.common.types import MessageRole

        # Create dict with ToolUseBlock
        message_dict = {
            "role": MessageRole.USER,
            "content": [{"type": "tool_use", "id": "test-id", "name": "test_tool", "input": {"param": "value"}}],
        }

        result = wrapper._dict_to_message(message_dict)

        assert result.role == MessageRole.USER
        assert len(result.content) == 1
        block = result.content[0]
        assert block.type == "tool_use"
        assert block.id == "test-id"
        assert block.name == "test_tool"
        assert block.input == {"param": "value"}

    @pytest.mark.asyncio
    async def test_dict_to_message_with_tool_result_block(self, wrapper):
        """Test message deserialization with ToolResultBlock."""
        from claif.common.types import MessageRole

        # Create dict with ToolResultBlock
        message_dict = {
            "role": MessageRole.ASSISTANT,
            "content": [{"type": "tool_result", "content": [{"type": "text", "text": "Tool output"}]}],
        }

        result = wrapper._dict_to_message(message_dict)

        assert result.role == MessageRole.ASSISTANT
        assert len(result.content) == 1
        block = result.content[0]
        assert block.type == "tool_result"
        assert len(block.content) == 1
        assert block.content[0].type == "text"
        assert block.content[0].text == "Tool output"

    @pytest.mark.asyncio
    async def test_dict_to_message_with_unknown_block_type(self, wrapper):
        """Test message deserialization with unknown block type."""
        from claif.common.types import MessageRole

        # Create dict with unknown block type
        message_dict = {"role": MessageRole.USER, "content": [{"type": "unknown", "data": "unknown data"}]}

        result = wrapper._dict_to_message(message_dict)

        assert result.role == MessageRole.USER
        assert len(result.content) == 1
        # Unknown blocks should be converted to TextBlocks
        assert hasattr(result.content[0], "text")
        assert "unknown data" in result.content[0].text

    @pytest.mark.asyncio
    async def test_base_query_with_mock_response(self, wrapper):
        """Test the base query method with mock response."""
        options = ClaifOptions(model="claude-3-sonnet")

        messages = []
        async for message in wrapper._base_query("Test prompt", options):
            messages.append(message)

        assert len(messages) == 1
        assert "Mock response to: Test prompt" in messages[0].content

    @pytest.mark.asyncio
    async def test_query_with_connection_error_retry(self, wrapper):
        """Test query with connection error and retry."""
        options = ClaifOptions(model="claude-3-sonnet")

        # Mock _base_query to fail twice then succeed
        call_count = 0

        async def mock_base_query(prompt, opts):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                msg = "Network error"
                raise ConnectionError(msg)
            yield Mock(role="assistant", content="Success after retry")

        with patch.object(wrapper, "_base_query", side_effect=mock_base_query):
            messages = []
            async for msg in wrapper.query("Test prompt", options):
                messages.append(msg)

        assert len(messages) == 1
        assert call_count == 3  # Should have retried twice

    @pytest.mark.asyncio
    async def test_query_with_timeout_error(self, wrapper):
        """Test query with timeout error."""
        options = ClaifOptions(model="claude-3-sonnet")

        # Mock _base_query to always timeout
        async def mock_base_query(prompt, opts):
            msg = "Request timeout"
            raise TimeoutError(msg)
            yield  # Never reached

        with patch.object(wrapper, "_base_query", side_effect=mock_base_query):
            with pytest.raises(ClaifTimeoutError):
                messages = []
                async for msg in wrapper.query("Test prompt", options):
                    messages.append(msg)

    @pytest.mark.asyncio
    async def test_query_with_quota_error(self, wrapper):
        """Test query with quota error."""
        options = ClaifOptions(model="claude-3-sonnet")

        # Mock _base_query to always fail with quota error
        async def mock_base_query(prompt, opts):
            msg = "API quota exceeded"
            raise Exception(msg)
            yield  # Never reached

        with patch.object(wrapper, "_base_query", side_effect=mock_base_query):
            with pytest.raises(ProviderError) as exc_info:
                messages = []
                async for msg in wrapper.query("Test prompt", options):
                    messages.append(msg)

            assert "quota" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_query_with_no_retry_option(self, wrapper):
        """Test query with no_retry option."""
        options = ClaifOptions(model="claude-3-sonnet", no_retry=True)

        # Mock _base_query to fail once
        async def mock_base_query(prompt, opts):
            msg = "Single failure"
            raise Exception(msg)
            yield  # Never reached

        with patch.object(wrapper, "_base_query", side_effect=mock_base_query), pytest.raises(ProviderError):
            messages = []
            async for msg in wrapper.query("Test prompt", options):
                messages.append(msg)

    @pytest.mark.asyncio
    async def test_query_with_zero_retry_count(self, wrapper):
        """Test query with zero retry count."""
        options = ClaifOptions(model="claude-3-sonnet", retry_count=0)

        # Mock _base_query to fail once
        async def mock_base_query(prompt, opts):
            msg = "Single failure"
            raise Exception(msg)
            yield  # Never reached

        with patch.object(wrapper, "_base_query", side_effect=mock_base_query), pytest.raises(ProviderError):
            messages = []
            async for msg in wrapper.query("Test prompt", options):
                messages.append(msg)

    @pytest.mark.asyncio
    async def test_cache_configuration(self, wrapper):
        """Test cache configuration."""
        assert wrapper.cache is not None
        assert wrapper.cache.ttl == 3600
        assert wrapper.cache.cache_dir.name == "claude"

    @pytest.mark.asyncio
    async def test_retry_configuration(self, wrapper):
        """Test retry configuration."""
        assert wrapper.retry_count == 3
        assert wrapper.retry_delay == 1.0
        assert wrapper.retry_backoff == 2.0
