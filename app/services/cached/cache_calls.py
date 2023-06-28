import time

from redis import Redis

from app.constants.time_constants import TimeConstants
from app.services.cached.redis_cached import RedisCached
from app.utils.logger_utils import get_logger

logger = get_logger('Cache Calls')


class CacheCalls(RedisCached):
    """Limit 50 calls per minute. """

    @classmethod
    def get_on_minute_calls(cls, r: Redis, ip):
        ts = int(time.time() / TimeConstants.A_MINUTE) * TimeConstants.A_MINUTE
        calls = r.get(f'{ip}.{ts}') or 0
        return int(calls)

    @classmethod
    def call(cls, r: Redis, ip):
        ts = int(time.time() / TimeConstants.A_MINUTE) * TimeConstants.A_MINUTE
        calls = r.incr(f'{ip}.{ts}')
        if calls == 1:
            r.expire(f'{ip}.{ts}', TimeConstants.A_MINUTE)

