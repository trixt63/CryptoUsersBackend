from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound
from sanic_ext import openapi, validate

from app.constants.network_constants import EMPTY_TOKEN_IMG, Chain
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.mongodb.mongodb_community import MongoDBCommunity
from app.services.artifacts.protocols import protocols, ProjectCollectorTypes

bp = Blueprint('homepage_blueprint', url_prefix='/')


@bp.get('/intro')
@openapi.tag("Homepage")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @validate(query=OverviewQuery)
async def get_types_info(request: Request):
    community_db: MongoDBCommunity = request.app.ctx.community_db

    returned_dict = {
        "CEX": {
            'numberOfApplications': community_db.count_projects_by_category('Cexes'),
            'numberOfUsers': community_db.count_cex_users(),
            'numberOfRealUsers': 0
        },
        "DEX": {
            'numberOfApplications': community_db.count_projects_by_category('Dexes'),
            'numberOfUsers': community_db.count_dex_users(),
            'numberOfRealUsers': 0
        },
        "Lendings": {
            'numberOfApplications': community_db.count_projects_by_category('Lending'),
            'numberOfUsers': community_db.count_lending_users(),
            'numberOfRealUsers': 0
        },
    }

    return json(returned_dict)


@bp.get('/cexes')
@openapi.tag("Homepage")
@openapi.summary("Get top CEX applications")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @validate(query=OverviewQuery)
async def get_types_info(request: Request):
    app = {
      "_id": "acsi-finance",
      "idDApp": "acsi-finance",
      "imgUrl": "https://dappimg.com/media/image/dapp/62fdd6e6b7684393884f29a5addbec3b.blob",
      "name": "ACSI Finance",
      "category": "exchange",
      "deployedChains": [
        "0x38"
      ],
      "numberOfUsers": 45,
      "numberOfRealUsers": 45,
      "numberOfTransactions": 409,
      "transactionVolume": 316220,
      # "socialSignal": 255,
      "sources": [
        "dapp"
      ],
      "id": "acsi-finance"
    }

    returned_data = [app] * 10

    return json(returned_data)


@bp.get('/defies')
@openapi.tag("Homepage")
@openapi.summary("Get top DeFis applications")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @validate(query=OverviewQuery)
async def get_types_info(request: Request):
    app = {
      "_id": "acsi-finance",
      "idDApp": "acsi-finance",
      "imgUrl": "https://dappimg.com/media/image/dapp/62fdd6e6b7684393884f29a5addbec3b.blob",
      "name": "ACSI Finance",
      "category": "exchange",
      "deployedChains": [
        "0x38"
      ],
      "numberOfUsers": 45,
      "numberOfRealUsers": 45,
      "numberOfTransactions": 409,
      "transactionVolume": 316220,
      # "socialSignal": 255,
      "sources": [
        "dapp"
      ],
      "id": "acsi-finance"
    }

    returned_data = [app] * 10

    return json(returned_data)
