"""Comprehensive tests for the enhanced Claude wrapper."""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from claif.common import ClaifOptions, ClaifTimeoutError, Config, Provider, ProviderError
from claif.common.types import TextBlock
from tenacity import RetryError

# Since we're mocking claude_code in conftest.py, we can import this
from claif_cla.wrapper import ClaudeWrapper, ResponseCache


@pytest.mark.unit
class TestResponseCacheComprehensive:
    """Comprehensive tests for ResponseCache functionality."""

    def test_cache_with_custom_ttl(self, temp_dir):
        """Test cache with custom TTL settings."""
        cache = ResponseCache(temp_dir, ttl=1800)  # 30 minutes

        options = ClaifOptions(model="claude-3", temperature=0.5)
        cache._get_cache_key("test prompt", options)

        # Save to cache using the set method
        messages = [{"role": "assistant", "content": "Cached response"}]
        # Since set needs options with cache=True
        options.cache = True
        cache.set("test prompt", options, messages)

        # Verify it exists using get method
        assert cache.get("test prompt", options) == messages

    @pytest.mark.asyncio
    async def test_cache_expiration(self, temp_dir):
        """Test cache expiration based on TTL."""
        import asyncio

        cache = ResponseCache(temp_dir, ttl=1)  # 1 second TTL

        options = ClaifOptions(model="claude-3", cache=True)

        # Save to cache
        messages = [{"role": "assistant", "content": "Expires soon"}]
        cache.set("test", options, messages)

        # Verify it exists immediately
        assert cache.get("test", options) == messages

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should return None after expiration
        assert cache.get("test", options) is None

    def test_cache_with_complex_options(self, temp_dir):
        """Test cache key generation with complex options."""
        cache = ResponseCache(temp_dir)

        options1 = ClaifOptions(
            model="claude-3",
            temperature=0.7,
            max_tokens=1000,
            system_prompt="Be creative",
            provider=Provider.CLAUDE,
            session_id="test-123",
        )

        options2 = ClaifOptions(
            model="claude-3",
            temperature=0.7,
            max_tokens=1000,
            system_prompt="Be creative",
            provider=Provider.CLAUDE,
            session_id="test-456",  # Different session
        )

        key1 = cache._get_cache_key("prompt", options1)
        key2 = cache._get_cache_key("prompt", options2)

        # Different session IDs should produce the same key since session_id is not part of cache key
        assert key1 == key2

    def test_cache_file_corruption_handling(self, temp_dir):
        """Test handling of corrupted cache files."""
        cache = ResponseCache(temp_dir)

        options = ClaifOptions(model="claude-3")
        key = cache._get_cache_key("test", options)

        # Create a corrupted cache file
        cache_file = cache.cache_dir / f"{key}.json"
        cache_file.write_text("invalid json {")

        # Should return None and not crash when calling get
        options.cache = True
        assert cache.get("test", options) is None


@pytest.mark.unit
class TestClaudeWrapperComprehensive:
    """Comprehensive tests for ClaudeWrapper functionality."""

    @pytest.mark.asyncio
    async def test_wrapper_initialization(self, mock_config, temp_dir):
        """Test wrapper initialization with various configurations."""
        wrapper = ClaudeWrapper(mock_config)

        assert wrapper.config == mock_config
        assert wrapper.client is not None
        assert wrapper.cache is not None
        assert wrapper.cache.ttl == 3600  # Default TTL

    @pytest.mark.asyncio
    async def test_query_with_caching_enabled(self, mock_config, temp_dir):
        """Test query with caching enabled."""
        wrapper = ClaudeWrapper(mock_config)

        options = ClaifOptions(model="claude-3", cache=True, provider=Provider.CLAUDE)

        # Mock the base query
        mock_messages = [Mock(role="assistant", content="Cached response")]

        with patch("claif_cla.wrapper.base_query") as mock_base_query:

            async def mock_query_gen(*args, **kwargs):
                for msg in mock_messages:
                    yield msg

            mock_base_query.return_value = mock_query_gen()

            # First query - should call base_query
            messages1 = []
            async for msg in wrapper.query("test prompt", options):
                messages1.append(msg)

            assert len(messages1) == 1
            mock_base_query.assert_called_once()

            # Second query - should use cache
            mock_base_query.reset_mock()
            messages2 = []
            async for msg in wrapper.query("test prompt", options):
                messages2.append(msg)

            assert len(messages2) == 1
            mock_base_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_with_retry_logic(self, mock_config, temp_dir):
        """Test query with retry logic on transient errors."""
        wrapper = ClaudeWrapper(mock_config)

        options = ClaifOptions(provider=Provider.CLAUDE, retry_count=3, retry_delay=0.1)

        call_count = 0

        with patch("claif_cla.wrapper.base_query") as mock_base_query:

            async def mock_query_with_errors(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count < 3:
                    # Fail first two attempts
                    msg = "Network error"
                    raise ConnectionError(msg)

                # Success on third attempt
                yield Mock(role="assistant", content="Success after retry")

            mock_base_query.side_effect = mock_query_with_errors

            messages = []
            async for msg in wrapper.query("test", options):
                messages.append(msg)

            assert len(messages) == 1
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_query_with_quota_error(self, mock_config, temp_dir):
        """Test query handling quota errors."""
        wrapper = ClaudeWrapper(mock_config)

        options = ClaifOptions(provider=Provider.CLAUDE)

        with patch("claif_cla.wrapper.base_query") as mock_base_query:

            async def mock_query_quota_error(*args, **kwargs):
                msg = "quota exceeded"
                raise ProviderError(msg, details={"error_type": "quota_exceeded"})
                yield  # Make it a generator

            mock_base_query.side_effect = mock_query_quota_error

            with pytest.raises(ProviderError) as exc_info:
                async for _ in wrapper.query("test", options):
                    pass

            assert "quota exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_with_custom_timeout(self, mock_config, temp_dir):
        """Test query with custom timeout handling."""
        wrapper = ClaudeWrapper(mock_config)

        options = ClaifOptions(
            provider=Provider.CLAUDE,
            timeout=1,  # 1 second timeout
        )

        with patch("claif_cla.wrapper.base_query") as mock_base_query:

            async def mock_slow_query(*args, **kwargs):
                await asyncio.sleep(2)  # Longer than timeout
                yield Mock(role="assistant", content="Too slow")

            mock_base_query.side_effect = mock_slow_query

            with pytest.raises(ClaifTimeoutError):
                async for _ in wrapper.query("test", options):
                    pass

    @pytest.mark.asyncio
    async def test_cleanup_on_error(self, mock_config, temp_dir):
        """Test proper cleanup when errors occur."""
        wrapper = ClaudeWrapper(mock_config)

        # Verify client cleanup is called on error
        with patch.object(wrapper.client, "close") as mock_close:
            with patch("claif_cla.wrapper.base_query") as mock_base_query:

                async def mock_error_query(*args, **kwargs):
                    msg = "Test error"
                    raise RuntimeError(msg)
                    yield

                mock_base_query.side_effect = mock_error_query

                with pytest.raises(RuntimeError):
                    async for _ in wrapper.query("test", ClaifOptions()):
                        pass

            # Close should still be called for cleanup
            mock_close.assert_called()

    @pytest.mark.asyncio
    async def test_parallel_queries(self, mock_config, temp_dir):
        """Test handling multiple parallel queries."""
        wrapper = ClaudeWrapper(mock_config)

        options = ClaifOptions(provider=Provider.CLAUDE)

        with patch("claif_cla.wrapper.base_query") as mock_base_query:

            async def mock_query_gen(prompt, *args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate some delay
                yield Mock(role="assistant", content=f"Response to: {prompt}")

            mock_base_query.side_effect = mock_query_gen

            # Run multiple queries in parallel
            tasks = []
            for i in range(5):

                async def collect_messages(prompt):
                    messages = []
                    async for msg in wrapper.query(prompt, options):
                        messages.append(msg)
                    return messages

                task = asyncio.create_task(collect_messages(f"Query {i}"))
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # Verify all queries completed
            assert len(results) == 5
            for i, messages in enumerate(results):
                assert len(messages) == 1


@pytest.mark.unit
class TestClaudeWrapperEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_config, temp_dir):
        """Test handling of empty responses."""
        wrapper = ClaudeWrapper(mock_config)

        with patch("claif_cla.wrapper.base_query") as mock_base_query:

            async def mock_empty_query(*args, **kwargs):
                # Don't yield anything
                return
                yield

            mock_base_query.side_effect = mock_empty_query

            messages = []
            async for msg in wrapper.query("test", ClaifOptions()):
                messages.append(msg)

            assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_malformed_message_handling(self, mock_config, temp_dir):
        """Test handling of malformed messages."""
        wrapper = ClaudeWrapper(mock_config)

        with patch("claif_cla.wrapper.base_query") as mock_base_query:

            async def mock_malformed_query(*args, **kwargs):
                # Yield various malformed messages
                yield None  # None message
                yield Mock(role=None, content="No role")  # Missing role
                yield Mock(role="assistant", content=None)  # None content
                yield Mock(role="assistant", content="Valid")  # Valid message

            mock_base_query.side_effect = mock_malformed_query

            messages = []
            async for msg in wrapper.query("test", ClaifOptions()):
                if msg and hasattr(msg, "role") and hasattr(msg, "content"):
                    messages.append(msg)

            # Only the valid message should be processed
            assert len(messages) == 1
            assert len(messages[0].content) == 1
            assert messages[0].content[0].text == "Valid"
