import time
from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic_ext import openapi, validate

from app.constants.time_constants import TimeConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.ranking.rankings import TopDAppsQuery, TopNFTsQuery, TopTokensQuery, TopSpotExchangesQuery, \
    TopDerivativeExchangesQuery
from app.services.artifacts.protocols import ProjectCollectorTypes
from app.utils.list_dict_utils import sort_log, get_logs_change_rate
from app.utils.parser import parse_pagination

rankings_bp = Blueprint('rankings_blueprint', url_prefix='/')


@rankings_bp.get('/dapps')
@openapi.tag("Ranking")
@openapi.summary("Get the list of dapps")
@openapi.parameter(name="order", description="Sort direction: asc or desc. Default: desc", schema=str, location="query")
@openapi.parameter(name="orderBy", description="Sort by field. Default: tvl", schema=str, location="query")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 10", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="duration", description="Duration to return tvl change rate. Default: 24 hours.", schema=int, location="query")
@openapi.parameter(name="category", description="DApp category. If not set, return dapp of all categories.", schema=str, location="query")
@openapi.parameter(name="chain", description="Chain ID. If not set, return data in all chains.", schema=str, location="query")
@validate(query=TopDAppsQuery)
async def get_top_dapps(request: Request, query: TopDAppsQuery):
    chain_id = query.chain
    category = query.category

    keys = ['name', 'imgUrl', 'category', 'tvl']
    change = {'tvl': 'tvlChangeLogs'}

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    data = get_documents_with_query(
        db, query=query, project_type=ProjectCollectorTypes.defillama,
        keys=keys, chain_id=chain_id, category=category, change=change
    )
    return json(data)


@rankings_bp.get('/nfts')
@openapi.tag("Ranking")
@openapi.summary("Get the list of nfts")
@openapi.parameter(name="order", description="Sort direction: asc or desc. Default: desc", schema=str, location="query")
@openapi.parameter(name="orderBy", description="Sort by field. Default: volume", schema=str, location="query")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 10", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="duration", description="Duration to return change rate. Default: 24 hours.", schema=int, location="query")
@validate(query=TopNFTsQuery)
async def get_top_nfts(request: Request, query: TopNFTsQuery):
    keys = [
        'name', 'imgUrl', 'volume', 'price',
        'numberOfOwners', 'numberOfItems'
    ]
    change = {'price': 'priceChangeLogs', 'volume': 'volumeChangeLogs'}

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    data = get_documents_with_query(
        db, query=query,
        project_type=ProjectCollectorTypes.nft,
        keys=keys, change=change
    )
    return json(data)


@rankings_bp.get('/tokens')
@openapi.tag("Ranking")
@openapi.summary("Get the list of tokens")
@openapi.parameter(name="order", description="Sort direction: asc or desc. Default: desc", schema=str, location="query")
@openapi.parameter(name="orderBy", description="Sort by field. Default: tokenHealth", schema=str, location="query")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 10", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="duration", description="Duration to return change rate. Default: 24 hours.", schema=int, location="query")
@validate(query=TopTokensQuery)
async def get_top_tokens(request: Request, query: TopTokensQuery):
    keys = ['name', 'symbol', 'imgUrl', 'numberOfHolders', 'price', 'marketCap', 'tokenHealth']
    mapping = {'volume': 'tradingVolume'}
    change = {'price': 'priceChangeLogs'}

    skip, limit = parse_pagination(query.page, query.pageSize)
    sort_by = query.orderBy
    if sort_by in mapping:
        sort_by = mapping[sort_by]
    reverse = True if query.order == 'desc' else False

    duration = query.duration

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    last_updated_at = int(time.time() - 2 * TimeConstants.A_DAY)
    tokens_cursor = db.get_contracts_by_type(
        'token', projection=['address', 'chainId', 'idCoingecko', sort_by],
        last_updated_at=last_updated_at
    )
    tokens = {}
    for doc in tokens_cursor:
        coin_id = doc['idCoingecko']
        if coin_id not in tokens:
            tokens[coin_id] = {'id': coin_id, sort_by: 0, 'keys': []}

        tokens[coin_id]['keys'].append(f'{doc["chainId"]}_{doc["address"]}')
        if sort_by == 'numberOfHolders':
            tokens[coin_id][sort_by] += doc.get(sort_by) or 0
        else:
            tokens[coin_id][sort_by] = doc.get(sort_by)

    number_of_docs = len(tokens)
    tokens = sorted(list(tokens.values()), key=lambda x: x[sort_by] or 0, reverse=reverse)
    tokens = tokens[skip:skip + limit]

    token_keys = []
    for token in tokens:
        token_keys.extend(token['keys'])

    tokens_cursor = db.get_contracts_by_keys(token_keys)

    tokens = {}
    for doc in tokens_cursor:
        coin_id = doc['idCoingecko']
        if coin_id not in tokens:
            token = {'id': coin_id, 'type': 'token'}
            token.update({k: doc.get(m) for k, m in mapping.items()})
            token.update({k: v for k, v in doc.items() if k in keys})
            token['numberOfHolders'] = 0

            # Calculate change rate in duration
            for field, change_log_field in change.items():
                change_log = doc.get(change_log_field) or {}
                change_log = sort_log(change_log)
                token[f'{field}ChangeRate'] = get_logs_change_rate(change_log, duration=duration)

            tokens[coin_id] = token
        tokens[coin_id]['numberOfHolders'] += doc.get('numberOfHolders') or 0

    tokens = sorted(list(tokens.values()), key=lambda x: x.get(query.orderBy) or 0, reverse=reverse)

    return json({
        'numberOfDocs': number_of_docs,
        'docs': tokens
    })


@rankings_bp.get('/spot-exchanges')
@openapi.tag("Ranking")
@openapi.summary("Get the list of spot exchanges")
@openapi.parameter(name="order", description="Sort direction: asc or desc. Default: desc", schema=str, location="query")
@openapi.parameter(name="orderBy", description="Sort by field. Default: volume", schema=str, location="query")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 10", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="duration", description="Duration to return change rate. Default: 24 hours.", schema=int, location="query")
@validate(query=TopSpotExchangesQuery)
async def get_top_spot_exchanges(request: Request, query: TopSpotExchangesQuery):
    keys = ['name', 'imgUrl', 'avgLiquidity', 'weeklyVisits', 'numberOfCoins', 'fiatSupported']
    mapping = {
        'volume': 'spotVolume',
        # 'volumeChangeRate': 'spotVolumeChangeRate',
        'numberOfMarkets': 'spotMarkets',
        'volumeHistoryGraph': 'spotVolumeGraph',
        'volumeHistoryGraphIsUp': 'spotVolumeGraphIncrease'
    }
    change = {'volume': 'spotVolumeChangeLogs'}

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    data = get_documents_with_query(
        db, query=query, project_type=ProjectCollectorTypes.spot_exchange,
        keys=keys, mapping=mapping, change=change
    )
    return json(data)


@rankings_bp.get('/derivative-exchanges')
@openapi.tag("Ranking")
@openapi.summary("Get the list of derivative exchanges")
@openapi.parameter(name="order", description="Sort direction: asc or desc. Default: desc", schema=str, location="query")
@openapi.parameter(name="orderBy", description="Sort by field. Default: volume", schema=str, location="query")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 10", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="duration", description="Duration to return change rate. Default: 24 hours.", schema=int, location="query")
@validate(query=TopDerivativeExchangesQuery)
async def get_top_derivative_exchanges(request: Request, query: TopDerivativeExchangesQuery):
    keys = ['name', 'imgUrl', 'makerFeesRate', 'takerFeesRate', 'openInterests', 'launchedAt']
    mapping = {
        'volume': 'derivativeVolume',
        # 'volumeChangeRate': 'derivativeVolumeChangeRate',
        'numberOfMarkets': 'derivativeMarkets'
    }
    change = {'volume': 'derivativeVolumeChangeLogs'}

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    data = get_documents_with_query(
        db, query=query, project_type=ProjectCollectorTypes.derivative_exchange,
        keys=keys, mapping=mapping, change=change
    )
    return json(data)


def get_documents_with_query(db: Union[MongoDB, KLGDatabase], query, project_type: str, keys=None, mapping=None, change=None, chain_id=None, category=None):
    if keys is None:
        keys = []
    if mapping is None:
        mapping = {}
    if change is None:
        change = {}

    skip, limit = parse_pagination(query.page, query.pageSize)
    sort_by = query.orderBy
    if sort_by in mapping:
        sort_by = mapping[sort_by]
    reverse = True if query.order == 'desc' else False

    duration = query.duration

    last_updated_at = int(time.time() - 2 * TimeConstants.A_DAY)
    number_of_docs = db.count_projects_by_type(project_type, chain=chain_id, category=category, last_updated_at=last_updated_at)
    docs = db.get_projects_by_type(
        project_type,
        sort_by=sort_by, reverse=reverse,
        skip=skip, limit=limit,
        chain=chain_id, category=category,
        last_updated_at=last_updated_at
    )
    docs = list(docs)

    projects = []
    for doc in docs:
        project = {'id': doc['id'], 'type': 'project'}
        project.update({k: doc.get(m) for k, m in mapping.items()})
        project.update({k: v for k, v in doc.items() if k in keys})

        if project_type == ProjectCollectorTypes.defillama:
            project['chains'] = list(doc.get('deployedChains', []))

        # Calculate change rate in duration
        for field, change_log_field in change.items():
            change_log = doc.get(change_log_field) or {}
            change_log = sort_log(change_log)
            project[f'{field}ChangeRate'] = get_logs_change_rate(change_log, duration=duration)

        projects.append(project)

    if project_type == ProjectCollectorTypes.defillama:
        tx_and_user_info = handler_for_defillama(db, docs)
        for project in projects:
            tx_and_user = tx_and_user_info.get(project['id'], {})
            project.update(tx_and_user)

    return {
        'numberOfDocs': number_of_docs,
        'docs': projects
    }


def handler_for_defillama(db: Union[MongoDB, KLGDatabase], docs):
    contract_keys = set()
    for doc in docs:
        contract_keys.update(list(doc.get('contractAddresses', {}).keys()))

    contracts_cursor = db.get_contracts_by_keys(keys=list(contract_keys), projection=[
        'address', 'chainId',
        'numberOfLastDayActiveUsers',
        'numberOfLastDayCalls',
    ])
    contracts = {f"{t['chainId']}_{t['address']}": t for t in contracts_cursor}

    tx_and_user_data = {}
    for doc in docs:
        key = doc['id']
        number_of_wallets = 0
        number_of_transactions = 0
        for contract_key in doc.get('contractAddresses', {}).keys():
            contract = contracts.get(contract_key)
            if contract is None:
                continue

            number_of_wallets += contract.get('numberOfLastDayActiveUsers') or 0
            number_of_transactions += contract.get('numberOfLastDayCalls') or 0

        tx_and_user_data[key] = {
            'numberOfUsers': number_of_wallets or None,
            'numberOfTransactions': number_of_transactions or None
        }

    return tx_and_user_data
