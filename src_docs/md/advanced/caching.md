---
# this_file: src_docs/md/advanced/caching.md
title: Chapter 9 - Advanced Features & Configuration
description: Performance optimization, caching strategies, configuration options, and troubleshooting
---

# Chapter 9: Advanced Features & Configuration

This chapter covers advanced capabilities, performance optimization techniques, comprehensive configuration options, and troubleshooting strategies for claif_cla.

## Response Caching

### Caching Architecture

claif_cla implements intelligent response caching to reduce API costs and improve performance:

```python
from claif_cla.wrapper import ResponseCache, ClaudeWrapper

# Initialize cache with custom settings
cache = ResponseCache(
    cache_dir="~/.claif/cache",
    default_ttl=3600,  # 1 hour
    max_cache_size="100MB",
    compression=True
)

# Create wrapper with caching enabled
wrapper = ClaudeWrapper(
    cache=cache,
    enable_cache=True,
    cache_strategy="smart"  # intelligent, aggressive, conservative
)
```

### Cache Key Generation

Cache keys are generated using SHA256 hashing of normalized inputs:

```python
def generate_cache_key(prompt: str, parameters: dict) -> str:
    """Generate deterministic cache key"""
    
    # Normalize parameters for consistent hashing
    normalized = {
        "prompt": prompt.strip(),
        "model": parameters.get("model"),
        "temperature": round(parameters.get("temperature", 0.7), 2),
        "max_tokens": parameters.get("max_tokens"),
        "system_message": parameters.get("system_message", "").strip()
    }
    
    # Remove None values and sort for consistency
    normalized = {k: v for k, v in normalized.items() if v is not None}
    
    # Generate SHA256 hash
    cache_input = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(cache_input.encode()).hexdigest()

# Example usage
cache_key = generate_cache_key(
    "What is machine learning?",
    {"model": "claude-3-5-sonnet-20241022", "temperature": 0.7}
)
```

### Smart Caching Strategies

#### 1. Semantic Similarity Caching

```python
class SemanticCache:
    """Cache based on semantic similarity rather than exact matches"""
    
    def __init__(self, similarity_threshold=0.85):
        self.threshold = similarity_threshold
        self.embeddings = {}  # prompt -> embedding
        self.responses = {}   # embedding_hash -> response
    
    def get_similar_response(self, prompt: str) -> dict | None:
        """Find cached response for semantically similar prompt"""
        
        prompt_embedding = self._get_embedding(prompt)
        
        for cached_prompt, cached_embedding in self.embeddings.items():
            similarity = self._cosine_similarity(prompt_embedding, cached_embedding)
            
            if similarity >= self.threshold:
                embedding_hash = self._hash_embedding(cached_embedding)
                return self.responses.get(embedding_hash)
        
        return None
    
    def cache_response(self, prompt: str, response: dict):
        """Cache response with prompt embedding"""
        embedding = self._get_embedding(prompt)
        embedding_hash = self._hash_embedding(embedding)
        
        self.embeddings[prompt] = embedding
        self.responses[embedding_hash] = response
```

#### 2. Contextual Caching

```python
class ContextualCache:
    """Cache considering conversation context"""
    
    def __init__(self):
        self.context_cache = {}  # context_hash -> responses
    
    def get_context_key(self, messages: List[dict]) -> str:
        """Generate context-aware cache key"""
        
        # Extract conversation context
        context_messages = messages[-5:]  # Last 5 messages
        
        context_summary = {
            "message_count": len(context_messages),
            "roles": [msg["role"] for msg in context_messages],
            "topics": self._extract_topics(context_messages),
            "sentiment": self._analyze_sentiment(context_messages)
        }
        
        return hashlib.sha256(
            json.dumps(context_summary, sort_keys=True).encode()
        ).hexdigest()
    
    def should_use_cache(self, messages: List[dict], cached_context: dict) -> bool:
        """Determine if cached response is still valid given context"""
        
        current_context = self._analyze_context(messages)
        
        # Check context compatibility
        context_drift = self._calculate_context_drift(
            current_context, 
            cached_context
        )
        
        return context_drift < 0.3  # Threshold for context similarity
```

#### 3. Temporal Caching

```python
class TemporalCache:
    """Time-aware caching with intelligent TTL"""
    
    def __init__(self):
        self.cache = {}
        self.access_patterns = {}
    
    def calculate_dynamic_ttl(self, cache_key: str, content_type: str) -> int:
        """Calculate TTL based on content type and access patterns"""
        
        base_ttls = {
            "factual": 86400,      # 24 hours - facts change slowly
            "creative": 3600,      # 1 hour - creative content varies
            "code": 7200,          # 2 hours - code solutions are stable
            "analysis": 1800,      # 30 minutes - analysis may become outdated
            "news": 900           # 15 minutes - news changes rapidly
        }
        
        base_ttl = base_ttls.get(content_type, 3600)
        
        # Adjust based on access patterns
        access_pattern = self.access_patterns.get(cache_key, {})
        frequency = access_pattern.get("frequency", 1)
        
        # Popular content stays cached longer
        if frequency > 10:
            base_ttl *= 2
        elif frequency > 5:
            base_ttl *= 1.5
        
        return base_ttl
```

## Performance Optimization

### 1. Connection Pooling

```python
class OptimizedClaudeClient:
    """Claude client with connection pooling and optimization"""
    
    def __init__(self, pool_size=10, **kwargs):
        self.pool_size = pool_size
        self.connection_pool = self._create_connection_pool()
        self.session_cache = {}
        
    def _create_connection_pool(self):
        """Create HTTP connection pool for better performance"""
        return httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=self.pool_size,
                max_connections=self.pool_size * 2,
                keepalive_expiry=300
            ),
            timeout=httpx.Timeout(60.0, connect=10.0)
        )
    
    async def batch_completions(self, requests: List[dict]) -> List[dict]:
        """Process multiple requests in parallel"""
        
        tasks = []
        for request in requests:
            task = asyncio.create_task(
                self._single_completion(request)
            )
            tasks.append(task)
        
        # Process with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def limited_completion(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[
            limited_completion(task) for task in tasks
        ])
        
        return results
```

### 2. Memory Optimization

```python
class MemoryOptimizedSessionManager:
    """Session manager with memory optimization"""
    
    def __init__(self, max_memory_mb=100):
        self.max_memory_mb = max_memory_mb
        self.session_cache = {}
        self.memory_usage = 0
        
    def add_session(self, session: Session):
        """Add session with memory management"""
        
        session_size = self._calculate_session_size(session)
        
        # Check memory limit
        if self.memory_usage + session_size > self.max_memory_mb * 1024 * 1024:
            self._evict_sessions(session_size)
        
        self.session_cache[session.id] = session
        self.memory_usage += session_size
    
    def _calculate_session_size(self, session: Session) -> int:
        """Calculate approximate memory usage of session"""
        size = 0
        
        # Basic session metadata
        size += len(str(session.id)) + len(session.title or "")
        
        # Messages
        for message in session.messages:
            size += len(message.content)
            size += len(json.dumps(message.metadata))
        
        # Metadata
        size += len(json.dumps(session.metadata))
        
        return size
    
    def _evict_sessions(self, required_space: int):
        """Evict least recently used sessions to free memory"""
        
        # Sort by last access time
        sessions_by_access = sorted(
            self.session_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        freed_space = 0
        for session_id, session in sessions_by_access:
            if freed_space >= required_space:
                break
                
            session_size = self._calculate_session_size(session)
            del self.session_cache[session_id]
            self.memory_usage -= session_size
            freed_space += session_size
```

### 3. Request Optimization

```python
class RequestOptimizer:
    """Optimize API requests for better performance"""
    
    def __init__(self):
        self.model_capabilities = self._load_model_capabilities()
        self.cost_matrix = self._load_cost_matrix()
    
    def optimize_request(self, request: dict) -> dict:
        """Optimize request parameters for best performance/cost ratio"""
        
        optimized = request.copy()
        
        # Model selection optimization
        optimized["model"] = self._select_optimal_model(
            request.get("messages", []),
            request.get("max_tokens", 1000),
            request.get("complexity_hint", "medium")
        )
        
        # Parameter optimization
        optimized = self._optimize_parameters(optimized)
        
        # Context optimization
        optimized["messages"] = self._optimize_context(
            optimized.get("messages", [])
        )
        
        return optimized
    
    def _select_optimal_model(self, messages: List[dict], max_tokens: int, complexity: str) -> str:
        """Select best model based on requirements"""
        
        # Calculate request complexity
        message_length = sum(len(msg.get("content", "")) for msg in messages)
        
        if complexity == "simple" or message_length < 1000:
            return "claude-3-haiku-20240307"  # Fast and cheap
        elif complexity == "complex" or "analyze" in str(messages).lower():
            return "claude-3-opus-20240229"   # Most capable
        else:
            return "claude-3-5-sonnet-20241022"  # Balanced
    
    def _optimize_context(self, messages: List[dict]) -> List[dict]:
        """Optimize conversation context for efficiency"""
        
        if len(messages) <= 10:
            return messages
        
        # Keep system message and recent messages
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        recent_messages = messages[-8:]  # Last 8 messages
        
        # Add most important historical messages
        historical = messages[len(system_messages):-8]
        important_historical = self._select_important_messages(historical, max_count=5)
        
        return system_messages + important_historical + recent_messages
```

## Configuration Management

### 1. Hierarchical Configuration

```python
class ConfigurationManager:
    """Hierarchical configuration management"""
    
    def __init__(self):
        self.config_sources = [
            DefaultConfig(),
            GlobalConfig("~/.claif/config.json"),
            ProjectConfig(".claif.json"),
            EnvironmentConfig(),
            RuntimeConfig()
        ]
    
    def get(self, key: str, default=None):
        """Get configuration value with precedence"""
        
        for source in reversed(self.config_sources):  # Higher precedence first
            value = source.get(key)
            if value is not None:
                return value
        
        return default
    
    def set(self, key: str, value, scope="runtime"):
        """Set configuration value in specified scope"""
        
        source_map = {
            "global": 1,
            "project": 2,
            "runtime": 4
        }
        
        source_index = source_map.get(scope, 4)
        self.config_sources[source_index].set(key, value)
    
    def reload(self):
        """Reload configuration from all sources"""
        for source in self.config_sources:
            source.reload()

class GlobalConfig:
    """Global configuration from ~/.claif/config.json"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path).expanduser()
        self.config = {}
        self.reload()
    
    def reload(self):
        """Reload configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}
    
    def get(self, key: str):
        """Get configuration value using dot notation"""
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def set(self, key: str, value):
        """Set configuration value using dot notation"""
        keys = key.split(".")
        config = self.config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value
        config[keys[-1]] = value
        
        # Save to file
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
```

### 2. Environment-Specific Configuration

```python
class EnvironmentConfig:
    """Environment-based configuration"""
    
    def __init__(self):
        self.env_mapping = {
            "CLAIF_DEFAULT_MODEL": "client.model",
            "CLAIF_API_KEY": "client.api_key", 
            "CLAIF_TIMEOUT": "client.timeout",
            "CLAIF_SESSION_DIR": "session.directory",
            "CLAIF_CACHE_TTL": "cache.default_ttl",
            "CLAIF_LOG_LEVEL": "logging.level"
        }
    
    def get(self, key: str):
        """Get value from environment variables"""
        
        # Check direct environment variable
        env_key = f"CLAIF_{key.upper().replace('.', '_')}"
        if env_key in os.environ:
            return self._convert_type(os.environ[env_key])
        
        # Check mapped environment variables
        for env_var, config_key in self.env_mapping.items():
            if config_key == key and env_var in os.environ:
                return self._convert_type(os.environ[env_var])
        
        return None
    
    def _convert_type(self, value: str):
        """Convert string environment variable to appropriate type"""
        
        # Boolean conversion
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        
        # Integer conversion
        try:
            if "." not in value:
                return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # String (default)
        return value
```

### 3. Dynamic Configuration Updates

```python
class DynamicConfigurationManager:
    """Configuration manager with live updates"""
    
    def __init__(self):
        self.config = {}
        self.watchers = []
        self.update_callbacks = defaultdict(list)
    
    def watch_file(self, file_path: str):
        """Watch configuration file for changes"""
        
        watcher = FileWatcher(file_path, self._on_file_changed)
        self.watchers.append(watcher)
        watcher.start()
    
    def register_callback(self, key_pattern: str, callback):
        """Register callback for configuration changes"""
        self.update_callbacks[key_pattern].append(callback)
    
    def _on_file_changed(self, file_path: str):
        """Handle configuration file changes"""
        
        try:
            with open(file_path) as f:
                new_config = json.load(f)
            
            # Find changes
            changes = self._find_changes(self.config, new_config)
            
            # Update configuration
            self.config.update(new_config)
            
            # Notify callbacks
            self._notify_callbacks(changes)
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
    
    def _find_changes(self, old_config: dict, new_config: dict) -> dict:
        """Find configuration changes"""
        changes = {}
        
        def compare_dicts(old, new, path=""):
            for key, value in new.items():
                full_key = f"{path}.{key}" if path else key
                
                if key not in old:
                    changes[full_key] = {"action": "added", "value": value}
                elif isinstance(value, dict) and isinstance(old[key], dict):
                    compare_dicts(old[key], value, full_key)
                elif old[key] != value:
                    changes[full_key] = {
                        "action": "changed",
                        "old_value": old[key],
                        "new_value": value
                    }
        
        compare_dicts(old_config, new_config)
        return changes
    
    def _notify_callbacks(self, changes: dict):
        """Notify registered callbacks of changes"""
        
        for change_key, change_info in changes.items():
            for pattern, callbacks in self.update_callbacks.items():
                if self._key_matches_pattern(change_key, pattern):
                    for callback in callbacks:
                        try:
                            callback(change_key, change_info)
                        except Exception as e:
                            logger.error(f"Configuration callback failed: {e}")
```

## Monitoring and Metrics

### 1. Performance Metrics

```python
class PerformanceMonitor:
    """Monitor claif_cla performance metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.start_time = time.time()
    
    def record_api_call(self, duration: float, model: str, tokens: int):
        """Record API call metrics"""
        self.metrics["api_call_duration"].append(duration)
        self.metrics["tokens_used"].append(tokens)
        self.counters[f"calls_by_model_{model}"] += 1
        self.counters["total_api_calls"] += 1
    
    def record_cache_hit(self, cache_key: str):
        """Record cache hit"""
        self.counters["cache_hits"] += 1
        self.counters["total_cache_requests"] += 1
    
    def record_cache_miss(self, cache_key: str):
        """Record cache miss"""
        self.counters["cache_misses"] += 1
        self.counters["total_cache_requests"] += 1
    
    def get_statistics(self) -> dict:
        """Get comprehensive performance statistics"""
        
        uptime = time.time() - self.start_time
        
        stats = {
            "uptime_seconds": uptime,
            "counters": dict(self.counters),
            "averages": {},
            "rates": {}
        }
        
        # Calculate averages
        if self.metrics["api_call_duration"]:
            stats["averages"]["api_call_duration"] = np.mean(self.metrics["api_call_duration"])
            stats["averages"]["tokens_per_call"] = np.mean(self.metrics["tokens_used"])
        
        # Calculate rates
        if uptime > 0:
            stats["rates"]["calls_per_second"] = self.counters["total_api_calls"] / uptime
            stats["rates"]["tokens_per_second"] = sum(self.metrics["tokens_used"]) / uptime
        
        # Cache statistics
        if self.counters["total_cache_requests"] > 0:
            stats["cache_hit_rate"] = (
                self.counters["cache_hits"] / self.counters["total_cache_requests"]
            )
        
        return stats
```

### 2. Health Monitoring

```python
class HealthMonitor:
    """Monitor system health and availability"""
    
    def __init__(self, client: ClaudeClient):
        self.client = client
        self.health_checks = [
            self._check_api_connectivity,
            self._check_session_storage,
            self._check_cache_storage,
            self._check_disk_space,
            self._check_memory_usage
        ]
    
    async def run_health_checks(self) -> dict:
        """Run all health checks and return status"""
        
        results = {}
        overall_status = "healthy"
        
        for check in self.health_checks:
            check_name = check.__name__.replace("_check_", "")
            
            try:
                status, details = await check()
                results[check_name] = {
                    "status": status,
                    "details": details,
                    "timestamp": datetime.now().isoformat()
                }
                
                if status in ("unhealthy", "critical"):
                    overall_status = "unhealthy"
                elif status == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                    
            except Exception as e:
                results[check_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                overall_status = "unhealthy"
        
        results["overall_status"] = overall_status
        return results
    
    async def _check_api_connectivity(self) -> tuple[str, dict]:
        """Check API connectivity"""
        try:
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "health check"}],
                max_tokens=10
            )
            
            duration = time.time() - start_time
            
            if duration > 10:
                return "warning", {"latency": duration, "message": "High latency"}
            
            return "healthy", {"latency": duration, "response_id": response.id}
            
        except Exception as e:
            return "unhealthy", {"error": str(e)}
```

This comprehensive advanced features guide covers optimization, configuration, and monitoring for production claif_cla deployments! ⚡