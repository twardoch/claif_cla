# this_file: claif_cla/src/claif_cla/client.py

import asyncio
import sys
import time
from collections.abc import AsyncIterator
from typing import Any, Dict

from claif.common import ClaifOptions, ClaifTimeoutError, Message, ProviderError
from claif.common.install import InstallError
from claif.common.utils import _print_error, _print_success, _print_warning
from loguru import logger
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from claif_cla.install import install_claude, is_claude_installed
from claif_cla.transport import ClaudeTransport
from claif_cla.types import Message as ClaudeMessage
from claif_cla.types import ResultMessage


class ClaudeClient:
    """
    Client for interacting with the Claude CLI.

    Manages the Claude CLI subprocess, handles queries, and processes responses.
    """

    _instance: "ClaudeClient" | None = None

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
        self.transport = ClaudeTransport(config)
        self._initialized = True
        logger.debug("ClaudeClient initialized.")

    async def query(
        self,
        prompt: str,
        options: ClaifOptions | None = None,
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

        retry_config = self.config.retry_config
        if options.no_retry:
            retry_config = {"count": 1, "delay": 0, "backoff": 1}  # No retry

        last_error: Exception | None = None

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(retry_config["count"]),
                wait=wait_exponential(
                    multiplier=retry_config["delay"], min=1, max=retry_config["backoff"] * retry_config["delay"]
                ),
                reraise=True,
            ):
                with attempt:
                    try:
                        await self.transport.connect()
                        async for response in self.transport.send_query(prompt, options):
                            if isinstance(response, ClaudeMessage):
                                yield response.to_claif_message()
                            elif isinstance(response, ResultMessage) and response.error:
                                logger.error(f"Claude error: {response.message}")
                                msg = f"Claude CLI error: {response.message}"
                                raise ProviderError(
                                    msg,
                                    details={"error_code": response.error_code, "raw_message": response.message},
                                )
                    except (InstallError, FileNotFoundError) as e:
                        _print_warning(f"Claude CLI not found or installed. Attempting auto-install: {e}")
                        try:
                            install_claude()
                            _print_success("Claude CLI installed successfully. Retrying query...")
                            # After successful install, retry the query
                            await self.transport.connect()  # Reconnect after install
                            async for response in self.transport.send_query(prompt, options):
                                if isinstance(response, ClaudeMessage):
                                    yield response.to_claif_message()
                                elif isinstance(response, ResultMessage) and response.error:
                                    logger.error(f"Claude error: {response.message}")
                                    msg = f"Claude CLI error: {response.message}"
                                    raise ProviderError(
                                        msg,
                                        details={"error_code": response.error_code, "raw_message": response.message},
                                    )
                        except Exception as install_e:
                            _print_error(f"Auto-install failed: {install_e}")
                            msg = f"Failed to install Claude CLI: {install_e}"
                            raise ProviderError(msg) from install_e
                    except TimeoutError as e:
                        msg = f"Claude query timed out after {options.timeout} seconds."
                        raise ClaifTimeoutError(msg) from e
                    except Exception as e:
                        last_error = e
                        logger.warning(f"Claude query failed: {e}. Retrying...")
                        raise  # Re-raise to trigger tenacity retry

        except Exception as e:
            if last_error:
                _print_error(f"Claude query failed after {retry_config['count']} retries: {last_error}")
                msg = f"Query failed after {retry_config['count']} retries."
                raise ProviderError(
                    msg,
                    details={"last_error": str(last_error)},
                ) from last_error
            _print_error(f"Claude query failed: {e}")
            msg = f"Claude query failed: {e}"
            raise ProviderError(msg) from e
        finally:
            await self.transport.disconnect()

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


async def query(prompt: str, options: ClaifOptions | None = None) -> AsyncIterator[Message]:
    """Module-level query function to access the singleton client."""
    client = get_client(options.config)  # Assuming options.config holds the config
    async for msg in client.query(prompt, options):
        yield msg
