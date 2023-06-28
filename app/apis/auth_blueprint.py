import jwt
from sanic import Blueprint
from sanic.exceptions import BadRequest, Unauthorized
from sanic.response import json
from sanic_ext import openapi, validate

from app.constants.network_constants import ProviderURI
from app.models.auth import AuthQuery, AuthBody
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth_blueprint', url_prefix='/auth')

auth_service = AuthService(provider_uri=ProviderURI.bsc_provider_uri)


@auth_bp.post('/login')
@openapi.tag("Auth")
@openapi.summary("Login with metamask")
@openapi.body({'application/json': AuthBody})
@validate(json=AuthBody)
async def login_with_metamask(request, body: AuthBody):
    address = body.address.lower()
    signature = body.signature
    nonce = body.nonce

    administrators = []
    role = 'user'
    if address in administrators:
        role = 'admin'

    try:
        results = auth_service.login_with_metamask(
            address=address, signature=signature, nonce=nonce,
            role=role, secret_key=request.app.config.SECRET
        )
    except ValueError:
        raise BadRequest('Login Fail')

    return json({
        'jwt': results,
        'role': role
    })


@auth_bp.get('/check-user')
@openapi.tag("Auth")
@openapi.summary("Check user is admin or not")
@openapi.parameter(name='jwt', description='JWT', location='query', required=True)
@validate(query=AuthQuery)
async def check_user(request, query: AuthQuery):
    token = query.jwt
    try:
        jwt_ = jwt.decode(token, request.app.config.SECRET, algorithms=["HS256"])
    except jwt.exceptions.InvalidTokenError:
        raise Unauthorized(message="Signature verification failed")

    return json(jwt_)
