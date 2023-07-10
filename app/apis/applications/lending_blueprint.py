from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound, BadRequest
from sanic_ext import openapi, validate

from app.apis._olds.portfolio.utils.utils import get_chains
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.entity.project import OverviewQuery

bp = Blueprint('lending_blueprint', url_prefix='/lending')


@bp.get('/<project_id>/introduction')
@openapi.tag("Lending")
@openapi.summary("Get project overview")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)
    # project_type, type_ = get_project_type(query.type)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    # project = get_project(db, project_id, chains, type_, project_type)
    project = {
      "id": f"{project_id}",
      "projectId": f"{project_id}",
      "name": "AAVE V2",
      "imgUrl": "https://icons.llama.fi/aave-v2.png",
      "chains": [
        "0x1",
        "0x38"
      ],
      "url": "https://pancakeswap.finance/",
      "socialNetworks": {
        "github": "https://github.com/aave",
        "reddit": "https://www.reddit.com/r/Aave_Official",
        "twitter": "https://twitter.com/AaveAave",
      }
    }

    return json(project)


@bp.get('/<project_id>/stats')
@openapi.tag("Lending")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, query: OverviewQuery):
    stats = {
        "id": f"{project_id}",
        "tvl": 0,
        "users": 0,
        "totalDeposited": 0,
        "totalBorrowed": 0
    }

    return json(stats)


@bp.get('/<project_id>/top-wallets')
@openapi.tag("Lending")
@openapi.summary("Get project top pairs")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_top_wallets(request: Request, project_id, query: OverviewQuery):
    pairs = [{
        'id': '0x804678fa97d91b974ec2af3c843270886528a9e6',
        'address': '0x804678fa97d91b974ec2af3c843270886528a9e6',
        'numberOfRelatedWallets': 0,
        'deposited': 0,
        'borrowed': 0,
    }] * 10

    return json(pairs)
