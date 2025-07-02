"""Tests for claif_cla.__init__ module."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from collections.abc import AsyncIterator

from claif.common import ClaifOptions, Message, MessageRole
from claude_code_sdk import AssistantMessage, UserMessage, SystemMessage, ResultMessage


@pytest.mark.unit
class TestClaudeMessageConversion:
    """Test message conversion between Claude and Claif formats."""
    
    def test_convert_user_message(self):
        """Test converting UserMessage to ClaifMessage."""
        from claif_cla import _convert_claude_message_to_claif
        
        claude_msg = UserMessage(content="Hello, Claude!")
        claif_msg = _convert_claude_message_to_claif(claude_msg)
        
        assert claif_msg is not None
        assert claif_msg.role == MessageRole.USER
        assert claif_msg.content == "Hello, Claude!"
    
    def test_convert_assistant_message_with_text_blocks(self):
        """Test converting AssistantMessage with text blocks."""
        from claif_cla import _convert_claude_message_to_claif
        
        # Mock text blocks
        block1 = Mock(text="First part")
        block2 = Mock(text="Second part")
        
        claude_msg = AssistantMessage(content=[block1, block2])
        claif_msg = _convert_claude_message_to_claif(claude_msg)
        
        assert claif_msg is not None
        assert claif_msg.role == MessageRole.ASSISTANT
        assert claif_msg.content == "First part\nSecond part"
    
    def test_convert_assistant_message_without_text_attr(self):
        """Test converting AssistantMessage with blocks lacking text attribute."""
        from claif_cla import _convert_claude_message_to_claif
        
        # Mock blocks without text attribute
        block1 = Mock(spec=[])  # No text attribute
        block1.__str__ = Mock(return_value="Block 1 string")
        
        claude_msg = AssistantMessage(content=[block1])
        claif_msg = _convert_claude_message_to_claif(claude_msg)
        
        assert claif_msg is not None
        assert claif_msg.role == MessageRole.ASSISTANT
        assert claif_msg.content == "Block 1 string"
    
    def test_skip_system_message(self):
        """Test that SystemMessage is skipped."""
        from claif_cla import _convert_claude_message_to_claif
        
        claude_msg = SystemMessage(content="System prompt")
        claif_msg = _convert_claude_message_to_claif(claude_msg)
        
        assert claif_msg is None
    
    def test_skip_result_message(self):
        """Test that ResultMessage is skipped."""
        from claif_cla import _convert_claude_message_to_claif
        
        claude_msg = ResultMessage()
        claif_msg = _convert_claude_message_to_claif(claude_msg)
        
        assert claif_msg is None
    
    def test_convert_unknown_message_type(self):
        """Test converting unknown message type."""
        from claif_cla import _convert_claude_message_to_claif
        
        # Mock unknown message type
        claude_msg = Mock()
        claude_msg.__str__ = Mock(return_value="Unknown message content")
        
        claif_msg = _convert_claude_message_to_claif(claude_msg)
        
        assert claif_msg is not None
        assert claif_msg.role == MessageRole.SYSTEM
        assert claif_msg.content == "Unknown message content"


@pytest.mark.unit
class TestCliMissingError:
    """Test CLI missing error detection."""
    
    @pytest.mark.parametrize("error_msg,expected", [
        ("command not found: claude", True),
        ("no such file or directory", True),
        ("claude is not recognized as an internal or external command", True),
        ("cannot find claude", True),
        ("claude not found", True),
        ("executable not found", True),
        ("Permission denied", True),
        ("FileNotFoundError: [Errno 2]", True),
        ("Some other error", False),
        ("Network connection failed", False),
    ])
    def test_is_cli_missing_error(self, error_msg, expected):
        """Test various error messages for CLI missing detection."""
        from claif_cla import _is_cli_missing_error
        
        error = Exception(error_msg)
        assert _is_cli_missing_error(error) == expected


@pytest.mark.asyncio
@pytest.mark.unit
class TestQuery:
    """Test the main query function."""
    
    async def test_query_success(self, mock_claude_query):
        """Test successful query execution."""
        from claif_cla import query
        
        with patch("claif_cla.claude_query", mock_claude_query):
            messages = []
            async for msg in query("Test prompt"):
                messages.append(msg)
            
            assert len(messages) == 2
            assert messages[0].role == MessageRole.USER
            assert messages[0].content == "Test prompt"
            assert messages[1].role == MessageRole.ASSISTANT
            assert messages[1].content == "Mock response"
    
    async def test_query_with_options(self, mock_claude_query, mock_claif_options):
        """Test query with custom options."""
        from claif_cla import query
        
        with patch("claif_cla.claude_query", mock_claude_query):
            messages = []
            async for msg in query("Test prompt", mock_claif_options):
                messages.append(msg)
            
            # Verify claude_query was called with correct options
            call_args = mock_claude_query.call_args
            assert call_args[1]["prompt"] == "Test prompt"
            assert call_args[1]["options"].model == "claude-3-opus-20240229"
            assert call_args[1]["options"].system_prompt == "You are a helpful assistant"
    
    async def test_query_filters_none_messages(self, mock_claude_query):
        """Test that None messages are filtered out."""
        from claif_cla import query
        
        # Mock query that returns a SystemMessage (which converts to None)
        async def mock_query_with_system(prompt, options):
            yield SystemMessage(content="System")
            yield UserMessage(content=prompt)
        
        mock_claude_query.side_effect = mock_query_with_system
        
        with patch("claif_cla.claude_query", mock_claude_query):
            messages = []
            async for msg in query("Test prompt"):
                messages.append(msg)
            
            # Only UserMessage should be returned
            assert len(messages) == 1
            assert messages[0].role == MessageRole.USER
    
    async def test_query_auto_install_on_cli_missing(self, mock_install_claude):
        """Test auto-install triggered on CLI missing error."""
        from claif_cla import query
        
        # Mock claude_query to raise CLI missing error first time
        call_count = 0
        async def mock_failing_query(prompt, options):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FileNotFoundError("claude not found")
            else:
                yield UserMessage(content=prompt)
                yield AssistantMessage(content=[Mock(text="Success after install")])
        
        mock_query = AsyncMock(side_effect=mock_failing_query)
        
        with patch("claif_cla.claude_query", mock_query), \
             patch("claif_cla.install.install_claude", mock_install_claude):
            
            messages = []
            async for msg in query("Test prompt"):
                messages.append(msg)
            
            # Verify install was called
            mock_install_claude.assert_called_once()
            
            # Verify query succeeded after install
            assert len(messages) == 2
            assert messages[1].content == "Success after install"
    
    async def test_query_auto_install_failure(self, mock_install_claude):
        """Test error when auto-install fails."""
        from claif_cla import query
        
        # Mock failed install
        mock_install_claude.return_value = {
            "installed": False,
            "message": "Installation failed"
        }
        
        # Mock claude_query to raise CLI missing error
        async def mock_failing_query(prompt, options):
            raise FileNotFoundError("claude not found")
        
        mock_query = AsyncMock(side_effect=mock_failing_query)
        
        with patch("claif_cla.claude_query", mock_query), \
             patch("claif_cla.install.install_claude", mock_install_claude):
            
            with pytest.raises(Exception) as exc_info:
                async for _ in query("Test prompt"):
                    pass
            
            assert "Claude CLI not found and auto-install failed" in str(exc_info.value)
    
    async def test_query_reraises_non_cli_errors(self):
        """Test that non-CLI errors are re-raised unchanged."""
        from claif_cla import query
        
        # Mock query that raises non-CLI error
        async def mock_failing_query(prompt, options):
            raise ValueError("Some other error")
        
        mock_query = AsyncMock(side_effect=mock_failing_query)
        
        with patch("claif_cla.claude_query", mock_query):
            with pytest.raises(ValueError) as exc_info:
                async for _ in query("Test prompt"):
                    pass
            
            assert str(exc_info.value) == "Some other error"
    
    async def test_query_install_then_retry_fails(self, mock_install_claude):
        """Test error when retry fails after successful install."""
        from claif_cla import query
        
        # Mock query that always fails
        async def mock_failing_query(prompt, options):
            raise RuntimeError("Persistent error")
        
        mock_query = AsyncMock(side_effect=mock_failing_query)
        
        # First call raises CLI missing, subsequent calls raise different error
        call_count = 0
        async def mock_query_with_changing_error(prompt, options):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FileNotFoundError("claude not found")
            else:
                raise RuntimeError("Different error after install")
        
        mock_query = AsyncMock(side_effect=mock_query_with_changing_error)
        
        with patch("claif_cla.claude_query", mock_query), \
             patch("claif_cla.install.install_claude", mock_install_claude):
            
            with pytest.raises(RuntimeError) as exc_info:
                async for _ in query("Test prompt"):
                    pass
            
            assert "Different error after install" in str(exc_info.value)


@pytest.mark.unit
def test_version():
    """Test that version is available."""
    from claif_cla import __version__
    
    assert __version__ is not None
    # Should be either a real version or the dev version
    assert __version__ == "0.0.0.dev0" or "." in __version__


@pytest.mark.unit
def test_exports():
    """Test that expected symbols are exported."""
    import claif_cla
    
    # Check main exports
    assert hasattr(claif_cla, "query")
    assert hasattr(claif_cla, "__version__")
    assert hasattr(claif_cla, "ClaudeCodeOptions")
    assert hasattr(claif_cla, "Message")
    
    # Check __all__ is defined
    assert hasattr(claif_cla, "__all__")
    assert "query" in claif_cla.__all__
    assert "__version__" in claif_cla.__all__