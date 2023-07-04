from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound, BadRequest
from sanic_ext import openapi, validate

from app.apis._olds.portfolio.utils.utils import get_chains
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.entity.project import OverviewQuery
from app.models.entity.projects import project_cls_mapping
from app.models.entity.projects.project import ProjectTypes, Project
from app.models.explorer.visualization import Visualization
from app.services.artifacts.protocols import ProjectCollectorTypes

bp = Blueprint('dex_blueprint', url_prefix='/dex')


@bp.get('/<project_id>/introduction')
@openapi.tag("Project")
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
      "name": "PancakeSwap",
      "imgUrl": "https://s2.coinmarketcap.com/static/img/exchanges/64x64/270.png",
      "chains": [
        "0x1",
        "0x38"
      ],
      "url": "https://pancakeswap.finance/",
      "socialNetworks": {
        "telegram": "https://t.me/PancakeSwap",
        "twitter": "https://twitter.com/pancakeswap"
      }
    }

    return json(project)


@bp.get('/<project_id>/stats')
@openapi.tag("Project")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, query: OverviewQuery):
    stats = {
      "id": f"{project_id}",
      "tvl": 95915987738.03323,
      "traders": 1.284184833196924,
      "realTraders": 1959,
      "providers": 0,
      "realProviders": 0
    }

    return json(stats)


@bp.get('/<project_id>/top-pairs')
@openapi.tag("Project")
@openapi.summary("Get project top pairs")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_top_pairs(request: Request, project_id, query: OverviewQuery):
    pairs = [{
        'id': '0x804678fa97d91b974ec2af3c843270886528a9e6',
        'name': 'Cake-BUSD',
        'address': '0x804678fa97d91b974ec2af3c843270886528a9e6',
        'tvl': 0,
        'reserveInUSD': 945961.7950825647,
        'deployedBy': '0xfca08fd2057a995cd270f22076c902b5cd2b4237',
    }] * 10

    return json(pairs)
