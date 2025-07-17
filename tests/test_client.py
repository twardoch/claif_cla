"""Tests for the ClaudeClient."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from claif.common import ClaifOptions, Message, MessageRole, TextBlock
from claif.common.errors import ProviderError

from claif_cla.client import ClaudeClient, get_client, query


@pytest.mark.unit
class TestClaudeClient:
    """Test ClaudeClient functionality."""

    def test_singleton_pattern(self):
        """Test that ClaudeClient follows singleton pattern."""
        # Reset class instance for testing
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client1 = ClaudeClient(mock_config)
            client2 = ClaudeClient(mock_config)

            assert client1 is client2
            assert ClaudeClient._instance is client1

    def test_init_sets_initialized_flag(self):
        """Test that initialization sets the _initialized flag."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper") as mock_wrapper:
            client = ClaudeClient(mock_config)

            assert client._initialized is True
            assert client.config is mock_config
            mock_wrapper.assert_called_once_with(mock_config)

    def test_init_skips_if_already_initialized(self):
        """Test that subsequent initializations are skipped."""
        ClaudeClient._instance = None

        mock_config1 = Mock()
        mock_config2 = Mock()

        with patch("claif_cla.client.ClaudeWrapper") as mock_wrapper:
            client1 = ClaudeClient(mock_config1)
            client2 = ClaudeClient(mock_config2)

            assert client1 is client2
            assert client1.config is mock_config1  # Should keep original config
            mock_wrapper.assert_called_once_with(mock_config1)

    def test_claude_to_claif_message_with_string_content(self):
        """Test message conversion with string content."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = ClaudeClient(mock_config)

            # Mock ClaudeMessage with string content
            claude_msg = Mock()
            claude_msg.role = MessageRole.ASSISTANT
            claude_msg.content = "Hello world"

            result = client._claude_to_claif_message(claude_msg)

            assert isinstance(result, Message)
            assert result.role == MessageRole.ASSISTANT
            assert len(result.content) == 1
            assert isinstance(result.content[0], TextBlock)
            assert result.content[0].text == "Hello world"

    def test_claude_to_claif_message_with_list_content(self):
        """Test message conversion with list content."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = ClaudeClient(mock_config)

            # Mock ClaudeMessage with list content
            claude_msg = Mock()
            claude_msg.role = MessageRole.USER

            # Mock content blocks
            block1 = Mock()
            block1.text = "Part 1"
            block2 = Mock()
            block2.text = "Part 2"
            claude_msg.content = [block1, block2]

            result = client._claude_to_claif_message(claude_msg)

            assert isinstance(result, Message)
            assert result.role == MessageRole.USER
            assert len(result.content) == 2
            assert result.content[0].text == "Part 1"
            assert result.content[1].text == "Part 2"

    def test_claude_to_claif_message_with_mixed_content(self):
        """Test message conversion with mixed content types."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = ClaudeClient(mock_config)

            # Mock ClaudeMessage with mixed content
            claude_msg = Mock()
            claude_msg.role = MessageRole.USER

            # Mix of text block and string
            block = Mock()
            block.text = "Text block"
            claude_msg.content = [block, "String content"]

            result = client._claude_to_claif_message(claude_msg)

            assert len(result.content) == 2
            assert result.content[0].text == "Text block"
            assert result.content[1].text == "String content"

    def test_claude_to_claif_message_with_unknown_block_type(self):
        """Test message conversion with unknown content block type."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = ClaudeClient(mock_config)

            # Mock ClaudeMessage with unknown content type
            claude_msg = Mock()
            claude_msg.role = MessageRole.USER

            # Unknown content type - mock object without text attribute
            unknown_block = Mock()
            # Remove text attribute to simulate unknown type
            del unknown_block.text
            claude_msg.content = [unknown_block]

            result = client._claude_to_claif_message(claude_msg)

            assert len(result.content) == 1
            assert isinstance(result.content[0], TextBlock)
            # The unknown block should be converted to string
            assert result.content[0].text == str(unknown_block)

    def test_claude_to_claif_message_with_malformed_message(self):
        """Test message conversion with malformed message."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = ClaudeClient(mock_config)

            # Mock malformed message (no role or content)
            claude_msg = Mock()
            # Remove role and content attributes to simulate malformed message
            del claude_msg.role
            del claude_msg.content

            result = client._claude_to_claif_message(claude_msg)

            assert isinstance(result, Message)
            assert result.role == MessageRole.ASSISTANT
            assert len(result.content) == 1
            assert isinstance(result.content[0], TextBlock)
            assert result.content[0].text == str(claude_msg)

    def test_claude_to_claif_message_with_none_values(self):
        """Test message conversion with None values."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = ClaudeClient(mock_config)

            # Mock message with None values
            claude_msg = Mock()
            claude_msg.role = None
            claude_msg.content = None

            result = client._claude_to_claif_message(claude_msg)

            assert result.role == MessageRole.ASSISTANT
            assert len(result.content) == 1
            assert isinstance(result.content[0], TextBlock)
            assert result.content[0].text == "None"

    @pytest.mark.asyncio
    async def test_query_success(self):
        """Test successful query execution."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper") as mock_wrapper_class:
            mock_wrapper = Mock()
            mock_wrapper_class.return_value = mock_wrapper

            # Mock Claude messages
            claude_msg1 = Mock()
            claude_msg1.role = MessageRole.ASSISTANT
            claude_msg1.content = "Response 1"

            claude_msg2 = Mock()
            claude_msg2.role = MessageRole.ASSISTANT
            claude_msg2.content = "Response 2"

            # Mock async generator
            async def mock_query_generator(*args, **kwargs):
                yield claude_msg1
                yield claude_msg2

            mock_wrapper.query = mock_query_generator

            client = ClaudeClient(mock_config)
            options = ClaifOptions(model="claude-3-opus")

            messages = []
            async for msg in client.query("Test prompt", options):
                messages.append(msg)

            assert len(messages) == 2
            assert messages[0].content[0].text == "Response 1"
            assert messages[1].content[0].text == "Response 2"
            # Note: We can't easily assert on the mock function call since it's replaced directly

    @pytest.mark.asyncio
    async def test_query_with_default_options(self):
        """Test query with default options."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper") as mock_wrapper_class:
            mock_wrapper = Mock()
            mock_wrapper_class.return_value = mock_wrapper

            # Mock async generator
            async def mock_query_generator(*args, **kwargs):
                yield Mock(role=MessageRole.ASSISTANT, content="Response")

            mock_wrapper.query = mock_query_generator

            client = ClaudeClient(mock_config)

            messages = []
            async for msg in client.query("Test prompt"):
                messages.append(msg)

            assert len(messages) == 1
            # Should work with default ClaifOptions - we can verify the message was processed correctly
            assert messages[0].content[0].text == "Response"

    @pytest.mark.asyncio
    async def test_query_exception_handling(self):
        """Test query exception handling."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper") as mock_wrapper_class:
            mock_wrapper = Mock()
            mock_wrapper_class.return_value = mock_wrapper

            # Mock exception in async generator
            async def mock_error_generator(*args, **kwargs):
                msg = "Test error"
                raise Exception(msg)
                yield  # This won't be reached

            mock_wrapper.query = mock_error_generator

            client = ClaudeClient(mock_config)

            with pytest.raises(ProviderError) as exc_info:
                messages = []
                async for msg in client.query("Test prompt"):
                    messages.append(msg)

            assert "Test error" in str(exc_info.value)
            assert exc_info.value.provider == "claude"

    @pytest.mark.asyncio
    async def test_is_available(self):
        """Test is_available method."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with (
            patch("claif_cla.client.ClaudeWrapper"),
            patch("claif_cla.client.is_claude_installed") as mock_is_installed,
        ):
            mock_is_installed.return_value = True
            client = ClaudeClient(mock_config)

            result = await client.is_available()

            assert result is True
            mock_is_installed.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_models(self):
        """Test get_models method."""
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = ClaudeClient(mock_config)

            models = await client.get_models()

            assert isinstance(models, dict)
            assert "claude-3-opus-20240229" in models
            assert "claude-3-sonnet-20240229" in models
            assert "claude-3-haiku-20240229" in models
            assert "description" in models["claude-3-opus-20240229"]


@pytest.mark.unit
class TestModuleFunctions:
    """Test module-level functions."""

    def test_get_client_creates_new_instance(self):
        """Test get_client creates new instance when none exists."""
        # Reset global state
        import claif_cla.client

        claif_cla.client._client = None
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client = get_client(mock_config)

            assert isinstance(client, ClaudeClient)
            assert claif_cla.client._client is client

    def test_get_client_returns_existing_instance(self):
        """Test get_client returns existing instance."""
        # Reset global state
        import claif_cla.client

        claif_cla.client._client = None
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            client1 = get_client(mock_config)
            client2 = get_client(mock_config)

            assert client1 is client2

    def test_get_client_recreates_if_not_initialized(self):
        """Test get_client recreates client if not initialized."""
        # Reset global state
        import claif_cla.client

        claif_cla.client._client = None
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper"):
            # Create uninitialized client
            client1 = ClaudeClient(mock_config)
            client1._initialized = False
            claif_cla.client._client = client1

            # get_client should recreate it
            client2 = get_client(mock_config)

            assert client2._initialized is True

    @pytest.mark.asyncio
    async def test_query_module_function_with_config(self):
        """Test module-level query function with provided config."""
        # Reset global state
        import claif_cla.client

        claif_cla.client._client = None
        ClaudeClient._instance = None

        mock_config = Mock()
        with patch("claif_cla.client.ClaudeWrapper") as mock_wrapper_class:
            mock_wrapper = Mock()
            mock_wrapper_class.return_value = mock_wrapper

            # Mock async generator
            async def mock_query_generator(*args, **kwargs):
                yield Mock(role=MessageRole.ASSISTANT, content="Response")

            mock_wrapper.query = mock_query_generator

            messages = []
            async for msg in query("Test prompt", config=mock_config):
                messages.append(msg)

            assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_query_module_function_loads_config(self):
        """Test module-level query function loads config when none provided."""
        # Reset global state
        import claif_cla.client

        claif_cla.client._client = None
        ClaudeClient._instance = None

        mock_config = Mock()
        with (
            patch("claif_cla.client.ClaudeWrapper") as mock_wrapper_class,
            patch("claif.common.config.load_config") as mock_load_config,
        ):
            mock_load_config.return_value = mock_config
            mock_wrapper = Mock()
            mock_wrapper_class.return_value = mock_wrapper

            # Mock async generator
            async def mock_query_generator(*args, **kwargs):
                yield Mock(role=MessageRole.ASSISTANT, content="Response")

            mock_wrapper.query = mock_query_generator

            messages = []
            async for msg in query("Test prompt"):
                messages.append(msg)

            assert len(messages) == 1
            mock_load_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_module_function_with_options(self):
        """Test module-level query function with options."""
        # Reset global state
        import claif_cla.client

        claif_cla.client._client = None
        ClaudeClient._instance = None

        mock_config = Mock()
        options = ClaifOptions(model="claude-3-opus")

        with patch("claif_cla.client.ClaudeWrapper") as mock_wrapper_class:
            mock_wrapper = Mock()
            mock_wrapper_class.return_value = mock_wrapper

            # Mock async generator
            async def mock_query_generator(*args, **kwargs):
                yield Mock(role=MessageRole.ASSISTANT, content="Response")

            mock_wrapper.query = mock_query_generator

            messages = []
            async for msg in query("Test prompt", options=options, config=mock_config):
                messages.append(msg)

            assert len(messages) == 1
            # Verify the test worked correctly
            assert messages[0].content[0].text == "Response"
