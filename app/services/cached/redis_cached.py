import json

from redis import Redis

from app.decorators.time_exe import sync_log_time_exe, TimeExeTag


class RedisCached:
    @classmethod
    @sync_log_time_exe(tag=TimeExeTag.cache)
    def get_cache(cls, r: Redis, key):
        value = r.get(key)
        try:
            if value:
                value = json.loads(value)
        except json.JSONDecodeError:
            pass
        return value

    @classmethod
    @sync_log_time_exe(tag=TimeExeTag.cache)
    def set_cache(cls, r: Redis, key, value, ttl=300):
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value)
        r.set(key, value, ex=ttl)
