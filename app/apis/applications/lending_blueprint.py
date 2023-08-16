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

bp = Blueprint('lending_blueprint', url_prefix='/lending')


@bp.get('/<project_id>/introduction')
@openapi.tag("Lending")
@openapi.summary("Get project overview")
@openapi.parameter(name="chain", description=f"Chain ID, eg: 0x38", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: compound", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain
    # chains = get_chains(chain_id)
    # project_type, type_ = get_project_type(query.type)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    project = get_project(db, project_id, chains=[chain_id])

    project_url = project['socialAccounts'].pop('website')

    project = {
      "id": f"{project_id}",
      "projectId": f"{project_id}",
      "name": project["name"],
      "imgUrl": project["imgUrl"],
      "chains": project["deployedChains"],
      "url": project_url,
      "socialNetworks": project["socialAccounts"],
    }

    return json(project)


@bp.get('/<project_id>/stats')
@openapi.tag("Lending")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID, eg: 0x38", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: compound", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, query: OverviewQuery):
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    community_db: MongoDBCommunity = request.app.ctx.community_db

    chain_id = query.chain or '0x38'

    app_data = get_project(db, project_id, chains=[chain_id])
    users_data = community_db.get_project_users(chain_id, project_id)
    if not app_data or not users_data:
        raise NotFound(f'Project with id {project_id}')

    stats = {
      "id": project_id,
      "volume": app_data['tvl'],
      "users": users_data,
    }

    return json(stats)


@bp.get('/<project_id>/top-wallets')
@openapi.tag("Lending")
@openapi.summary("Get project top pairs")
@openapi.parameter(name="chain", description=f"Chain ID, eg: 0x38", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: compound", location="path", required=True)
@validate(query=OverviewQuery)
async def get_top_wallets(request: Request, project_id, query: OverviewQuery):
    community_db: MongoDBCommunity = request.app.ctx.community_db
    chain_id = query.chain or '0x38'

    data = community_db.get_sample_lending_wallets(chain_id, project_id)

    wallets = [{
        'id': datum['_id'],
        'address': datum['address'],
        'numberOfRelatedWallets': 0,
        'deposited': 0,
        'borrowed': 0,
    } for datum in data]

    return json(wallets)


def get_project(db: Union[MongoDB, KLGDatabase], project_id, chains=[]):
    project = db.get_project(project_id)
    if not project or not filter(lambda x: x in project.get('deployedChains', []), chains):
        raise NotFound(f'Project with id {project_id}')
    return project
