"""Redis caching service for high-speed URL redirection."""

import redis.asyncio as aioredis

from src.config import get_settings

settings = get_settings()


class CacheService:
    """Manages Redis cache-aside operations for short links."""

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self.client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Initializes the async Redis connection pool."""
        if not self.client:
            self.client = aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )

    async def disconnect(self) -> None:
        """Closes the Redis connection pool."""
        if self.client:
            await self.client.close()

    async def get_url(self, short_code: str) -> str | None:
        """Fetches target destination URL from Redis cache.

        Args:
            short_code: The alphanumeric short code (e.g. 'wCg').

        Returns:
            The cached original URL string, or None on cache miss.

        TODO (Student):
            1. Ensure client is connected.
            2. Query key `f"shortlink:code:{short_code}"`.
            3. Return string value or None.
        """
        raise NotImplementedError("TODO: Implement get_url cache lookup yourself!")

    async def set_url(
        self,
        short_code: str,
        target_url: str,
        ttl_seconds: int = settings.REDIS_TTL_SECONDS,
    ) -> None:
        """Stores a short code to target URL mapping in Redis with TTL.

        Args:
            short_code: The alphanumeric short code.
            target_url: Destination URL.
            ttl_seconds: Cache expiration in seconds (default: 24h).

        TODO (Student):
            1. Ensure client is connected.
            2. Set key `f"shortlink:code:{short_code}"` with ex=ttl_seconds.
        """
        raise NotImplementedError("TODO: Implement set_url cache persistence yourself!")

    async def invalidate(self, short_code: str) -> None:
        """Removes a short code from Redis cache upon deletion or expiration."""
        if self.client:
            await self.client.delete(f"shortlink:code:{short_code}")


# Singleton instance
cache_service = CacheService()
