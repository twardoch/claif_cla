# this_file: claif_cla/src/claif_cla/client.py
"""Claude client with OpenAI Responses API compatibility using claude-code-sdk."""

import os
import time
from collections.abc import Iterator
from typing import Any, Union

from openai import NOT_GIVEN, NotGiven
from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta

try:
    from claude_code_sdk import Client as ClaudeCodeClient
    from claude_code_sdk.types import Message as ClaudeMessage
    HAS_CLAUDE_CODE_SDK = True
except ImportError:
    HAS_CLAUDE_CODE_SDK = False
    ClaudeCodeClient = None
    ClaudeMessage = None


class ChatCompletions:
    """Namespace for completions methods to match OpenAI client structure."""

    def __init__(self, parent: "ClaudeClient"):
        self.parent = parent

    def create(
        self,
        *,
        messages: list[ChatCompletionMessageParam],
        model: str = "claude-3-5-sonnet-20241022",
        frequency_penalty: float | None | NotGiven = NOT_GIVEN,
        function_call: Any | None | NotGiven = NOT_GIVEN,
        functions: list[Any] | None | NotGiven = NOT_GIVEN,
        logit_bias: dict[str, int] | None | NotGiven = NOT_GIVEN,
        logprobs: bool | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = NOT_GIVEN,
        n: int | None | NotGiven = NOT_GIVEN,
        presence_penalty: float | None | NotGiven = NOT_GIVEN,
        response_format: Any | None | NotGiven = NOT_GIVEN,
        seed: int | None | NotGiven = NOT_GIVEN,
        stop: str | None | list[str] | NotGiven = NOT_GIVEN,
        stream: bool | None | NotGiven = NOT_GIVEN,
        temperature: float | None | NotGiven = NOT_GIVEN,
        tool_choice: Any | None | NotGiven = NOT_GIVEN,
        tools: list[Any] | None | NotGiven = NOT_GIVEN,
        top_logprobs: int | None | NotGiven = NOT_GIVEN,
        top_p: float | None | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        # Additional parameters
        extra_headers: Any | None | NotGiven = NOT_GIVEN,
        extra_query: Any | None | NotGiven = NOT_GIVEN,
        extra_body: Any | None | NotGiven = NOT_GIVEN,
        timeout: float | NotGiven = NOT_GIVEN,
    ) -> ChatCompletion | Iterator[ChatCompletionChunk]:
        """Create a chat completion using Claude Code SDK.

        This method provides compatibility with OpenAI's chat.completions.create API.
        """
        if not HAS_CLAUDE_CODE_SDK:
            raise ImportError(
                "claude-code-sdk is not installed. Please install it with: pip install claude-code-sdk"
            )
            
        # Extract the last user message as the prompt
        prompt = ""
        system_prompt = ""
        
        for msg in messages:
            if isinstance(msg, dict):
                role = msg["role"]
                content = msg["content"]
            else:
                role = msg.role
                content = msg.content
                
            if role == "system":
                system_prompt = content
            elif role == "user":
                prompt = content  # Take the last user message
            elif role == "assistant":
                # For multi-turn conversations, append assistant responses
                if prompt:
                    prompt = f"{prompt}\n\nAssistant: {content}\n\nHuman: "
                    
        # Map parameters to claude-code-sdk options
        options = {}
        if temperature is not NOT_GIVEN:
            options["temperature"] = temperature
        if max_tokens is not NOT_GIVEN:
            options["max_tokens"] = max_tokens
        if system_prompt:
            options["system"] = system_prompt
            
        # Handle streaming
        if stream is True:
            return self._create_stream(prompt, model, options)
        else:
            return self._create_sync(prompt, model, options)

    def _create_sync(self, prompt: str, model: str, options: dict) -> ChatCompletion:
        """Create a synchronous chat completion."""
        # Call claude-code-sdk
        if hasattr(self.parent._client, 'query'):
            # Use query method if available
            response = self.parent._client.query(prompt, **options)
        else:
            # Fall back to messages API
            response = self.parent._client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **options
            )
        
        # Convert response to ChatCompletion format
        timestamp = int(time.time())
        
        # Extract content from response
        if hasattr(response, 'content'):
            if isinstance(response.content, list):
                content = "".join(
                    block.text for block in response.content 
                    if hasattr(block, 'text')
                )
            else:
                content = str(response.content)
        else:
            content = str(response)
            
        # Calculate token usage
        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, 'usage'):
            prompt_tokens = getattr(response.usage, 'input_tokens', 0)
            completion_tokens = getattr(response.usage, 'output_tokens', 0)
            
        # Create unique ID
        response_id = f"chatcmpl-{timestamp}{os.getpid()}"
        
        return ChatCompletion(
            id=response_id,
            object="chat.completion",
            created=timestamp,
            model=model,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=content,
                    ),
                    finish_reason="stop",
                    logprobs=None,
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    def _create_stream(
        self, prompt: str, model: str, options: dict
    ) -> Iterator[ChatCompletionChunk]:
        """Create a streaming chat completion."""
        # For now, implement a simple non-streaming fallback
        # In a real implementation, this would use claude-code-sdk's streaming API
        response = self._create_sync(prompt, model, options)
        
        timestamp = int(time.time())
        chunk_id = f"chatcmpl-{timestamp}{os.getpid()}"
        
        # Initial chunk with role
        yield ChatCompletionChunk(
            id=chunk_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChoiceDelta(role="assistant", content=""),
                    finish_reason=None,
                    logprobs=None,
                )
            ],
        )
        
        # Content chunk
        yield ChatCompletionChunk(
            id=chunk_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChoiceDelta(content=response.choices[0].message.content),
                    finish_reason=None,
                    logprobs=None,
                )
            ],
        )
        
        # Final chunk
        yield ChatCompletionChunk(
            id=chunk_id,
            object="chat.completion.chunk",
            created=timestamp,
            model=model,
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChoiceDelta(),
                    finish_reason="stop",
                    logprobs=None,
                )
            ],
        )


class Chat:
    """Namespace for chat-related methods to match OpenAI client structure."""

    def __init__(self, parent: "ClaudeClient"):
        self.parent = parent
        self.completions = ChatCompletions(parent)


class ClaudeClient:
    """Claude client compatible with OpenAI's chat completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 600.0,
    ):
        """Initialize the Claude client.

        Args:
            api_key: Anthropic API key (defaults to env var)
            base_url: Base URL for Claude Code SDK (optional)
            timeout: Request timeout in seconds
        """
        # Store configuration
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
        self._sdk_available = HAS_CLAUDE_CODE_SDK

        # Initialize the Claude Code SDK client if available
        if self._sdk_available:
            try:
                self._client = ClaudeCodeClient(
                    api_key=self.api_key,
                    # Add other claude-code-sdk specific parameters as needed
                )
            except Exception as e:
                # If claude-code-sdk initialization fails, provide helpful error
                raise RuntimeError(
                    f"Failed to initialize claude-code-sdk client: {e}. "
                    f"Make sure claude-code-sdk is properly installed and configured."
                )

        # Create namespace structure to match OpenAI client
        self.chat = Chat(self)

    # Convenience method for backward compatibility
    def create(self, **kwargs) -> ChatCompletion:
        """Create a chat completion (backward compatibility method)."""
        return self.chat.completions.create(**kwargs)