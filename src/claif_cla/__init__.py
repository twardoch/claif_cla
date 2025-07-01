"""CLAIF Claude wrapper - thin passthrough to claude-code-sdk."""

from typing import AsyncIterator, Optional

from claude_code_sdk import query as claude_query, ClaudeCodeOptions, Message

from ..claif.common import ClaifOptions, get_logger


logger = get_logger(__name__)


async def query(
    prompt: str,
    options: Optional[ClaifOptions] = None,
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


__all__ = ["query", "Message", "ClaudeCodeOptions"]