"""Claif Claude wrapper - thin passthrough to claude-code-sdk."""

from collections.abc import AsyncIterator

from claif.common import ClaifOptions, MessageRole
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
    """Convert claude-code-sdk message to Claif message."""
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


def _is_cli_missing_error(error: Exception) -> bool:
    """Check if error indicates missing CLI tool."""
    error_str = str(error).lower()
    error_indicators = [
        "command not found",
        "no such file or directory",
        "is not recognized as an internal or external command",
        "cannot find",
        "not found",
        "executable not found",
        "claude not found",
        "permission denied",
        "filenotfounderror",
    ]
    return any(indicator in error_str for indicator in error_indicators)


async def query(
    prompt: str,
    options: ClaifOptions | None = None,
) -> AsyncIterator[ClaifMessage]:
    """Query Claude using claude-code-sdk with auto-install on missing tools.

    This function automatically installs Claude CLI if it's missing and the
    query fails due to missing tools.

    Args:
        prompt: The prompt to send to Claude
        options: Optional Claif options

    Yields:
        Messages from Claude
    """
    if options is None:
        options = ClaifOptions()

    # Convert Claif options to Claude options
    claude_options = ClaudeCodeOptions(
        model=options.model,
        system_prompt=options.system_prompt,
        cwd=None,  # Use current working directory
    )

    logger.debug(f"Querying Claude with prompt: {prompt[:100]}...")

    try:
        # First attempt: try normal query
        async for claude_message in claude_query(prompt=prompt, options=claude_options):
            claif_message = _convert_claude_message_to_claif(claude_message)
            if claif_message is not None:
                yield claif_message
    except Exception as e:
        # Check if this is a missing CLI tool error
        if _is_cli_missing_error(e):
            logger.info("Claude CLI not found, attempting auto-install...")

            # Import and run install
            from claif_cla.install import install_claude

            install_result = install_claude()

            if install_result.get("installed"):
                logger.info("Claude CLI installed, retrying query...")

                # Retry the query
                try:
                    async for claude_message in claude_query(prompt=prompt, options=claude_options):
                        claif_message = _convert_claude_message_to_claif(claude_message)
                        if claif_message is not None:
                            yield claif_message
                except Exception as retry_error:
                    logger.error(f"Query failed even after installing Claude CLI: {retry_error}")
                    raise retry_error
            else:
                error_msg = install_result.get("message", "Unknown installation error")
                logger.error(f"Auto-install failed: {error_msg}")
                msg = f"Claude CLI not found and auto-install failed: {error_msg}"
                raise Exception(msg) from e
        else:
            # Re-raise non-CLI-missing errors unchanged
            raise e


__all__ = ["ClaudeCodeOptions", "Message", "__version__", "query"]
