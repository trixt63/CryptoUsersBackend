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

bp = Blueprint('cex_blueprint', url_prefix='/cex')


@bp.get('/<project_id>/introduction')
@openapi.tag("Project")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @openapi.parameter(name="type", description=f"Type of project. Allowable values: defi, nft, exchange", required=True, location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_overview(request: Request, project_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)
    # project_type, type_ = get_project_type(query.type)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    # project = get_project(db, project_id, chains, type_, project_type)
    project = {
      "id": f"{project_id}",
      "projectId": f"{project_id}",
      "name": "Binance",
      "imgUrl": "https://s2.coinmarketcap.com/static/img/exchanges/64x64/270.png",
      "chains": [
        "0x1",
        "0x38"
      ],
      "projectType": "exchange",
      "url": "https://www.binance.com/",
      "socialNetworks": {
        "telegram": "https://t.me/binanceexchange",
        "twitter": "https://twitter.com/binance"
      }
    }

    return json(project)


@bp.get('/<project_id>/stats')
@openapi.tag("Project")
@openapi.summary("Get project introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @openapi.parameter(name="type", description=f"Type of project. Allowable values: dex, lending, nft, exchange",
#                    required=True, location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_stats(request: Request, project_id, query: OverviewQuery):
    stats = {
      "id": f"{project_id}",
      "volume": 95915987738.03323,
      "volumeChangeRate": 1.284184833196924,
      "numberOfMarkets": 1959,
      "numberOfCoins": 386
    }

    return json(stats)


@bp.get('/<project_id>/whales-list')
@openapi.tag("Project")
@openapi.summary("Get project overview")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="project_id", description="Project ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_whales(request: Request, project_id, query: OverviewQuery):
    whales = [{
        'id': '0xf977814e90da44bfa03b6295a0616a897441acec',
        'address': '0xf977814e90da44bfa03b6295a0616a897441acec',
        'estimatedBalance': 75034499.975,
        # 'ownedBy': '0x1111111111111111111111111111111111111111',
        'socialNetworks': {
            'telegram': 'https://t.me/binanceexchange',
            'twitter': 'https://twitter.com/binance'}
    }] * 100

    return json(whales)


# ---------Helper functions---------
def get_project_type(type_):
    allowable = {
        ProjectTypes.defi: ProjectCollectorTypes.defillama,
        ProjectTypes.nft: ProjectCollectorTypes.nft,
        ProjectTypes.exchange: ProjectCollectorTypes.spot_exchange
    }
    if (not type_) or (type_.lower() not in allowable):
        raise BadRequest(f'Invalid project type {type_}')

    type_ = type_.lower()
    return type_, allowable[type_]


def get_project(db: Union[MongoDB, KLGDatabase], project_id, chains, type_, project_type):
    project = db.get_project(project_id)
    if not project or not filter(lambda x: x in project.get('deployedChains', []), chains):
        raise NotFound(f'Project with id {project_id}')

    if type_ not in project.get('sources', []):
        raise NotFound(f'Project {project_id} with type {project_type}')

    return project


def get_info_to_project_obj(
        db: Union[MongoDB, KLGDatabase],
        project: dict, project_type: str, contract_information=True
) -> Project:
    if contract_information:
        contract_keys = list(project.get('contractAddresses', {}).keys())
        contracts_cursor = db.get_contracts_by_keys(keys=contract_keys)
        project['contracts'] = {f"{t['chainId']}_{t['address']}": t for t in contracts_cursor}

    token_keys = [
        f'{chain_id}_{token_address}' for chain_id, token_address in project.get('tokenAddresses', {}).items()
    ]
    token_keys.extend(list(project.get('supportedTokenAddresses', {}).keys()))
    tokens_cursor = db.get_contracts_by_keys(keys=list(set(token_keys)))
    project['tokens'] = {f"{t['chainId']}_{t['address']}": t for t in tokens_cursor}

    project_cls = project_cls_mapping[project_type]
    project_obj: Project = project_cls.from_dict(project, project_type)
    return project_obj
