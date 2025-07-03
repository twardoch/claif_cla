"""Enhanced wrapper for Claude with caching and error handling."""

import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator
from pathlib import Path

from claif.common import (
    ClaifOptions,
    ClaifTimeoutError,
    Config,
    ProviderError,
)
from claude_code import ClaudeCodeClient
from claude_code.code_tools import CodeToolFactory
from claude_code_sdk import Message as ClaudeMessage
from loguru import logger
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from claif_cla import query as base_query





class ResponseCache:
    """
    A simple in-memory cache for Claude API responses with a time-to-live (TTL).

    Responses are cached based on a hash of the prompt and relevant options.
    Cached entries expire after a specified TTL.
    """

    def __init__(self, cache_dir: Path, ttl: int = 3600) -> None:
        """
        Initializes the ResponseCache.

        Args:
            cache_dir: The directory where cache files will be stored.
            ttl: The time-to-live for cache entries in seconds. Defaults to 3600 (1 hour).
        """
        self.cache_dir: Path = cache_dir
        self.ttl: int = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, prompt: str, options: ClaifOptions) -> str:
        """
        Generates a unique cache key based on the prompt and relevant query options.

        The key is a SHA256 hash of a JSON string representation of the query parameters.

        Args:
            prompt: The query prompt string.
            options: The `ClaifOptions` object containing query parameters.

        Returns:
            A SHA256 hash string representing the cache key.
        """
        key_data: Dict[str, Any] = {
            "prompt": prompt,
            "model": options.model,
            "temperature": options.temperature,
            "system_prompt": options.system_prompt,
            # Add other relevant options that should differentiate cache entries
        }
        key_str: str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prompt: str, options: ClaifOptions) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves a cached response if available and not expired.

        Args:
            prompt: The query prompt string.
            options: The `ClaifOptions` object. Caching is only performed if `options.cache` is True.

        Returns:
            A list of dictionaries representing cached messages, or None if no valid
            cached entry is found or caching is disabled.
        """
        if not options.cache:
            return None

        key: str = self._get_cache_key(prompt, options)
        cache_file: Path = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data: Dict[str, Any] = json.load(f)

            # Check if the cached entry has expired.
            if time.time() - data["timestamp"] > self.ttl:
                cache_file.unlink()  # Remove expired entry
                logger.debug(f"Cache entry for key {key} expired and removed.")
                return None

            logger.debug(f"Cache hit for key {key}")
            return data["messages"]

        except Exception as e:
            logger.warning(f"Failed to read from cache file {cache_file}: {e}")
            return None

    def set(self, prompt: str, options: ClaifOptions, messages: List[Dict[str, Any]]) -> None:
        """
        Caches a response.

        Args:
            prompt: The query prompt string.
            options: The `ClaifOptions` object. Caching is only performed if `options.cache` is True.
            messages: A list of dictionaries representing the messages to cache.
        """
        if not options.cache:
            return

        key: str = self._get_cache_key(prompt, options)
        cache_file: Path = self.cache_dir / f"{key}.json"

        try:
            data: Dict[str, Any] = {
                "timestamp": time.time(),
                "prompt": prompt,
                "options": {
                    "model": options.model,
                    "temperature": options.temperature,
                    "system_prompt": options.system_prompt,
                }, # Store relevant options for debugging/inspection
                "messages": messages,
            }

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2) # Use indent for readability

            logger.debug(f"Cached response for key {key} to {cache_file}")

        except Exception as e:
            logger.warning(f"Failed to write to cache file {cache_file}: {e}")


class ClaudeWrapper:
    """
    An enhanced wrapper for interacting with the Claude LLM via `claude_code_sdk`.

    This wrapper provides functionalities such as response caching, retry mechanisms
    for transient failures, and robust error handling, building upon the base
    `claude_code_sdk` client.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the ClaudeWrapper with a given configuration.

        Args:
            config: A `Config` object containing API keys, retry settings, and cache TTL.
        """
        self.config: Config = config
        self.client: ClaudeCodeClient = ClaudeCodeClient(api_key=self.config.api_key)
        self.tool_factory: CodeToolFactory = CodeToolFactory()
        
        # Configure response caching.
        cache_dir: Path = Path.home() / ".claif" / "cache" / "claude"
        self.cache: ResponseCache = ResponseCache(cache_dir, self.config.cache_ttl)
        
        # Retrieve retry parameters from the configuration.
        self.retry_count: int = self.config.retry_config.get("count", 3)
        self.retry_delay: float = self.config.retry_config.get("delay", 1.0)
        self.retry_backoff: float = self.config.retry_config.get("backoff", 2.0) # Default backoff factor

    async def query(
        self,
        prompt: str,
        options: Optional[ClaifOptions] = None,
    ) -> AsyncIterator[ClaudeMessage]:
        """
        Sends a query to the Claude LLM with enhanced features like caching and retries.

        Args:
            prompt: The input prompt string for the Claude model.
            options: Optional `ClaifOptions` to override default behavior for this query.

        Yields:
            An asynchronous iterator of `ClaudeMessage` objects representing the LLM's response.

        Raises:
            ClaifTimeoutError: If the query times out after all retry attempts.
            ProviderError: If the Claude API returns a specific error (e.g., quota exceeded)
                           or if all retries fail due to other provider-related issues.
            Exception: For any other unexpected errors during the query process.
        """
        if options is None:
            options = ClaifOptions()

        # Attempt to retrieve the response from cache first.
        cached_messages_data: Optional[List[Dict[str, Any]]] = self.cache.get(prompt, options)
        if cached_messages_data:
            logger.debug("Serving response from cache.")
            for msg_data in cached_messages_data:
                yield self._dict_to_message(msg_data)
            return

        # Determine retry settings for the current query, prioritizing options over config defaults.
        retry_count: int = getattr(options, "retry_count", self.retry_count)
        retry_delay: float = getattr(options, "retry_delay", self.retry_delay)
        # Use the instance's retry_backoff as it's a global config setting.
        retry_backoff: float = self.retry_backoff
        no_retry: bool = getattr(options, "no_retry", False)

        # If retries are explicitly disabled or the retry count is zero/negative,
        # execute the query once without any retry mechanism.
        if no_retry or retry_count <= 0:
            messages_to_cache: List[Dict[str, Any]] = []
            async for message in base_query(prompt, options):
                messages_to_cache.append(self._message_to_dict(message))
                yield message

            # Cache the successful response if caching is enabled.
            if messages_to_cache and options.cache:
                self.cache.set(prompt, options, messages_to_cache)
            return

        # List to collect messages for caching after successful retrieval.
        messages_to_cache = []
        last_error: Optional[Exception] = None

        # Define exceptions that trigger a retry.
        retry_exceptions: Tuple[Type[Exception], ...] = (
            ClaifTimeoutError,  # Custom timeout error from Claif
            ProviderError,      # Custom provider-specific errors
            ConnectionError,    # Network connection issues
            asyncio.TimeoutError, # asyncio-specific timeout
            Exception,          # Catch-all for unexpected errors during query
        )

        try:
            # Configure and execute the retry mechanism using tenacity.
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(retry_count), # Stop after N attempts
                wait=wait_exponential(
                    multiplier=retry_delay,
                    min=retry_delay,
                    max=retry_delay * (retry_backoff ** (retry_count - 1)),
                ), # Exponential backoff strategy
                retry=retry_if_exception_type(retry_exceptions), # Retry only on specified exceptions
                reraise=True, # Re-raise the last exception if all retries fail
            ):
                with attempt:
                    try:
                        messages_for_current_attempt: List[Dict[str, Any]] = []
                        async for message in base_query(prompt, options):
                            messages_for_current_attempt.append(self._message_to_dict(message))
                            yield message

                        # If the current attempt is successful, update the main list for caching.
                        messages_to_cache = messages_for_current_attempt

                        # Cache the successful response if caching is enabled.
                        if messages_to_cache and options.cache:
                            self.cache.set(prompt, options, messages_to_cache)

                        return # Exit on successful attempt

                    except Exception as e:
                        last_error = e
                        logger.warning(f"Claude query attempt {attempt.retry_state.attempt_number} failed: {e}")
                        raise # Re-raise to trigger tenacity retry logic

        except RetryError as e:
            # This block is executed if all retry attempts fail.
            # It extracts the last encountered error and maps it to a more specific Claif error.
            final_error: Exception = last_error if last_error else e.__cause__ or e
            error_str: str = str(final_error).lower()
            
            # Check for specific error types and raise appropriate Claif exceptions.
            if "timeout" in error_str:
                msg = f"Claude query timed out after {retry_count} retries"
                raise ClaifTimeoutError(msg) from final_error
            elif any(indicator in error_str for indicator in ["quota", "rate limit", "429", "exhausted"]):
                msg = f"Claude API quota/rate limit exceeded after {retry_count} retries"
                raise ProviderError(
                    "claude",
                    msg,
                    {"last_error": str(final_error), "prompt_snippet": prompt[:100]}
                ) from final_error
            else:
                # For other errors, raise a generic ProviderError.
                raise ProviderError(
                    "claude",
                    f"Query failed after {retry_count} retries",
                    {
                        "last_error": str(final_error),
                        "prompt_snippet": prompt[:100],
                    },
                ) from final_error

    def _message_to_dict(self, message: ClaudeMessage) -> Dict[str, Any]:
        """
        Converts a `claude_code_sdk.Message` object to a dictionary for caching.

        This method handles both string content and structured content blocks
        (TextBlock, ToolUseBlock, ToolResultBlock) for proper serialization.

        Args:
            message: The `claude_code_sdk.Message` object to convert.

        Returns:
            A dictionary representation of the message.
        """
        content_data: Union[str, List[Dict[str, Any]]]

        if isinstance(message.content, str):
            content_data = message.content
        else:
            # Handle list of content blocks
            serialized_blocks: List[Dict[str, Any]] = []
            for block in message.content:
                if isinstance(block, ClaudeTextBlock):
                    serialized_blocks.append({"type": block.type, "text": block.text})
                elif isinstance(block, ClaudeToolUseBlock):
                    serialized_blocks.append({"type": block.type, "id": block.id, "name": block.name, "input": block.input})
                elif isinstance(block, ClaudeToolResultBlock):
                    # Recursively convert content within ToolResultBlock if it's a list of blocks
                    tool_result_content = block.content
                    if isinstance(tool_result_content, list):
                        serialized_tool_result_content = []
                        for tr_block in tool_result_content:
                            if isinstance(tr_block, ClaudeTextBlock):
                                serialized_tool_result_content.append({"type": tr_block.type, "text": tr_block.text})
                            else:
                                # Handle other potential types within tool_result_content if necessary
                                serialized_tool_result_content.append(str(tr_block))
                    else:
                        serialized_tool_result_content = str(tool_result_content)

                    serialized_blocks.append({"type": block.type, "tool_use_id": block.tool_use_id, "content": serialized_tool_result_content, "is_error": block.is_error})
                else:
                    # Fallback for any other unexpected block types
                    serialized_blocks.append({"type": "unknown", "content": str(block)})
            content_data = serialized_blocks

        return {"role": message.role, "content": content_data}

    def _dict_to_message(self, data: Dict[str, Any]) -> ClaudeMessage:
        """
        Converts a dictionary back to a `claude_code_sdk.Message` object.

        This method reconstructs the `ClaudeMessage` from its dictionary
        representation, handling both string content and structured content blocks.

        Args:
            data: A dictionary representation of the message.

        Returns:
            A `claude_code_sdk.Message` object.
        """
        content_from_dict: Union[str, List[Union[ClaudeTextBlock, ClaudeToolUseBlock, ClaudeToolResultBlock]]]

        if isinstance(data["content"], str):
            content_from_dict = data["content"]
        else:
            # Reconstruct list of content blocks
            deserialized_blocks: List[Union[ClaudeTextBlock, ClaudeToolUseBlock, ClaudeToolResultBlock]] = []
            for block_data in data["content"]:
                block_type = block_data.get("type")
                if block_type == "text":
                    deserialized_blocks.append(ClaudeTextBlock(text=block_data.get("text", "")))
                elif block_type == "tool_use":
                    deserialized_blocks.append(ClaudeToolUseBlock(id=block_data.get("id", ""), name=block_data.get("name", ""), input=block_data.get("input", {})))
                elif block_type == "tool_result":
                    # Recursively deserialize content within ToolResultBlock
                    tr_content_data = block_data.get("content")
                    deserialized_tr_content: Union[str, List[ClaudeTextBlock]]
                    if isinstance(tr_content_data, list):
                        deserialized_tr_content = []
                        for tr_block_data in tr_content_data:
                            if tr_block_data.get("type") == "text":
                                deserialized_tr_content.append(ClaudeTextBlock(text=tr_block_data.get("text", "")))
                            # Add handling for other block types within tool_result if they exist
                            else:
                                deserialized_tr_content.append(str(tr_block_data))
                    else:
                        deserialized_tr_content = str(tr_content_data)

                    deserialized_blocks.append(ClaudeToolResultBlock(tool_use_id=block_data.get("tool_use_id", ""), content=deserialized_tr_content, is_error=block_data.get("is_error", False)))
                # Add handling for any other custom block types if they exist
                else:
                    logger.warning(f"Unknown content block type encountered: {block_type}")
                    deserialized_blocks.append(ClaudeTextBlock(text=str(block_data))) # Fallback to text
            content_from_dict = deserialized_blocks

        return ClaudeMessage(role=data["role"], content=content_from_dict)
