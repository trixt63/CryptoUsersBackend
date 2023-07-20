from typing import Union
from sanic import Blueprint, Request
from sanic import json
from sanic_ext import openapi, validate

# from app.apis._olds.portfolio.utils.utils import get_chains, check_address
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.mongodb.mongodb_community import MongoDBCommunity
from app.models.entity.project import OverviewQuery
from app.utils.random_utils import generate_random_number, generate_random_string

bp = Blueprint('dex_pair_blueprint', url_prefix='/lp-pair')


@bp.get('/<pair_address>/introduction')
@openapi.tag("Dex Pair")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="pair_address", description="Liquidation Pair address", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, pair_address, query: OverviewQuery):
    chain_id = query.chain
    # chains = get_chains(chain_id)
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    community_db: MongoDBCommunity = request.app.ctx.community_db

    # get data
    pair_data = community_db.get_dex_pair(chain_id=chain_id, address=pair_address)

    dex_id = pair_data['dex']
    project_data = db.get_project(dex_id)

    # get token name
    token0 = db.get_token(chain_id=chain_id, address=pair_data['token0'])
    token1 = db.get_token(chain_id=chain_id, address=pair_data['token1'])

    pair_info = {
      "projectId": f"{dex_id}",
      "projectName": project_data['name'],
      # "deployer": "0xfca08fd2057a995cd270f22076c902b5cd2b4237",
      "imgUrl": project_data['imgUrl'],
      # "token0": pair_data['token0'],
      # "token1": pair_data['token1'],
      "pairName": f"{token0['name']} / {token1['name']}",
    }

    return json(pair_info)


@bp.get('/<project_id>/<pair_address>/stats')
@openapi.tag("Dex Pair")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, pair_address, query: OverviewQuery):
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    stats = {
        "projectId": project_id,
        "id": pair_address,
        "traders": 0,
        "realTraders": 1959,
        "providers": 0,
        "realProviders": 0
    }

    return json(stats)


@bp.get('/<project_id>/<pair_address>/top-traders')
@openapi.tag("Dex Pair")
@openapi.summary("Get project top pairs")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_top_traders(request: Request, project_id, pair_address, query: OverviewQuery):
    wallets = [{
        'id': '0x804678fa97d91b974ec2af3c843270886528a9e6',
        'address': '0x804678fa97d91b974ec2af3c843270886528a9e6',
        'numberOfRelatedWallets': 0,
        # 'balance': 0,
        'socialAccounts': {
            'telegram': ['https://t.me/binanceexchange'],
            'twitter': ['https://twitter.com/binance']}
    }] * 10

    return json(wallets)
