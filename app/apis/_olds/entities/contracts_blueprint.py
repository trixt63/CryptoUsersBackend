import random
import time
from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import BadRequest
from sanic_ext import openapi, validate
from redis import Redis
from web3 import Web3

from app.constants.network_constants import Chain
from app.constants.search_constants import SearchConstants, RelationshipType
from app.constants.time_constants import TimeConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.blocks_mapping_timestamp import Blocks
from app.models.entity.contract import TransactionsQuery
from app.models.entity.projects import ProjectTypes
from app.models.entity.token import Token
from app.models.explorer.node import Node
from app.models.explorer.visualization import Visualization
from app.services.cached.cache_tokens import CacheTokens
from app.services.jobs.portfolio_jobs.multithread_tokens_job import MultithreadTokensJob
from app.services.transaction_services import TransactionService
from app.utils.format_utils import short_address
from app.utils.list_dict_utils import get_value_with_default, coordinate_logs, sort_log
from app.utils.parser import parse_pagination
from app.utils.search_data_utils import get_explorer_link
from app.utils.time_utils import round_timestamp

contracts_bp = Blueprint('contracts_entity_blueprint', url_prefix='/contracts')


@contracts_bp.get('/<contract_id>/introduction')
@openapi.tag("Contract")
@openapi.summary("Get contract introduction")
@openapi.parameter(name="contract_id", description="Contract ID", location="path", required=True)
async def get_introduction(request: Request, contract_id):
    contract = _check_contract_id(contract_id, request=request)
    chain_id = contract['chainId']
    contract_address = contract['address']

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    r: Redis = request.app.ctx.redis
    tokens_by_chain = CacheTokens.get_top_tokens_by_chain(r, db, [chain_id])

    data = {
        'id': f'{chain_id}_{contract_address}',
        'name': get_value_with_default(contract, key='name', default=short_address(contract_address)),
        'transactions24h': get_value_with_default(contract, key='numberOfLastDayCalls', default=0),
        'users24h': get_value_with_default(contract, key='numberOfLastDayActiveUsers', default=0),
        'address': contract['address'],
        'explorerUrls': [get_explorer_link(chain_id, contract_address, SearchConstants.contract)],
        'chains': [chain_id],
        'verified': contract.get('verified', False)  # TODO: recheck
    }

    asset_job = MultithreadTokensJob(contract_address, tokens_by_chain)
    asset_job.run()
    assets = asset_job.get_assets()
    data['tvl'] = sum([a['valueInUSD'] for a in assets])

    return json(data)


@contracts_bp.get('/<contract_id>/overview')
@openapi.tag("Contract")
@openapi.summary("Get contract overview")
@openapi.parameter(name="contract_id", description="Contract ID", location="path", required=True)
async def get_overview(request, contract_id):
    contract = _check_contract_id(contract_id, request=request)
    chain_id = contract['chainId']
    contract_address = contract['address']

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    r: Redis = request.app.ctx.redis
    tokens_by_chain = CacheTokens.get_top_tokens_by_chain(r, db, [chain_id])

    data = {
        'id': f'{chain_id}_{contract_address}',
        'name': get_value_with_default(contract, key='name', default=short_address(contract_address)),
        'transactions24h': get_value_with_default(contract, key='numberOfLastDayCalls', default=0),
        'users24h': get_value_with_default(contract, key='numberOfLastDayActiveUsers', default=0),
        'address': contract['address'],
        'explorerUrls': [get_explorer_link(contract['chainId'], contract['address'], SearchConstants.contract)],
        'createdAt': contract.get('createdAt'),
        'verified': contract.get('verified', False),
        'chains': [chain_id],
    }

    timestamp_30_days_ago = round_timestamp(int(time.time())) - TimeConstants.DAYS_30

    daily_transactions = get_value_with_default(contract, key='numberOfDailyCalls', default={})
    daily_transactions = sort_log(daily_transactions)
    daily_transactions = coordinate_logs(
        daily_transactions, start_time=timestamp_30_days_ago,
        frequency=TimeConstants.A_DAY, fill_start_value=True, default_start_value=0
    )
    number_of_transactions = sum(daily_transactions.values())
    data['numberOfTransactions'] = number_of_transactions

    project_id = contract.get('project')
    if project_id:
        project_info = db.get_project(project_id)
        if project_info:
            data['project'] = {
                'id': project_id,
                'type': SearchConstants.project,
                'name': project_info.get('name'),
                'projectType': ProjectTypes.defi,
                'url': project_info.get('links', {}).get('website') or project_info.get('url')
            }

    asset_job = MultithreadTokensJob(contract_address, tokens_by_chain)
    asset_job.run()
    assets = asset_job.get_assets()
    data['tvl'] = sum([a['valueInUSD'] for a in assets])
    data['tokens'] = assets

    return json(data)


@contracts_bp.get('/<contract_id>/transactions')
@openapi.tag("Contract")
@openapi.summary("Get contract transactions")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 25", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="contract_id", description="Contract ID", location="path", required=True)
@validate(query=TransactionsQuery)
async def get_transactions(request: Request, contract_id, query: TransactionsQuery):
    contract = _check_contract_id(contract_id, request=request)
    chain_id = contract['chainId']
    contract_address = contract['address']

    skip, limit = parse_pagination(query.page, query.pageSize)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    tx_service = TransactionService(db, mongo)

    timestamp_30_days_ago = round_timestamp(int(time.time())) - TimeConstants.DAYS_30

    # Calculate block number of 30 days ago
    start_block = Blocks().block_numbers(chain_id, timestamp_30_days_ago)

    transactions_info = tx_service.get_transactions(
        chain_id, contract_address, start_block=start_block, skip=skip, limit=limit, count=False)
    transactions = transactions_info['transactions']

    transactions = sorted(transactions, key=lambda x: x.block_timestamp, reverse=True)[:limit]
    transactions = [tx.to_dict() for tx in transactions]

    # Get daily transactions
    daily_transactions = get_value_with_default(contract, key='numberOfDailyCalls', default={})
    daily_transactions = sort_log(daily_transactions)
    daily_transactions = coordinate_logs(
        daily_transactions, start_time=timestamp_30_days_ago,
        frequency=TimeConstants.A_DAY, fill_start_value=True, default_start_value=0
    )
    number_of_transactions = sum(daily_transactions.values())

    return json({
        'id': f'{chain_id}_{contract_address}',
        'numberOfTransactions': number_of_transactions,
        'dailyTransactions': daily_transactions,
        'transactions': transactions
    })


@contracts_bp.get('/<contract_id>/users')
@openapi.tag("Contract")
@openapi.summary("Get contract users")
@openapi.parameter(name="contract_id", description="Contract ID", location="path", required=True)
async def get_users(request: Request, contract_id):
    chain_id, contract_address = contract_id.lower().split('_')

    # TODO: get users

    current_time = int(time.time())
    users = []
    for _ in range(100):
        address = '0x0391be54e72f7e001f6bbc331777710b4f2999ef'
        users.append({
            'id': address,
            'address': address,
            'tvl': random.random() * 1000,
            'percentage': random.random() * 50,
            'lastActiveAt': current_time - random.randint(0, TimeConstants.DAYS_30)
        })
    return json({
        'id': contract_id,
        'numberOfUsers': 1341,
        'numberOfTopUsers': len(users),
        'users': users
    })


@contracts_bp.get('/<contract_id>/visualize')
@openapi.tag("Contract")
@openapi.summary("Get contract visualize information")
@openapi.parameter(name="contract_id", description="Contract ID", location="path", required=True)
async def get_visualize(request: Request, contract_id):
    contract = _check_contract_id(contract_id, request=request)
    chain_id = contract['chainId']
    contract_address = contract['address']

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    tx_service = TransactionService(db, mongo)

    contract.update({'type': SearchConstants.contract})

    visualize = Visualization()
    node = Node.contract_node(contract)
    visualize.focus(node)

    # Project
    project_id = contract.get('project')
    if project_id:
        project_info = db.get_project(project_id)
        if project_info:
            project_node = Node.project_node({
                'key': project_id,
                'type': SearchConstants.project,
                'name': project_info.get('name'),
                'projectType': ProjectTypes.defi,
            })
            visualize.add_node(project_node)
            visualize.link_from_node(source=project_node, type_=RelationshipType.has_contract)

    # Users
    timestamp_30_days_ago = round_timestamp(int(time.time())) - TimeConstants.DAYS_30

    # Calculate block number of 30 days ago
    start_block = Blocks().block_numbers(chain_id, timestamp_30_days_ago)

    transactions_info = tx_service.get_transactions(
        chain_id, contract_address, start_block=start_block, limit=10, count=False, decode_tx_method=False)
    transactions = transactions_info['transactions']
    for transaction in transactions:
        from_ = transaction.from_
        if from_:
            from_node = from_.to_node()
            visualize.add_node(from_node)
            visualize.link_from_node(source=from_node, type_=RelationshipType.call_contract)

    # Supported Tokens
    if contract.get('lendingInfo'):
        lending_info = contract['lendingInfo']
        reserves_list = lending_info.get('reservesList', {})
        token_keys = [f'{chain_id}_{token_address}' for token_address in reserves_list]

        tokens = db.get_contracts_by_keys(keys=token_keys)
        tokens = [Token.from_dict(token) for token in tokens]

        for token in tokens:
            token_node = token.to_node()
            visualize.add_node(token_node)
            visualize.link_to_node(target=token_node, type_=RelationshipType.support)

    return json({
        'id': f'{chain_id}_{contract_address}',
        **visualize.to_dict()
    })


def _check_contract_id(contract_id, request: Request):
    contract_id = contract_id.lower()
    chain_id, contract_address = contract_id.split('_')
    if (chain_id not in Chain.chain_names) or (not Web3.isAddress(contract_address)):
        raise BadRequest(f'Invalid contract id {contract_id}')

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    contracts = db.get_contracts_by_keys(keys=[contract_id])
    contracts = list(contracts)
    contract = contracts[0] if contracts else {'id': contract_id, 'chainId': chain_id, 'address': contract_address}
    return contract
