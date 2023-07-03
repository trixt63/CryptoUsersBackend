import time
from typing import Union

from redis import Redis
from sanic import Blueprint, Request
from sanic import json
from sanic_ext import openapi, validate

from app.apis._olds.portfolio.utils.utils import check_address, get_chains
from app.constants.network_constants import EMPTY_TOKEN_IMG
from app.constants.search_constants import SearchConstants, RelationshipType
from app.constants.time_constants import TimeConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.async_blockchain_etl import AsyncBlockchainETL
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.postgresdb.token_transfer import TokenTransferDB
from app.models.blocks_mapping_timestamp import Blocks
from app.models.entity.wallet import OverviewQuery, CreditScoreQuery, TransactionsQuery
from app.models.explorer.link import Link
from app.models.explorer.node import Node
from app.models.explorer.visualization import Visualization
from app.services.cached.cache_dapps import CacheDApps
from app.services.cached.cache_tokens import CacheTokens
from app.services.jobs.portfolio_jobs.multithread_dapps_job import MultithreadDappsJob
from app.services.jobs.portfolio_jobs.multithread_tokens_job import MultithreadTokensJob
from app.services.transaction_services import TransactionService
from app.utils.format_utils import short_address
from app.utils.list_dict_utils import sort_log, combined_logs, merge_logs, coordinate_logs
from app.utils.parser import parse_pagination
from app.utils.search_data_utils import get_explorer_link
from app.utils.time_utils import round_timestamp
from app.utils.validate_query import wallet_transactions_with_pagination

wallets_bp = Blueprint('wallets_blueprint', url_prefix='/wallets')


@wallets_bp.get('/<address>/introduction')
@openapi.tag("Wallet")
@openapi.summary("Get wallet introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="address", description=f"Address", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, address, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)
    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    wallets = db.get_wallet_by_address(address, None, projection=['chainId', 'balanceInUSD', 'depositInUSD', 'borrowInUSD'])

    returned_chains = set()
    explorers = []
    total_balance = 0
    total_tvl = 0
    for wallet in wallets:
        chain = wallet['chainId']
        returned_chains.add(chain)
        if chain not in chains:
            continue

        total_balance += wallet.get('balanceInUSD') or 0
        deposit_in_usd = wallet.get('depositInUSD') or 0
        borrow_in_usd = wallet.get('borrowInUSD') or 0
        total_tvl += deposit_in_usd - borrow_in_usd

        explorers.append(get_explorer_link(chain, address, SearchConstants.wallet))

    credit_score, _ = db.get_score_change_logs(address)

    return json({
        'id': address,
        'name': short_address(address),
        'address': address,
        'explorerUrls': explorers,
        'chains': list(returned_chains),
        'creditScore': credit_score,
        'balance': max(total_balance, 0),
        'dappsValue': max(total_tvl, 0),
    })


@wallets_bp.get('/<address>/overview')
@openapi.tag("Wallet")
@openapi.summary("Get wallet overview")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="address", description=f"Address", location="path", required=True)
@validate(query=OverviewQuery)
async def get_overview(request: Request, address, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)
    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    r: Redis = request.app.ctx.redis
    tokens_by_chain = CacheTokens.get_top_tokens_by_chain(r, db, chains)
    dapps = CacheDApps.get_dapps(r, db, chains)

    credit_score, _ = db.get_score_change_logs(address)

    contracts = db.get_contracts_by_address(
        address, chains, projection=['address', 'chainId', 'tags', 'name', 'symbol', 'idCoingecko', 'imgUrl'])
    trackers = []
    for contract in contracts:
        address = contract['address']
        chain_id = contract['chainId']
        tags = contract.get('tags') or []
        contract_type = SearchConstants.token if 'token' in tags else SearchConstants.contract
        id_ = contract['idCoingecko'] if contract.get('idCoingecko') else f"{chain_id}_{address}"
        trackers.append({
            'id': id_,
            'type': contract_type,
            'name': contract.get('name') or short_address(address),
            'symbol': contract.get('symbol'),
            'imgUrl': contract.get('imgUrl') or EMPTY_TOKEN_IMG
        })

    asset_job = MultithreadTokensJob(address, tokens_by_chain)
    asset_job.run()
    assets = asset_job.get_assets()
    total_balance = sum([a['valueInUSD'] for a in assets])

    w_chains = asset_job.get_chains()
    explorer_urls = [get_explorer_link(chain, address, SearchConstants.wallet) for chain in w_chains]

    dapp_job = MultithreadDappsJob(address, dapps, db)
    dapp_job.run()
    dapps = dapp_job.get_dapps()
    total_tvl = sum([d['value'] for d in dapps])

    return json({
        'id': address,
        'address': address,
        'chains': w_chains,
        'explorerUrls': explorer_urls,
        'creditScore': credit_score,
        'tracker': trackers[0] if trackers else None,
        'balance': total_balance,
        'dappsValue': total_tvl,
        'assets': assets,
        'dapps': dapps
    })


@wallets_bp.get('/<address>/transactions')
@openapi.tag("Wallet")
@openapi.summary("Get wallet transactions")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 25", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="address", description=f"Address", location="path", required=True)
@validate(query=TransactionsQuery)
async def get_transactions(request: Request, address, query: TransactionsQuery):
    wallet_transactions_with_pagination(query)

    chain_id = query.chain
    skip, limit = parse_pagination(query.page, query.pageSize)

    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    async_mongo: AsyncBlockchainETL = request.app.ctx.async_mongo
    tx_service = TransactionService(db, mongo, async_mongo)

    wallets = db.get_wallet_by_address(address, chain_id=chain_id, projection=['chainId', 'dailyAllTransactions'])
    chains = [w['chainId'] for w in wallets]

    timestamp_30_days_ago = round_timestamp(int(time.time())) - TimeConstants.DAYS_30

    transactions = []
    number_of_transactions = 0
    for chain in chains:
        # Calculate block number of 30 days ago
        start_block = Blocks().block_numbers(chain, timestamp_30_days_ago)

        transactions_info = tx_service.get_transactions(
            chain, address, start_block=start_block, skip=skip, limit=limit)

        transactions.extend(transactions_info['transactions'])
        number_of_transactions += transactions_info['numberOfTransactions']

    transactions = sorted(transactions, key=lambda x: x.block_timestamp, reverse=True)[:limit]
    transactions = [tx.to_dict() for tx in transactions]

    wallets_daily_transactions = [sort_log(w['dailyAllTransactions']) for w in wallets if w.get('dailyAllTransactions')]
    daily_transactions = combined_logs(*wallets_daily_transactions, handler_func=sum, default_value=0)
    daily_transactions = coordinate_logs(daily_transactions, start_time=timestamp_30_days_ago, frequency=TimeConstants.A_DAY)

    return json({
        'id': address,
        'numberOfTransactions': number_of_transactions,
        'dailyTransactions': daily_transactions,
        'transactions': transactions
    })


@wallets_bp.get('/<address>/money-flow')
@openapi.tag("Wallet")
@openapi.summary("Get wallet money flow")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="address", description=f"Address", location="path", required=True)
@validate(query=OverviewQuery)
async def get_money_flow(request: Request, address, query: OverviewQuery):
    chain_id = query.chain
    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    transfer_db: TokenTransferDB = request.app.ctx.transfer_db

    wallets = db.get_wallet_by_address(address, chain_id=chain_id, projection=['chainId', 'dailyNumberOfTransactions'])
    chains = [w['chainId'] for w in wallets]

    timestamp_a_day_ago = int(time.time()) - TimeConstants.A_DAY
    tokens_value = {}
    for chain in chains:
        from_block = Blocks().block_numbers(chain, timestamp_a_day_ago)
        incoming = transfer_db.get_incoming_token_amount(chain, address, from_block=from_block)
        for row in incoming:
            tokens_value[f"{chain}_{row['contract_address']}"] = {'input': row['total_value']}

        outgoing = transfer_db.get_outgoing_token_amount(chain, address, from_block=from_block)
        for row in outgoing:
            contract_key = f"{chain}_{row['contract_address']}"
            if contract_key not in tokens_value:
                tokens_value[contract_key] = {}
            tokens_value[f"{chain}_{row['contract_address']}"].update({'output': row['total_value']})

    tokens = db.get_contracts_by_keys(
        list(tokens_value.keys()),
        projection=['address', 'chainId', 'idCoingecko', 'name', 'symbol', 'price', 'imgUrl']
    )
    tokens = {f"{t['chainId']}_{t['address']}": t for t in tokens}

    data = {}
    for token_key, in_out in tokens_value.items():
        token = tokens.get(token_key) or {}
        chain, token_address = token_key.split('_')
        token_id = token.get('idCoingecko') or token_key
        price = token.get('price')

        if token_id not in data:
            data[token_id] = {
                "id": token_id,
                "type": SearchConstants.token,
                "name": token.get('name') or short_address(token_address),
                "symbol": token.get('symbol') or 'UNKNOWN',
                "imgUrl": token.get('imgUrl') or EMPTY_TOKEN_IMG,
                "price": price,
                "input": {
                    "amount": 0,
                },
                "output": {
                    "amount": 0,
                }
            }

        data[token_id]['input']['amount'] += in_out.get('input', 0)
        data[token_id]['output']['amount'] += in_out.get('output', 0)

    for info in data.values():
        price = info['price']
        key = 'valueInUSD'
        if price is None:
            info['input'][key] = None
            info['output'][key] = None
            info['transferVolume'] = None
        else:
            info['input'][key] = info['input']['amount'] * price
            info['output'][key] = info['output']['amount'] * price
            info['transferVolume'] = info['input'][key] + info['output'][key]

    transfers = sorted(data.values(), key=lambda x: x.get('transferVolume') or 0, reverse=True)

    # TODO: exchanges

    exchanges = []
    for _ in range(10):
        exchanges.append({
            "name": "PancakeSwap V2",
            "type": "project",
            "id": "pancakeswap",
            "tradingVolume": 190.1,
            "transactions": 5
        })

    return json({
        'id': address,
        'tokens': transfers,
        'exchanges': exchanges
    })


@wallets_bp.get('/<address>/credit-score')
@openapi.tag("Wallet")
@openapi.summary("Get wallet credit score")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="address", description=f"Address", location="path", required=True)
@validate(query=CreditScoreQuery)
async def get_credit_score(request: Request, address, query: CreditScoreQuery):
    chain_id = query.chain
    duration = query.duration

    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    wallets = db.get_wallet_by_address(address, chain_id=chain_id, projection=['balanceInUSD', 'balanceChangeLogs'])

    current_time = int(time.time())

    # Get balance information
    balance_change_logs = []
    for w in wallets:
        balance_change_logs_ = sort_log(w.get('balanceChangeLogs', {}))
        balance_change_logs_ = coordinate_logs(
            balance_change_logs_, start_time=current_time - duration,
            frequency=int(duration / 100), fill_start_value=True, default_start_value=0
        )
        balance_change_logs.append(balance_change_logs_)

    balance_history = combined_logs(*balance_change_logs)

    credit_score, credit_score_history = db.get_score_change_logs(address)
    credit_score_history = coordinate_logs(
        credit_score_history, start_time=current_time - duration,
        frequency=int(duration / 100), fill_start_value=True, default_start_value=0
    )
    data_history = merge_logs({'balance': balance_history, 'creditScore': credit_score_history}, default_value=0)

    score_detail = db.get_score_details(address)

    data = {
        'creditScore': credit_score,
        'detail': score_detail
    }
    if credit_score_history:
        data['minCreditScore'] = min(credit_score_history.values())
        data['maxCreditScore'] = max(credit_score_history.values())
    else:
        data['minCreditScore'] = credit_score
        data['maxCreditScore'] = credit_score
    data['creditScoreHistory'] = data_history

    return json({
        'id': address,
        **data
    })


@wallets_bp.get('/<address>/visualize')
@openapi.tag("Wallet")
@openapi.summary("Get wallet visualize information")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="address", description=f"Address", location="path", required=True)
@validate(query=OverviewQuery)
async def get_visualize(request: Request, address, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)
    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    r: Redis = request.app.ctx.redis
    tokens_by_chain = CacheTokens.get_top_tokens_by_chain(r, db, chains)
    dapps = CacheDApps.get_dapps(r, db, chains)

    visualize = Visualization()
    node = Node.wallet_node(address)
    visualize.focus(node)

    contracts = db.get_contracts_by_address(address, chains, projection=['tags', 'name', 'address', 'chainId', 'idCoingecko'])
    for contract in contracts:
        tracker_node = Node.contract_node(contract)
        visualize.add_node(tracker_node)
        visualize.add_link(Link.from_dict({'source': node.id, 'target': tracker_node.id, 'type': RelationshipType.tracker}))

    asset_job = MultithreadTokensJob(address, tokens_by_chain)
    asset_job.run()
    assets = asset_job.get_assets()
    for asset in assets:
        asset_node = Node.from_dict({'key': asset['id'], 'type': SearchConstants.token, 'name': asset['name']})
        visualize.add_node(asset_node)
        visualize.add_link(Link.from_dict({'source': node.id, 'target': asset_node.id, 'type': RelationshipType.hold}))

    dapp_job = MultithreadDappsJob(address, dapps, db)
    dapp_job.run()
    dapps = dapp_job.get_dapps()
    for dapp in dapps:
        dapp_node = Node.contract_node(dapp)
        visualize.add_node(dapp_node)
        visualize.add_link(Link.from_dict({'source': node.id, 'target': dapp_node.id, 'type': RelationshipType.use}))

    return json({
        'id': address,
        **visualize.to_dict()
    })
