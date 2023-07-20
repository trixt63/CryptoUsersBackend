from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound, BadRequest
from sanic_ext import openapi, validate

# from app.apis._olds.portfolio.utils.utils import get_chains
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.mongodb.mongodb_community import MongoDBCommunity
from app.models.entity.project import OverviewQuery

bp = Blueprint('dex_blueprint', url_prefix='/dex')


@bp.get('/<project_id>/introduction')
@openapi.tag("Dex")
@openapi.summary("Get project overview")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain
    # chains = get_chains(chain_id)
    # project_type, type_ = get_project_type(query.type)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    project = get_project(db, project_id=project_id)
    # project = get_project(db, project_id, chains, type_, project_type)
    project_url = project["socialAccounts"].pop('website')
    project = {
      "id": f"{project_id}",
      "projectId": f"{project_id}",
      "name": project["name"],
      "imgUrl": project["imgUrl"],
      "chains": project["deployedChains"],
      "url": project_url,
      "socialNetworks": project["socialAccounts"],
    }

    return json(dict(project))


@bp.get('/<project_id>/stats')
@openapi.tag("Dex")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    community_db: MongoDBCommunity = request.app.ctx.community_db

    project = get_project(db, project_id)
    users_data = community_db.get_project_users(chain_id, project_id)
    if not project or not users_data:
        raise NotFound(f'Project with id {project_id}')

    stats = {
      "id": f"{project_id}",
      "tvl": project['tvl'],
      "traders": users_data,
      "realTraders": 0,
      "providers": 0,
      "realProviders": 0
    }
    return json(stats)


@bp.get('/<project_id>/top-pairs')
@openapi.tag("Dex")
@openapi.summary("Get project top pairs")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_top_pairs(request: Request, project_id, query: OverviewQuery):
    # db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    community_db: MongoDBCommunity = request.app.ctx.community_db
    data = community_db.get_top_pairs(project_id, limit=100)

    returned_data = [
        {
            'id': datum['_id'],
            'address': datum['address'],
            'chainId': datum['chainId'],
            'reserveInUSD': datum['pairBalancesInUSD']['token0'] + datum['pairBalancesInUSD']['token1'],
            'token0': datum['token0'],
            'token1': datum['token1']
        }
        for datum in data
    ]

    return json(returned_data)


def get_project(db: Union[MongoDB, KLGDatabase], project_id, chains=[]):
    project = db.get_project(project_id)
    if not project or not filter(lambda x: x in project.get('deployedChains', []), chains):
        raise NotFound(f'Project with id {project_id}')
    return project
