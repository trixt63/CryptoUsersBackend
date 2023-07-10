from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound
from sanic_ext import openapi

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
            'numberOfUsers': community_db.count_users_by_category('Cexes'),
            'numberOfRealUsers': 0
        },
        "DEX": {
            'numberOfApplications': community_db.count_projects_by_category('Dexes'),
            'numberOfUsers': community_db.count_users_by_category('Dexes'),
            'numberOfRealUsers': 0
        },
        "Lendings": {
            'numberOfApplications': community_db.count_projects_by_category('Lending'),
            'numberOfUsers': community_db.count_users_by_category('Lending'),
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
    community_db: MongoDBCommunity = request.app.ctx.community_db
    data = list(community_db.get_applications(category="Cexes",
                                              sort_by="spotVolume"))
    for datum in data:
        datum['id'] = datum['_id']
        datum['category'] = 'CEX'
        datum['numberOfUsers'] = 0
        datum['numberOfRealUsers'] = 0
    return json({
        'numberOfDocs': len(data),
        'docs': data
    })


@bp.get('/dexes')
@openapi.tag("Homepage")
@openapi.summary("Get top Dexes applications")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @validate(query=OverviewQuery)
async def get_types_info(request: Request):
    community_db: MongoDBCommunity = request.app.ctx.community_db
    data = list(community_db.get_applications(category="Dexes",
                                              sort_by="tvl"))
    for datum in data:
        datum['id'] = datum['_id']
        datum['category'] = 'DEX'
        datum['numberOfUsers'] = 0
        datum['numberOfRealUsers'] = 0
    return json({
        'numberOfDocs': len(data),
        'docs': data
    })

@bp.get('/lendings')
@openapi.tag("Homepage")
@openapi.summary("Get top Lendings applications")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
# @validate(query=OverviewQuery)
async def get_types_info(request: Request):
    community_db: MongoDBCommunity = request.app.ctx.community_db
    data = list(community_db.get_applications(category="Lending",
                                              sort_by="tvl"))
    for datum in data:
        datum['id'] = datum['_id']
        datum['category'] = 'Lending'
        datum['numberOfUsers'] = 0
        datum['numberOfRealUsers'] = 0
    return json({
        'numberOfDocs': len(data),
        'docs': data
    })
