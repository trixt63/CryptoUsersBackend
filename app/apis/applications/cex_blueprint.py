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

bp = Blueprint('cex_blueprint', url_prefix='/cex')


@bp.get('/<project_id>/introduction')
@openapi.tag("Cex")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @openapi.parameter(name="type", description=f"Type of project. Allowable values: defi, nft, exchange", required=True, location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: binance", location="path", required=True)
@validate(query=OverviewQuery)
async def get_overview(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain
    # chains = get_chains(chain_id)
    # project_type, type_ = get_project_type(query.type)

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
@openapi.tag("Cex")
@openapi.summary("Get project introduction. Eg: binance")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @openapi.parameter(name="type", description=f"Type of project. Allowable values: dex, lending, nft, exchange",
#                    required=True, location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: binance", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, query: OverviewQuery):
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    community_db: MongoDBCommunity = request.app.ctx.community_db

    chain_id = query.chain or '0x38'
    # chains = get_chains(chain_id)

    app_data = get_project(db, project_id, chains=[chain_id])
    users_data = community_db.get_project_users(chain_id, project_id)
    if not app_data or not users_data:
        raise NotFound(f'Project with id {project_id}')

    stats = {
      "id": project_id,
      "volume": app_data['spotVolume'],
      "users": users_data,
    }

    return json(stats)


@bp.get('/<project_id>/whales-list')
@openapi.tag("Cex")
@openapi.summary("Get project overview. Eg: binance")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID, eg: binance", location="path", required=True)
@validate(query=OverviewQuery)
async def get_whales(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain or '0x38'
    community_db: MongoDBCommunity = request.app.ctx.community_db
    groups = list(community_db.get_whales_list(project_id, chain_id=chain_id))

    returned_data = [
        {
            'id': project_id,
            'userWallets': group['user_wallets'],
            'depositWallets': group['deposit_wallets'],
        }
        for group in groups
    ]

    return json(returned_data)


def get_project(db: Union[MongoDB, KLGDatabase], project_id, chains):
    project = db.get_project(project_id)
    if not project or not filter(lambda x: x in project.get('deployedChains', []), chains):
        raise NotFound(f'Project with id {project_id}')
    return project


# ---------Helper functions---------
# def get_project_type(type_):
#     allowable = {
#         ProjectTypes.defi: ProjectCollectorTypes.defillama,
#         ProjectTypes.nft: ProjectCollectorTypes.nft,
#         ProjectTypes.exchange: ProjectCollectorTypes.spot_exchange
#     }
#     if (not type_) or (type_.lower() not in allowable):
#         raise BadRequest(f'Invalid project type {type_}')
#
#     type_ = type_.lower()
#     return type_, allowable[type_]
#
#
# def get_project(db: Union[MongoDB, KLGDatabase], project_id, chains, type_, project_type):
#     project = db.get_project(project_id)
#     if not project or not filter(lambda x: x in project.get('deployedChains', []), chains):
#         raise NotFound(f'Project with id {project_id}')
#
#     if type_ not in project.get('sources', []):
#         raise NotFound(f'Project {project_id} with type {project_type}')
#
#     return project
#
#
# def get_info_to_project_obj(
#         db: Union[MongoDB, KLGDatabase],
#         project: dict, project_type: str, contract_information=True
# ) -> Project:
#     if contract_information:
#         contract_keys = list(project.get('contractAddresses', {}).keys())
#         contracts_cursor = db.get_contracts_by_keys(keys=contract_keys)
#         project['contracts'] = {f"{t['chainId']}_{t['address']}": t for t in contracts_cursor}
#
#     token_keys = [
#         f'{chain_id}_{token_address}' for chain_id, token_address in project.get('tokenAddresses', {}).items()
#     ]
#     token_keys.extend(list(project.get('supportedTokenAddresses', {}).keys()))
#     tokens_cursor = db.get_contracts_by_keys(keys=list(set(token_keys)))
#     project['tokens'] = {f"{t['chainId']}_{t['address']}": t for t in tokens_cursor}
#
#     project_cls = project_cls_mapping[project_type]
#     project_obj: Project = project_cls.from_dict(project, project_type)
#     return project_obj
