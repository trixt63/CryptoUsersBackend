from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound, BadRequest
from sanic_ext import openapi, validate

from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.mongodb.mongodb_community import MongoDBCommunity
from app.models.entity.project import OverviewQuery

bp = Blueprint('dex_blueprint', url_prefix='/dex')


@bp.get('/<project_id>/introduction')
@openapi.tag("Dex")
@openapi.summary("Get project overview")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: pancakeswap", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    data = get_project(db, project_id, chains=[chain_id])

    project_socials = data.get('socialAccounts', {})
    project_url = None
    if project_socials:
        project_url = project_socials.pop('website')

    project = {
      "id": f"{project_id}",
      "projectId": f"{project_id}",
      "name": data["name"],
      "imgUrl": data["imgUrl"],
      "url": project_url,
      "socialNetworks": project_socials,
      "chains": data.get('deployedChains', []),
    }

    return json(project)

@bp.get('/<project_id>/stats')
@openapi.tag("Dex")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID, eg: 0x38", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: pancakeswap", location="path", required=True)
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
        "traders": users_data["traders"],
        "deployers": users_data["deployers"]
    }
    return json(stats)


@bp.get('/<project_id>/top-pairs')
@openapi.tag("Dex")
@openapi.summary("Get project top pairs")
@openapi.parameter(name="chain", description=f"Chain ID, eg: 0x38", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: pancakeswap", location="path", required=True)
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


@bp.get('/<project_id>/top-traders')
@openapi.tag("Dex")
@openapi.summary("Get project overview")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: pancakeswap", location="path", required=True)
@validate(query=OverviewQuery)
async def get_top_traders(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain
    if not chain_id:
        dex_chain_mappers = {'pancakeswap': '0x38', 'spookyswap': '0xfa', 'uniswap-v2': '0x1'}
        chain_id = dex_chain_mappers[project_id]

    community_db: MongoDBCommunity = request.app.ctx.community_db

    wallets_data = community_db.get_sample_traders_wallets(project_id=project_id,
                                                           chain_id=chain_id)

    returned_data = [
        {
            'id': project_id,
            'address': datum['address'],
        }
        for datum in wallets_data
    ]

    return json(returned_data)


def get_project(db: Union[MongoDB, KLGDatabase], project_id, chains=[]):
    project = db.get_project(project_id)
    if not project or not filter(lambda x: x in project.get('deployedChains', []), chains):
        raise NotFound(f'Project with id {project_id}')
    return project
