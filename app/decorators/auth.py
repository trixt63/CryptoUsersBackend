from functools import wraps
import jwt
from sanic.exceptions import Unauthorized, Forbidden


def check_token(request, token, address='0x'):
    if not token:
        raise Unauthorized('JWT required')

    try:
        jwt_ = jwt.decode(
            token, request.app.config.SECRET, algorithms=["HS256"]
        )

        if jwt_["role"] == 'admin':
            return

        if address.lower() != jwt_["address"]:
            raise Forbidden('Permission denied')
    except jwt.exceptions.InvalidTokenError:
        raise Unauthorized('Invalid JWT')


def protected(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            token = request.token
            check_token(request, token, kwargs.get('address', '0x'))

            response = await f(request, *args, **kwargs)
            return response

        return decorated_function

    return decorator(wrapped)
 