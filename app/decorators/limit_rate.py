from functools import wraps

from sanic import Request
from sanic.exceptions import SanicException
from redis import Redis

from app.services.cached.cache_calls import CacheCalls

LIMIT_CALLS_PER_MINUTE = 50


def limit_rate(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            ip = request.ip
            r: Redis = request.app.ctx.redis
            calls = CacheCalls.get_on_minute_calls(r, ip)
            if calls > LIMIT_CALLS_PER_MINUTE:
                raise TooManyRequests('Exceeds rate 50 requests/minute.')

            response = await f(request, *args, **kwargs)

            CacheCalls.call(r, ip)
            return response

        return decorated_function

    return decorator(wrapped)


class TooManyRequests(SanicException):
    """
    **Status**: 429 Too Many Requests
    """

    status_code = 429
    quiet = True
