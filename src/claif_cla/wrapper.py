"""Enhanced wrapper for Claude with caching and error handling."""

import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator
from pathlib import Path

from claif.common import (
    ClaifOptions,
    Config,
    ProviderError,
)
from claif.common import (
    TimeoutError as ClaifTimeoutError,
)
from claude_code import ClaudeCodeClient
from claude_code.code_tools import CodeToolFactory
from claude_code_sdk import Message as ClaudeMessage
from loguru import logger

from claif_cla import query as base_query


class ResponseCache:
    """Simple response cache with TTL."""

    def __init__(self, cache_dir: Path, ttl: int = 3600):
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, prompt: str, options: ClaifOptions) -> str:
        """Generate cache key from prompt and options."""
        key_data = {
            "prompt": prompt,
            "model": options.model,
            "temperature": options.temperature,
            "system_prompt": options.system_prompt,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prompt: str, options: ClaifOptions) -> list | None:
        """Get cached response if available and not expired."""
        if not options.cache:
            return None

        key = self._get_cache_key(prompt, options)
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)

            # Check TTL
            if time.time() - data["timestamp"] > self.ttl:
                cache_file.unlink()
                return None

            logger.debug(f"Cache hit for key {key}")
            return data["messages"]

        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def set(self, prompt: str, options: ClaifOptions, messages: list) -> None:
        """Cache response."""
        if not options.cache:
            return

        key = self._get_cache_key(prompt, options)
        cache_file = self.cache_dir / f"{key}.json"

        try:
            data = {
                "timestamp": time.time(),
                "prompt": prompt,
                "options": {
                    "model": options.model,
                    "temperature": options.temperature,
                },
                "messages": messages,
            }

            with open(cache_file, "w") as f:
                json.dump(data, f)

            logger.debug(f"Cached response for key {key}")

        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")


class ClaudeWrapper:
    """Enhanced Claude wrapper with caching, retry, and error handling."""

    def __init__(self, config: Config):
        self.config = config
        self.client = ClaudeCodeClient(api_key=self.config.api_key)
        self.tool_factory = CodeToolFactory()
        cache_dir = Path.home() / ".claif" / "cache" / "claude"
        self.cache = ResponseCache(cache_dir, config.cache_ttl)
        self.retry_count = config.retry_config["count"]
        self.retry_delay = config.retry_config["delay"]
        self.retry_backoff = config.retry_config["backoff"]

    async def query(
        self,
        prompt: str,
        options: ClaifOptions | None = None,
    ) -> AsyncIterator[ClaudeMessage]:
        """Query Claude with enhanced features."""
        if options is None:
            options = ClaifOptions()

        # Check cache first
        cached = self.cache.get(prompt, options)
        if cached:
            for msg_data in cached:
                yield self._dict_to_message(msg_data)
            return

        # Collect messages for caching
        messages = []
        retry_count = 0
        last_error = None

        while retry_count <= self.retry_count:
            try:
                async for message in base_query(prompt, options):
                    messages.append(self._message_to_dict(message))
                    yield message

                # Cache successful response
                if messages and options.cache:
                    self.cache.set(prompt, options, messages)

                return

            except Exception as e:
                last_error = e
                retry_count += 1

                if retry_count > self.retry_count:
                    break

                # Exponential backoff
                delay = self.retry_delay * (self.retry_backoff ** (retry_count - 1))
                logger.warning(f"Query failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

        # All retries failed
        if "timeout" in str(last_error).lower():
            msg = f"Claude query timed out after {self.retry_count} retries"
            raise ClaifTimeoutError(msg)
        else:
            msg = "claude"
            raise ProviderError(
                msg,
                f"Query failed after {self.retry_count} retries",
                {
                    "last_error": str(last_error),
                    "prompt": prompt[:100],
                },
            )

    def _message_to_dict(self, message: ClaudeMessage) -> dict:
        """Convert Claude message to dict for caching."""
        return {
            "role": message.role,
            "content": message.content
            if isinstance(message.content, str)
            else [{"type": block.type, "text": getattr(block, "text", "")} for block in message.content],
        }

    def _dict_to_message(self, data: dict) -> ClaudeMessage:
        """Convert dict back to Claude message."""
        return ClaudeMessage(
            role=data["role"],
            content=data["content"],
        )
