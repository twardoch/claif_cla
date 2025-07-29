# this_file: claif_cla/tests/test_openai_client.py
"""Tests for Claude client with OpenAI compatibility."""

import unittest
from unittest.mock import MagicMock, patch

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)

from claif_cla.client import ClaudeClient


class TestClaudeClient(unittest.TestCase):
    """Test cases for ClaudeClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = ClaudeClient(api_key="test-key")

    def test_init_default(self):
        """Test client initialization with defaults."""
        client = ClaudeClient()
        assert client.api_key is None  # No key if not in env
        assert client.base_url is None
        assert client.timeout == 600.0

    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = ClaudeClient(api_key="test-key", base_url="https://custom.anthropic.com", timeout=300.0)
        assert client.api_key == "test-key"
        assert client.base_url == "https://custom.anthropic.com"
        assert client.timeout == 300.0

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"})
    def test_init_from_env(self):
        """Test client initialization from environment variables."""
        client = ClaudeClient()
        assert client.api_key == "env-key"

    def test_namespace_structure(self):
        """Test that the client has the correct namespace structure."""
        assert self.client.chat is not None
        assert self.client.chat.completions is not None
        assert hasattr(self.client.chat.completions, "create")

    @patch("anthropic.Anthropic")
    def test_create_sync(self, mock_anthropic_class):
        """Test synchronous chat completion creation."""
        # Mock the Anthropic client
        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic

        # Mock response
        mock_response = MagicMock()
        mock_response.id = "msg_123"
        mock_response.content = [MagicMock(text="Hello from Claude!")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_anthropic.messages.create.return_value = mock_response

        # Create client and make request
        client = ClaudeClient()
        response = client.chat.completions.create(
            model="claude-3-sonnet-20240229", messages=[{"role": "user", "content": "Hello"}]
        )

        # Verify response
        assert isinstance(response, ChatCompletion)
        assert response.model == "claude-3-sonnet-20240229"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Hello from Claude!"
        assert response.choices[0].message.role == "assistant"
        assert response.usage.total_tokens == 15

    @patch("anthropic.Anthropic")
    def test_create_stream(self, mock_anthropic_class):
        """Test streaming chat completion creation."""
        # Mock the Anthropic client
        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic

        # Mock streaming response
        mock_events = [
            MagicMock(type="message_start"),
            MagicMock(type="content_block_delta", delta=MagicMock(text="Hello")),
            MagicMock(type="content_block_delta", delta=MagicMock(text=" from Claude!")),
            MagicMock(type="message_delta", delta=MagicMock(stop_reason="end_turn")),
        ]
        mock_anthropic.messages.create.return_value = iter(mock_events)

        # Create client and make streaming request
        client = ClaudeClient()
        stream = client.chat.completions.create(
            model="claude-3-sonnet-20240229", messages=[{"role": "user", "content": "Hello"}], stream=True
        )

        # Collect chunks
        chunks = list(stream)

        # Verify chunks
        assert len(chunks) == 4
        assert isinstance(chunks[0], ChatCompletionChunk)
        assert chunks[0].choices[0].delta.role == "assistant"
        assert chunks[1].choices[0].delta.content == "Hello"
        assert chunks[2].choices[0].delta.content == " from Claude!"
        assert chunks[3].choices[0].finish_reason == "stop"

    @patch("anthropic.Anthropic")
    def test_message_conversion(self, mock_anthropic_class):
        """Test that messages are correctly converted to Anthropic format."""
        # Mock the Anthropic client
        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic

        # Create client and make request with various message types
        client = ClaudeClient()
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        client.chat.completions.create(model="claude-3-sonnet-20240229", messages=messages)

        # Verify the call was made with correct parameters
        mock_anthropic.messages.create.assert_called_once()
        call_args = mock_anthropic.messages.create.call_args[1]

        assert call_args["model"] == "claude-3-sonnet-20240229"
        assert call_args["system"] == "You are helpful"
        assert len(call_args["messages"]) == 3  # No system message in messages
        assert call_args["messages"][0]["role"] == "user"
        assert call_args["messages"][0]["content"] == "Hello"

    def test_model_name_mapping(self):
        """Test model name mapping from OpenAI to Claude."""
        namespace = self.client.chat.completions

        assert namespace._map_model_name("gpt-4") == "claude-3-opus-20240229"
        assert namespace._map_model_name("gpt-3.5-turbo") == "claude-3-sonnet-20240229"
        assert namespace._map_model_name("claude-3-opus") == "claude-3-opus-20240229"
        assert namespace._map_model_name("custom-model") == "custom-model"

    def test_stop_reason_mapping(self):
        """Test stop reason mapping from Anthropic to OpenAI."""
        namespace = self.client.chat.completions

        assert namespace._map_stop_reason("end_turn") == "stop"
        assert namespace._map_stop_reason("max_tokens") == "length"
        assert namespace._map_stop_reason("stop_sequence") == "stop"
        assert namespace._map_stop_reason(None) == "stop"

    def test_backward_compatibility(self):
        """Test the backward compatibility create method."""
        with patch.object(self.client.chat.completions, "create") as mock_create:
            mock_create.return_value = MagicMock(spec=ChatCompletion)

            self.client.create(model="claude-3-sonnet-20240229", messages=[{"role": "user", "content": "Hello"}])

            mock_create.assert_called_once_with(
                model="claude-3-sonnet-20240229", messages=[{"role": "user", "content": "Hello"}]
            )


if __name__ == "__main__":
    unittest.main()
