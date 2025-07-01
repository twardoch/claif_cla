"""CLAIF Claude wrapper - thin passthrough to claude-code-sdk."""

from collections.abc import AsyncIterator

from claif.common import ClaifOptions
from claude_code_sdk import ClaudeCodeOptions, Message
from claude_code_sdk import query as claude_query
from loguru import logger

try:
    from claif_cla.__version__ import __version__
except ImportError:
    __version__ = "0.0.0.dev0"


async def query(
    prompt: str,
    options: ClaifOptions | None = None,
) -> AsyncIterator[Message]:
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
        temperature=options.temperature,
        max_tokens=options.max_tokens,
        system=options.system_prompt,
        timeout=options.timeout,
        verbose=options.verbose,
    )

    logger.debug(f"Querying Claude with prompt: {prompt[:100]}...")

    # Pass through to claude-code-sdk
    async for message in claude_query(prompt, claude_options):
        yield message


__all__ = ["ClaudeCodeOptions", "Message", "__version__", "query"]
