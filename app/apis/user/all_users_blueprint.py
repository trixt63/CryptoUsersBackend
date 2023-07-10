from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound
from sanic_ext import openapi

from app.constants.network_constants import EMPTY_TOKEN_IMG, Chain
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.mongodb.mongodb_community import MongoDBCommunity
from app.services.artifacts.protocols import protocols, ProjectCollectorTypes
from app.utils.random_utils import generate_random_string, generate_random_number

bp = Blueprint('user_overview_blueprint', url_prefix='/overview')


@bp.get('/stats')
@openapi.tag("user")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @validate(query=OverviewQuery)
async def get_intro(request: Request):
    returned_data = {
        "users": generate_random_number(100, 1000),
        "wallets": generate_random_number(100, 1000)
    }
    return json(returned_data)


@bp.get('/top-users')
@openapi.tag("Overview statistic of a user")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @validate(query=OverviewQuery)
async def get_intro(request: Request):
    returned_data = [
        dict(
            wallets=f"0x{generate_random_string(40)}",
            totalBalance=generate_random_number(1000, 100000),
            socialAccounts={
                'twitter': f'twitter.com/{generate_random_string(7)}',
                'discord': f'discord.com/{generate_random_string(7)}'
            }
        )
        for i in range(100)
    ]

    return json(returned_data)
