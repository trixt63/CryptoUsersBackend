from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic_ext import openapi, validate

from app.apis._olds.portfolio.utils.utils import get_chains, check_address
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.entity.project import OverviewQuery
from app.utils.random_utils import generate_random_number, generate_random_string

bp = Blueprint('dex_pair_blueprint', url_prefix='/lp-pair')


@bp.get('/<project_id>/<pair_address>/introduction')
@openapi.tag("Dex Pair")
@openapi.summary("Get project overview")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@openapi.parameter(name="pair_address", description="Liquidation Pair address", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, project_id, pair_address, query: OverviewQuery):
    chain_id = query.chain
    # chains = get_chains(chain_id)
    # db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    pair_info = {
      "projectId": f"{project_id}",
      "projectName": "PancakeSwap",
      "deployer": "0xfca08fd2057a995cd270f22076c902b5cd2b4237",
      "imgUrl": "https://s2.coinmarketcap.com/static/img/exchanges/64x64/270.png",
      "token0": "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82",
      "token1": "0xe9e7cea3dedca5984780bafc599bd69add087d56",
      "pairName": f"{'Cake'}-{'BUSD'}",
    }

    return json(pair_info)


@bp.get('/<project_id>/<pair_address>/stats')
@openapi.tag("Dex Pair")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, pair_address, query: OverviewQuery):
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
