# this_file: claif_cla/tests/test_functional.py
"""Functional tests for claif_cla that validate actual client behavior."""

from unittest.mock import MagicMock, patch

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from claif_cla.client import ClaudeClient


class TestClaudeClientFunctional:
    """Functional tests for the ClaudeClient."""

    @pytest.fixture
    def mock_claude_response(self):
        """Create a mock response string from Claude."""
        return "Hello! I'm Claude, an AI assistant created by Anthropic. How can I help you today?"

    @patch("claif_cla.client.HAS_CLAUDE_CODE_SDK", True)
    @patch("claif_cla.client.ClaudeCodeClient")
    def test_basic_query(self, mock_client_class, mock_claude_response):
        """Test basic non-streaming query functionality."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.query.return_value = mock_claude_response
        mock_client_class.return_value = mock_client

        # Create client
        client = ClaudeClient(api_key="test-key")

        # Execute
        response = client.chat.completions.create(
            model="claude-3-5-sonnet-20241022", messages=[{"role": "user", "content": "Hello Claude"}]
        )

        # Verify response structure
        assert isinstance(response, ChatCompletion)
        assert response.choices[0].message.content == mock_claude_response
        assert response.choices[0].message.role == "assistant"
        assert response.model == "claude-3-5-sonnet-20241022"

        # Verify the SDK was called
        mock_client.query.assert_called_once()
        call_args = mock_client.query.call_args
        assert "Hello Claude" in call_args[0][0]  # First positional argument

    @patch("claif_cla.client.HAS_CLAUDE_CODE_SDK", True)
    @patch("claif_cla.client.ClaudeCodeClient")
    def test_streaming_query(self, mock_client_class):
        """Test streaming query functionality."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.query.return_value = "Hello from Claude!"
        mock_client_class.return_value = mock_client

        client = ClaudeClient()

        # Execute with streaming
        stream = client.chat.completions.create(
            model="claude-3-5-sonnet-20241022", messages=[{"role": "user", "content": "Hello"}], stream=True
        )

        # Collect chunks
        chunks = list(stream)

        # Verify we got chunks
        assert len(chunks) >= 2  # At least role chunk and content chunk
        assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)

        # First chunk should have role
        assert chunks[0].choices[0].delta.role == "assistant"

        # Verify content in subsequent chunks
        content_parts = []
        for chunk in chunks[1:]:
            if chunk.choices and chunk.choices[0].delta.content:
                content_parts.append(chunk.choices[0].delta.content)

        # Should have the full response
        full_content = "".join(content_parts)
        assert "Hello from Claude!" in full_content

    @patch("claif_cla.client.HAS_CLAUDE_CODE_SDK", True)
    @patch("claif_cla.client.ClaudeCodeClient")
    def test_with_parameters(self, mock_client_class, mock_claude_response):
        """Test query with additional parameters."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.query.return_value = mock_claude_response
        mock_client_class.return_value = mock_client

        client = ClaudeClient()

        # Execute with parameters
        client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "Write a hello world function"},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        # Verify parameters were passed
        mock_client.query.assert_called_once()
        call_args = mock_client.query.call_args

        # Check that system prompt and parameters were passed
        assert call_args.kwargs.get("temperature") == 0.7
        assert call_args.kwargs.get("max_tokens") == 100
        assert call_args.kwargs.get("system") == "You are a helpful coding assistant."

    @patch("claif_cla.client.HAS_CLAUDE_CODE_SDK", True)
    @patch("claif_cla.client.ClaudeCodeClient")
    def test_multi_turn_conversation(self, mock_client_class, mock_claude_response):
        """Test multi-turn conversation handling."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.query.return_value = mock_claude_response
        mock_client_class.return_value = mock_client

        client = ClaudeClient()

        # Execute with conversation history
        client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "user", "content": "Hi, my name is Alice"},
                {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
                {"role": "user", "content": "What's my name?"},
            ],
        )

        # Verify the conversation was formatted correctly
        mock_client.query.assert_called_once()
        call_args = mock_client.query.call_args
        prompt = call_args[0][0]

        # The prompt should be the last user message, but with context from previous messages
        # The implementation formats multi-turn conversations
        assert "What's my name?" in prompt

    @patch("claif_cla.client.HAS_CLAUDE_CODE_SDK", True)
    @patch("claif_cla.client.ClaudeCodeClient")
    def test_error_handling(self, mock_client_class):
        """Test error handling for API failures."""
        # Setup error mock
        mock_client = MagicMock()
        mock_client.query.side_effect = Exception("API rate limit exceeded")
        mock_client_class.return_value = mock_client

        client = ClaudeClient()

        # Execute and verify error propagates
        with pytest.raises(Exception) as exc_info:
            client.chat.completions.create(
                model="claude-3-5-sonnet-20241022", messages=[{"role": "user", "content": "Hello"}]
            )

        assert "API rate limit exceeded" in str(exc_info.value)

    @patch("claif_cla.client.HAS_CLAUDE_CODE_SDK", False)
    def test_no_sdk_error(self):
        """Test error when SDK is not installed."""
        client = ClaudeClient()

        with pytest.raises(ImportError) as exc_info:
            client.chat.completions.create(
                model="claude-3-5-sonnet-20241022", messages=[{"role": "user", "content": "Hello"}]
            )

        assert "claude-code-sdk is not installed" in str(exc_info.value)

    @patch("claif_cla.client.HAS_CLAUDE_CODE_SDK", True)
    @patch("claif_cla.client.ClaudeCodeClient")
    def test_empty_messages(self, mock_client_class):
        """Test handling of empty messages."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.query.return_value = "I need a message to respond to."
        mock_client_class.return_value = mock_client

        client = ClaudeClient()

        # Execute with empty messages
        response = client.chat.completions.create(model="claude-3-5-sonnet-20241022", messages=[])

        # Should handle gracefully
        assert isinstance(response, ChatCompletion)


class TestClaudeClientIntegration:
    """Integration tests that would run against real Claude API."""

    @pytest.mark.skip(reason="Requires Claude API key and claude-code-sdk")
    def test_real_claude_connection(self):
        """Test connection to real Claude API."""
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("No ANTHROPIC_API_KEY found")

        client = ClaudeClient(api_key=api_key)

        try:
            response = client.chat.completions.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": "Say 'test successful' and nothing else"}],
                max_tokens=10,
            )

            assert "test successful" in response.choices[0].message.content.lower()
        except Exception as e:
            pytest.skip(f"Claude API not available: {e}")

    @pytest.mark.skip(reason="Requires Claude API key and claude-code-sdk")
    def test_real_streaming(self):
        """Test streaming with real Claude API."""
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("No ANTHROPIC_API_KEY found")

        client = ClaudeClient(api_key=api_key)

        try:
            stream = client.chat.completions.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": "Count to 3"}],
                stream=True,
                max_tokens=20,
            )

            chunks = list(stream)
            assert len(chunks) > 0

            # Reconstruct message
            full_content = "".join(
                chunk.choices[0].delta.content or ""
                for chunk in chunks
                if chunk.choices and chunk.choices[0].delta.content
            )

            # Should contain numbers
            assert any(num in full_content for num in ["1", "2", "3"])
        except Exception as e:
            pytest.skip(f"Claude API not available: {e}")
