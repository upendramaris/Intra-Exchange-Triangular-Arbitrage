from typing import Any, Dict

import redis.asyncio as redis

from triarb.config import get_settings


class RedisState:
    def __init__(self):
        self.settings = get_settings()
        self.client = redis.from_url(self.settings.redis_url, decode_responses=True)

    async def set_json(self, key: str, value: Dict[str, Any]) -> None:
        import json

        await self.client.set(key, json.dumps(value))

    async def close(self) -> None:
        if isinstance(self.client, redis.Redis):
            await self.client.close()
