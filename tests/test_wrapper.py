"""Tests for the enhanced Claude wrapper."""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest

from claif.common import ClaifOptions, ClaifTimeoutError, Config, ProviderError
from claif_cla.wrapper import ResponseCache, ClaudeWrapper


@pytest.mark.unit
class TestResponseCache:
    """Test ResponseCache functionality."""
    
    def test_cache_init(self, temp_dir):
        """Test cache initialization."""
        cache_dir = temp_dir / "cache"
        cache = ResponseCache(cache_dir, ttl=3600)
        
        assert cache.cache_dir == cache_dir
        assert cache.ttl == 3600
        assert cache_dir.exists()
    
    def test_get_cache_key(self, temp_dir):
        """Test cache key generation."""
        cache = ResponseCache(temp_dir, ttl=3600)
        
        options1 = ClaifOptions(model="claude-3", temperature=0.7, system_prompt="Test")
        key1 = cache._get_cache_key("prompt", options1)
        
        # Same inputs should produce same key
        key2 = cache._get_cache_key("prompt", options1)
        assert key1 == key2
        
        # Different prompt should produce different key
        key3 = cache._get_cache_key("different", options1)
        assert key1 != key3
        
        # Different options should produce different key
        options2 = ClaifOptions(model="claude-3", temperature=0.8, system_prompt="Test")
        key4 = cache._get_cache_key("prompt", options2)
        assert key1 != key4
    
    def test_get_cache_disabled(self, temp_dir):
        """Test cache get when caching is disabled."""
        cache = ResponseCache(temp_dir)
        options = ClaifOptions(cache=False)
        
        result = cache.get("prompt", options)
        assert result is None
    
    def test_get_cache_miss(self, temp_dir):
        """Test cache miss."""
        cache = ResponseCache(temp_dir)
        options = ClaifOptions(cache=True)
        
        result = cache.get("prompt", options)
        assert result is None
    
    def test_get_cache_hit(self, temp_dir):
        """Test cache hit."""
        cache = ResponseCache(temp_dir, ttl=3600)
        options = ClaifOptions(cache=True)
        
        # Manually create cache file
        key = cache._get_cache_key("prompt", options)
        cache_file = cache.cache_dir / f"{key}.json"
        
        test_messages = [{"role": "user", "content": "test"}]
        cache_data = {
            "timestamp": time.time(),
            "messages": test_messages
        }
        
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)
        
        result = cache.get("prompt", options)
        assert result == test_messages
    
    def test_get_cache_expired(self, temp_dir):
        """Test expired cache entries are removed."""
        cache = ResponseCache(temp_dir, ttl=1)  # 1 second TTL
        options = ClaifOptions(cache=True)
        
        # Create expired cache file
        key = cache._get_cache_key("prompt", options)
        cache_file = cache.cache_dir / f"{key}.json"
        
        cache_data = {
            "timestamp": time.time() - 10,  # 10 seconds ago
            "messages": [{"role": "user", "content": "test"}]
        }
        
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)
        
        result = cache.get("prompt", options)
        assert result is None
        assert not cache_file.exists()  # Should be deleted
    
    def test_get_cache_corrupted(self, temp_dir):
        """Test handling of corrupted cache files."""
        cache = ResponseCache(temp_dir)
        options = ClaifOptions(cache=True)
        
        # Create corrupted cache file
        key = cache._get_cache_key("prompt", options)
        cache_file = cache.cache_dir / f"{key}.json"
        cache_file.write_text("invalid json")
        
        result = cache.get("prompt", options)
        assert result is None
    
    def test_set_cache_disabled(self, temp_dir):
        """Test cache set when caching is disabled."""
        cache = ResponseCache(temp_dir)
        options = ClaifOptions(cache=False)
        
        cache.set("prompt", options, [])
        
        # Should not create cache file
        assert len(list(cache.cache_dir.glob("*.json"))) == 0
    
    def test_set_cache_success(self, temp_dir):
        """Test successful cache set."""
        cache = ResponseCache(temp_dir)
        options = ClaifOptions(
            cache=True,
            model="claude-3",
            temperature=0.7
        )
        
        messages = [{"role": "assistant", "content": "response"}]
        cache.set("prompt", options, messages)
        
        # Verify cache file created
        key = cache._get_cache_key("prompt", options)
        cache_file = cache.cache_dir / f"{key}.json"
        assert cache_file.exists()
        
        # Verify content
        with open(cache_file) as f:
            data = json.load(f)
        
        assert data["prompt"] == "prompt"
        assert data["options"]["model"] == "claude-3"
        assert data["options"]["temperature"] == 0.7
        assert data["messages"] == messages
        assert "timestamp" in data
    
    def test_set_cache_write_error(self, temp_dir):
        """Test cache set handles write errors."""
        cache = ResponseCache(temp_dir)
        options = ClaifOptions(cache=True)
        
        # Make cache dir read-only
        cache.cache_dir.chmod(0o444)
        
        try:
            # Should not raise, just log warning
            cache.set("prompt", options, [])
        finally:
            # Restore permissions
            cache.cache_dir.chmod(0o755)


@pytest.mark.unit
class TestClaudeWrapper:
    """Test ClaudeWrapper functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock(spec=Config)
        config.api_key = "test-key"
        config.cache_ttl = 3600
        config.retry_config = {
            "count": 3,
            "delay": 1.0,
            "backoff": 2.0
        }
        return config
    
    @pytest.fixture
    def wrapper(self, mock_config, temp_dir):
        """Create wrapper instance."""
        with patch("claif_cla.wrapper.ClaudeCodeClient"), \
             patch("claif_cla.wrapper.CodeToolFactory"), \
             patch("pathlib.Path.home", return_value=temp_dir):
            return ClaudeWrapper(mock_config)
    
    @pytest.mark.asyncio
    async def test_query_cache_hit(self, wrapper):
        """Test query with cache hit."""
        options = ClaifOptions(cache=True)
        cached_messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]
        
        wrapper.cache.get = Mock(return_value=cached_messages)
        wrapper._dict_to_message = Mock(side_effect=lambda d: Mock(role=d["role"], content=d["content"]))
        
        messages = []
        async for msg in wrapper.query("test prompt", options):
            messages.append(msg)
        
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].content == "response"
        
        # Should not call base_query
        wrapper.cache.get.assert_called_once_with("test prompt", options)
    
    @pytest.mark.asyncio
    async def test_query_cache_miss(self, wrapper):
        """Test query with cache miss."""
        options = ClaifOptions(cache=True)
        
        # Mock cache miss
        wrapper.cache.get = Mock(return_value=None)
        wrapper.cache.set = Mock()
        
        # Mock base_query
        mock_messages = [
            Mock(role="user", content="test"),
            Mock(role="assistant", content="response")
        ]
        
        async def mock_base_query(prompt, opts):
            for msg in mock_messages:
                yield msg
        
        with patch("claif_cla.wrapper.base_query", side_effect=mock_base_query):
            messages = []
            async for msg in wrapper.query("test prompt", options):
                messages.append(msg)
        
        assert len(messages) == 2
        
        # Should cache the response
        wrapper.cache.set.assert_called_once()
        call_args = wrapper.cache.set.call_args[0]
        assert call_args[0] == "test prompt"
        assert call_args[1] == options
        assert len(call_args[2]) == 2
    
    @pytest.mark.asyncio
    async def test_query_no_cache(self, wrapper):
        """Test query without caching."""
        options = ClaifOptions(cache=False)
        
        mock_messages = [Mock(role="assistant", content="response")]
        
        async def mock_base_query(prompt, opts):
            for msg in mock_messages:
                yield msg
        
        with patch("claif_cla.wrapper.base_query", side_effect=mock_base_query):
            messages = []
            async for msg in wrapper.query("test prompt", options):
                messages.append(msg)
        
        assert len(messages) == 1
        
        # Should not interact with cache
        wrapper.cache.get = Mock()
        wrapper.cache.set = Mock()
        wrapper.cache.get.assert_not_called()
        wrapper.cache.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_query_retry_success(self, wrapper):
        """Test query retry on failure."""
        options = ClaifOptions()
        
        # Mock base_query to fail twice then succeed
        call_count = 0
        async def mock_base_query(prompt, opts):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            yield Mock(role="assistant", content="success")
        
        with patch("claif_cla.wrapper.base_query", side_effect=mock_base_query), \
             patch("asyncio.sleep"):  # Skip actual delays
            
            messages = []
            async for msg in wrapper.query("test prompt", options):
                messages.append(msg)
        
        assert len(messages) == 1
        assert messages[0].content == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_query_retry_exhausted(self, wrapper):
        """Test query when all retries are exhausted."""
        options = ClaifOptions()
        wrapper.retry_count = 2
        
        # Mock base_query to always fail
        async def mock_base_query(prompt, opts):
            raise Exception("Persistent error")
        
        with patch("claif_cla.wrapper.base_query", side_effect=mock_base_query), \
             patch("asyncio.sleep"):
            
            with pytest.raises(ProviderError) as exc_info:
                async for _ in wrapper.query("test prompt", options):
                    pass
            
            assert "Query failed after 2 retries" in str(exc_info.value)
            assert "Persistent error" in str(exc_info.value.details["last_error"])
    
    @pytest.mark.asyncio
    async def test_query_timeout_error(self, wrapper):
        """Test query timeout error handling."""
        options = ClaifOptions()
        
        async def mock_base_query(prompt, opts):
            raise TimeoutError("Request timed out")
        
        with patch("claif_cla.wrapper.base_query", side_effect=mock_base_query), \
             patch("asyncio.sleep"):
            
            with pytest.raises(ClaifTimeoutError) as exc_info:
                async for _ in wrapper.query("test prompt", options):
                    pass
            
            assert "timed out after" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_query_exponential_backoff(self, wrapper):
        """Test exponential backoff calculation."""
        options = ClaifOptions()
        wrapper.retry_delay = 1.0
        wrapper.retry_backoff = 2.0
        
        delays = []
        async def mock_sleep(delay):
            delays.append(delay)
        
        async def mock_base_query(prompt, opts):
            raise Exception("Error")
        
        with patch("claif_cla.wrapper.base_query", side_effect=mock_base_query), \
             patch("asyncio.sleep", side_effect=mock_sleep):
            
            try:
                async for _ in wrapper.query("test prompt", options):
                    pass
            except ProviderError:
                pass
        
        # Check exponential backoff: 1, 2, 4
        assert len(delays) == 3
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
    
    def test_message_to_dict_string_content(self, wrapper):
        """Test converting message with string content to dict."""
        message = Mock(role="user", content="Hello")
        
        result = wrapper._message_to_dict(message)
        
        assert result == {
            "role": "user",
            "content": "Hello"
        }
    
    def test_message_to_dict_block_content(self, wrapper):
        """Test converting message with block content to dict."""
        block1 = Mock(type="text", text="Part 1")
        block2 = Mock(type="text", text="Part 2")
        message = Mock(role="assistant", content=[block1, block2])
        
        result = wrapper._message_to_dict(message)
        
        assert result == {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Part 1"},
                {"type": "text", "text": "Part 2"}
            ]
        }
    
    def test_message_to_dict_block_without_text(self, wrapper):
        """Test converting message with blocks lacking text attribute."""
        block = Mock(type="other")
        block.text = Mock(side_effect=AttributeError())
        delattr(block, "text")  # Ensure no text attribute
        
        message = Mock(role="assistant", content=[block])
        
        result = wrapper._message_to_dict(message)
        
        assert result["content"] == [{"type": "other", "text": ""}]
    
    def test_dict_to_message(self, wrapper):
        """Test converting dict back to message."""
        data = {
            "role": "user",
            "content": "Hello"
        }
        
        with patch("claif_cla.wrapper.ClaudeMessage") as mock_message_class:
            wrapper._dict_to_message(data)
            
            mock_message_class.assert_called_once_with(
                role="user",
                content="Hello"
            )