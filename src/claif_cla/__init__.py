"""CLAIF Claude wrapper - thin passthrough to claude-code-sdk."""

from collections.abc import AsyncIterator

from claif.common import ClaifOptions, MessageRole, TextBlock
from claif.common import Message as ClaifMessage
from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    Message,
    ResultMessage,
    SystemMessage,
    UserMessage,
)
from claude_code_sdk import query as claude_query
from loguru import logger

try:
    from claif_cla.__version__ import __version__
except ImportError:
    __version__ = "0.0.0.dev0"


def _convert_claude_message_to_claif(claude_message: Message) -> ClaifMessage | None:
    """Convert claude-code-sdk message to CLAIF message."""
    if isinstance(claude_message, UserMessage):
        return ClaifMessage(
            role=MessageRole.USER,
            content=claude_message.content,
        )
    if isinstance(claude_message, AssistantMessage):
        # Convert content blocks to text for now
        text_parts = []
        for block in claude_message.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            else:
                text_parts.append(str(block))

        return ClaifMessage(
            role=MessageRole.ASSISTANT,
            content="\n".join(text_parts) if text_parts else "",
        )
    if isinstance(claude_message, SystemMessage):
        # Skip system messages for now
        return None
    if isinstance(claude_message, ResultMessage):
        # Skip result messages - they're metadata
        return None
    # Handle other message types by converting to string
    return ClaifMessage(
        role=MessageRole.SYSTEM,
        content=str(claude_message),
    )


async def query(
    prompt: str,
    options: ClaifOptions | None = None,
) -> AsyncIterator[ClaifMessage]:
    """Query Claude using claude-code-sdk.

    This is a thin wrapper that converts CLAIF options to ClaudeCodeOptions
    and passes through to the claude-code-sdk.

    Args:
        prompt: The prompt to send to Claude
        options: Optional CLAIF options

    Yields:
        Messages from Claude
    """
    if options is None:
        options = ClaifOptions()

    # Convert CLAIF options to Claude options
    claude_options = ClaudeCodeOptions(
        model=options.model,
        system_prompt=options.system_prompt,
        cwd=None,  # Use current working directory
    )

    logger.debug(f"Querying Claude with prompt: {prompt[:100]}...")

    # Pass through to claude-code-sdk and convert messages
    async for claude_message in claude_query(prompt=prompt, options=claude_options):
        claif_message = _convert_claude_message_to_claif(claude_message)
        if claif_message is not None:
            yield claif_message


__all__ = ["ClaudeCodeOptions", "Message", "__version__", "query"]
