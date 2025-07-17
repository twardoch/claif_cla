# this_file: claif_cla/src/claif_cla/client.py

import asyncio
import sys
import time
from collections.abc import AsyncIterator
from typing import Any, Dict, Optional, Union

from claif.common import ClaifOptions, ClaifTimeoutError, Message, ProviderError
from claif.common.install import InstallError
from claif.common.utils import _print_error, _print_success, _print_warning
from loguru import logger
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from claif_cla.install import install_claude, is_claude_installed
from claif_cla.wrapper import ClaudeWrapper


class ClaudeClient:
    """
    Client for interacting with the Claude CLI.

    Manages the Claude CLI subprocess, handles queries, and processes responses.
    """

    _instance: Optional["ClaudeClient"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ClaudeClient":
        """Singleton pattern for ClaudeClient."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Any):
        """
        Initializes the ClaudeClient.

        Args:
            config: The Claif configuration object.
        """
        if self._initialized:
            return

        self.config = config
        self.wrapper = ClaudeWrapper(config)
        self._initialized = True
        logger.debug("ClaudeClient initialized.")

    def _claude_to_claif_message(self, claude_message) -> Message:
        """Convert ClaudeMessage to Claif Message format."""
        from claif.common import MessageRole, TextBlock
        
        # Handle mock objects that don't have proper attributes
        if hasattr(claude_message, 'role') and hasattr(claude_message, 'content'):
            role = claude_message.role if claude_message.role else MessageRole.ASSISTANT
            content = claude_message.content if claude_message.content else []
            
            # If content is a string, wrap it in TextBlock
            if isinstance(content, str):
                content = [TextBlock(text=content)]
            elif isinstance(content, list):
                # Convert content blocks to TextBlocks
                converted_content = []
                for block in content:
                    if hasattr(block, 'text'):
                        converted_content.append(TextBlock(text=block.text))
                    elif isinstance(block, str):
                        converted_content.append(TextBlock(text=block))
                    else:
                        # Fallback for unknown block types
                        converted_content.append(TextBlock(text=str(block)))
                content = converted_content
                # If content is empty list, create default TextBlock
                if not content:
                    content = [TextBlock(text=str(claude_message.content))]
            else:
                content = [TextBlock(text=str(content))]
            
            return Message(role=role, content=content)
        else:
            # Fallback for malformed messages
            return Message(role=MessageRole.ASSISTANT, content=[TextBlock(text=str(claude_message))])

    async def query(
        self,
        prompt: str,
        options: Optional[ClaifOptions] = None,
    ) -> AsyncIterator[Message]:
        """
        Sends a query to the Claude CLI and yields messages.

        Handles auto-installation of the Claude CLI if it's missing.

        Args:
            prompt: The prompt to send.
            options: Optional ClaifOptions for the query.

        Yields:
            Message: Messages received from the Claude CLI.

        Raises:
            ProviderError: If the query fails after retries or due to a critical error.
        """
        if options is None:
            options = ClaifOptions()

        logger.debug(f"Querying Claude with prompt: {prompt[:100]}...")

        try:
            async for claude_message in self.wrapper.query(prompt, options):
                # Convert ClaudeMessage to Claif Message
                yield self._claude_to_claif_message(claude_message)
        except Exception as e:
            logger.error(f"Claude query failed: {e}")
            msg = f"Claude query failed: {e}"
            raise ProviderError(provider="claude", message=str(e)) from e

    async def is_available(self) -> bool:
        """Check if Claude CLI is installed and executable."""
        return is_claude_installed()

    async def get_models(self) -> dict[str, Any]:
        """Get available Claude models (currently hardcoded)."""
        return {
            "claude-3-opus-20240229": {"description": "Claude 3 Opus (most powerful)"},
            "claude-3-sonnet-20240229": {"description": "Claude 3 Sonnet (balanced)"},
            "claude-3-haiku-20240229": {"description": "Claude 3 Haiku (fastest)"},
        }


_client: ClaudeClient | None = None


def get_client(config: Any) -> ClaudeClient:
    """Get singleton ClaudeClient instance."""
    global _client
    if _client is None or not _client._initialized:
        _client = ClaudeClient(config)
    return _client


async def query(prompt: str, options: Optional[ClaifOptions] = None, config: Any = None) -> AsyncIterator[Message]:
    """Module-level query function to access the singleton client."""
    from claif.common.config import load_config
    
    if config is None:
        config = load_config()
    
    client = get_client(config)
    async for msg in client.query(prompt, options):
        yield msg
