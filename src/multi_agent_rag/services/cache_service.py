"""
Redis cache service for the multi-agent RAG system.

Provides caching functionality for:
- Research data (to avoid redundant searches)
- Vector search results (to speed up repeated queries)
- Conversation responses (for quick retrieval)

Uses redis-stack-server for JSON document support and advanced caching features.
"""

import hashlib
import json
from typing import Any

import redis
from redis.exceptions import ConnectionError, TimeoutError

from src.multi_agent_rag.core.config import (
    CACHE_ENABLED,
    CACHE_PREFIX_EMBEDDINGS,
    CACHE_PREFIX_RESEARCH,
    CACHE_PREFIX_RESPONSE,
    CACHE_PREFIX_VECTOR,
    CACHE_TTL_SECONDS,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
)
from src.multi_agent_rag.core.logging_config import logger


class CacheService:
    """
    Redis-based caching service with automatic TTL and invalidation.

    Implements the Singleton pattern to maintain a single Redis connection pool.
    Provides graceful fallback when Redis is unavailable.
    Tracks hit/miss ratios for performance auditing.
    """

    _instance = None
    _client = None

    # Stat keys
    STATS_HITS = "cache:stats:hits"
    STATS_MISSES = "cache:stats:misses"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the Redis connection."""
        if not CACHE_ENABLED:
            logger.info("Cache is disabled via configuration.")
            self._client = None
            return

        try:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Test connection
            self._client.ping()
            logger.info(f"Redis cache connected: {REDIS_HOST}:{REDIS_PORT}")
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._client = None

    @property
    def is_available(self) -> bool:
        """Check if Redis is available and responsive."""
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            return False

    def _generate_key(self, prefix: str, content: str) -> str:
        """Generate a consistent cache key from content hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        return f"{prefix}{content_hash}"

    def _track_hit(self):
        """Increment hit counter."""
        if self.is_available:
            self._client.incr(self.STATS_HITS)

    def _track_miss(self):
        """Increment miss counter."""
        if self.is_available:
            self._client.incr(self.STATS_MISSES)

    def get_stats(self) -> dict[str, Any]:
        """Retrieve cache hit/miss statistics."""
        if not self.is_available:
            return {"hits": 0, "misses": 0, "ratio": 0}

        hits = int(self._client.get(self.STATS_HITS) or 0)
        misses = int(self._client.get(self.STATS_MISSES) or 0)
        total = hits + misses
        ratio = (hits / total) if total > 0 else 0
        return {"hits": hits, "misses": misses, "ratio": round(ratio, 4)}

    # ==================== Core Cache Operations ====================

    def get(self, key: str) -> Any | None:
        """
        Retrieve a value from cache.
        """
        if not self.is_available:
            return None

        try:
            value = self._client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                self._track_hit()
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            self._track_miss()
            return None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Store a value in cache with TTL.
        """
        if not self.is_available:
            return False

        ttl = ttl or CACHE_TTL_SECONDS

        try:
            serialized = json.dumps(value)
            self._client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a specific key from cache."""
        if not self.is_available:
            return False

        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        """
        if not self.is_available:
            return 0

        try:
            keys = self._client.keys(pattern)
            if keys:
                count = self._client.delete(*keys)
                logger.info(f"Cache invalidated {count} keys matching: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            return 0

    # ==================== Specialized Cache Methods ====================

    def get_research_cache(self, query: str) -> str | None:
        key = self._generate_key(CACHE_PREFIX_RESEARCH, query.lower().strip())
        return self.get(key)

    def set_research_cache(self, query: str, research_data: str):
        key = self._generate_key(CACHE_PREFIX_RESEARCH, query.lower().strip())
        self.set(key, research_data)

    def get_vector_cache(self, query: str) -> str | None:
        key = self._generate_key(CACHE_PREFIX_VECTOR, query.lower().strip())
        return self.get(key)

    def set_vector_cache(self, query: str, results: str):
        key = self._generate_key(CACHE_PREFIX_VECTOR, query.lower().strip())
        self.set(key, results)

    def get_embeddings_cache(self, text: str) -> list | None:
        key = self._generate_key(CACHE_PREFIX_EMBEDDINGS, text)
        return self.get(key)

    def set_embeddings_cache(self, text: str, embeddings: list):
        key = self._generate_key(CACHE_PREFIX_EMBEDDINGS, text)
        self.set(key, embeddings)

    def get_response_cache(self, message_hash: str) -> dict | None:
        key = f"{CACHE_PREFIX_RESPONSE}{message_hash}"
        return self.get(key)

    def set_response_cache(self, message_hash: str, response: dict):
        key = f"{CACHE_PREFIX_RESPONSE}{message_hash}"
        self.set(key, response)

    # ==================== Cache Invalidation ====================

    def invalidate_research(self):
        self.invalidate_pattern(f"{CACHE_PREFIX_RESEARCH}*")

    def invalidate_vector(self):
        self.invalidate_pattern(f"{CACHE_PREFIX_VECTOR}*")

    def invalidate_all(self) -> int:
        total = 0
        for prefix in [
            CACHE_PREFIX_RESEARCH,
            CACHE_PREFIX_VECTOR,
            CACHE_PREFIX_RESPONSE,
            CACHE_PREFIX_EMBEDDINGS,
        ]:
            total += self.invalidate_pattern(f"{prefix}*")
        return total

    def on_knowledge_base_update(self):
        """Invalidate research and vector caches as they depend on KB state."""
        logger.info("Knowledge base changed. Invalidating research and vector caches.")
        self.invalidate_research()
        self.invalidate_vector()


# Singleton instance
cache_service = CacheService()
