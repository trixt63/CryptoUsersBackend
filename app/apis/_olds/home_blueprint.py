from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic_ext import openapi

from app.constants.arangodb_graph_constants import ArangoDBGraphConstant
from app.constants.network_constants import EMPTY_TOKEN_IMG, Chain
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.services.artifacts.protocols import protocols, ProjectCollectorTypes

home_bp = Blueprint('statistics_blueprint', url_prefix='/')


@home_bp.get('/intro')
@openapi.tag("Homepage")
@openapi.summary("Get list projects and dapps introduction.")
async def get_introduction(request: Request):
    types = {
        'defi': 'project',
        'nfts': 'project',
        'tokens': 'token',
        'spots': 'project',
        'derivatives': 'project'
    }
    number_of_docs = 10

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    projection = ['id', 'name', 'imgUrl']
    dapps = db.get_projects_by_type(ProjectCollectorTypes.defillama, sort_by='tvl', reverse=True, limit=number_of_docs, projection=projection)
    nfts = db.get_projects_by_type(ProjectCollectorTypes.nft, sort_by='volume', reverse=True, limit=number_of_docs, projection=projection)
    spot_exchanges = db.get_projects_by_type(ProjectCollectorTypes.spot_exchange, sort_by='spotVolume', reverse=True, limit=number_of_docs, projection=projection)
    derivative_exchanges = db.get_projects_by_type(ProjectCollectorTypes.derivative_exchange, sort_by='derivativeVolume', reverse=True, limit=number_of_docs, projection=projection)

    data = {
        'defi': dapps,
        'nfts': nfts,
        'spots': spot_exchanges,
        'derivatives': derivative_exchanges
    }
    for ranking_type, docs in data.items():
        entity_type = types[ranking_type]
        entities = []
        for doc in docs:
            entities.append({
                'id': doc['id'],
                'type': entity_type,
                'name': doc['name'],
                'imgUrl': doc.get('imgUrl') or EMPTY_TOKEN_IMG
            })
        data[ranking_type] = entities

    tokens = db.get_contracts_by_type('token', sort_by='tokenHealth', reverse=True, limit=10 * number_of_docs, projection=['idCoingecko', 'name', 'imgUrl'])
    distinct_tokens = {}
    for token in tokens:
        coin_id = token['idCoingecko']
        if coin_id not in distinct_tokens:
            distinct_tokens[coin_id] = token

    data['tokens'] = []
    for coin_id, token in distinct_tokens.items():
        data['tokens'].append({
            'id': coin_id,
            'type': 'token',
            'name': token['name'],
            'imgUrl': token.get('imgUrl') or EMPTY_TOKEN_IMG
        })
        if len(data['tokens']) >= number_of_docs:
            break

    return json(data)


@home_bp.get('/statistic')
@openapi.tag("Homepage")
@openapi.summary("Get number of entities.")
async def get_statistics(request: Request):
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    number_of_dapps = db.count_documents_of_collection(ArangoDBGraphConstant.PROJECTS)
    number_of_contracts = db.count_documents_of_collection(ArangoDBGraphConstant.SMART_CONTRACTS)

    number_of_protocols = len(protocols)  # Hardcode
    number_of_networks = len(Chain().get_all_chain_id())
    return json({
        'numberOfDApps': number_of_dapps,
        'numberOfContracts': number_of_contracts,
        'numberOfProtocols': number_of_protocols,
        'numberOfNetworks': number_of_networks
    })
