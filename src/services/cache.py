"""Redis caching service for high-speed URL redirection."""

import redis.asyncio as aioredis

from src.config import get_settings

settings = get_settings()


class CacheService:
    """Manages Redis cache-aside operations for short links."""

    def __init__(self, redis_url: str = settings.REDIS_URL) -> None:
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
        """Fetches target destination URL from Redis cache."""
        try:
            if not self.client:
                await self.connect()
            if self.client:
                val = await self.client.get(f"shortlink:code:{short_code}")
                if isinstance(val, bytes):
                    return val.decode("utf-8")
                if isinstance(val, str):
                    return val
                return None
        except (aioredis.RedisError, OSError):
            return None
        return None

    async def set_url(
        self,
        short_code: str,
        target_url: str,
        ttl_seconds: int = settings.REDIS_TTL_SECONDS,
    ) -> None:
        """Stores a short code to target URL mapping in Redis with TTL."""
        try:
            if not self.client:
                await self.connect()
            if self.client:
                await self.client.set(
                    f"shortlink:code:{short_code}",
                    target_url,
                    ex=ttl_seconds,
                )
        except (aioredis.RedisError, OSError):
            pass

    async def invalidate(self, short_code: str) -> None:
        """Removes a short code from Redis cache upon deletion or expiration."""
        if self.client:
            await self.client.delete(f"shortlink:code:{short_code}")


# Singleton instance
cache_service = CacheService()
