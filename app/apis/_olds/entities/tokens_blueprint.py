import random
import time
from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic_ext import openapi, validate
from web3 import Web3

from app.apis.portfolio.utils.utils import get_chains
from app.constants.network_constants import EMPTY_TOKEN_IMG
from app.constants.search_constants import SearchConstants, RelationshipType
from app.constants.time_constants import TimeConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.mongodb.mongodb_token import MongoDBToken
from app.databases.postgresdb.token_transfer import TokenTransferDB
from app.models.blocks_mapping_timestamp import Blocks
from app.models.entity.projects import ProjectTypes
from app.models.entity.token import OverviewQuery, TransfersQuery
from app.models.explorer.node import Node
from app.models.explorer.visualization import Visualization
from app.services.artifacts.exchanges.exchanges_mapping import EXCHANGE_MAPPING
from app.services.market_service import MarketService
from app.services.transaction_services import TransactionService
from app.utils.format_utils import short_address
from app.utils.list_dict_utils import get_value_with_default, sort_log, combined_logs, coordinate_logs
from app.utils.parser import parse_pagination
from app.utils.search_data_utils import get_explorer_link
from app.utils.time_utils import round_timestamp
from app.utils.validate_query import wallet_transactions_with_pagination

tokens_bp = Blueprint('tokens_blueprint', url_prefix='/tokens')

token_db = MongoDBToken()


@tokens_bp.get('/<token_id>/introduction')
@openapi.tag("Token")
@openapi.summary("Get token introduction")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_introduction(request: Request, token_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)
    all_chains = get_chains(None)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    projection = ['address', 'chainId', 'idCoingecko', 'tags', 'name', 'symbol', 'price', 'marketCap', 'tokenHealth', 'imgUrl']
    contracts = db.get_tokens_by_id(token_id, chains=all_chains, projection=projection)

    returned_chains = set()
    if not contracts:
        chain, address = token_id.split('_')
        returned_chains.add(chain)
        data = {
            'name': short_address(address),
            'symbol': 'UNKNOWN',
            'explorerUrls': [get_explorer_link(chain, address, SearchConstants.token)],
            'price': None,
            'marketCap': None,
            'imgUrl': EMPTY_TOKEN_IMG
        }
    else:
        contract = contracts[0]
        data = {
            'name': contract.get('name') or short_address(contract['address']),
            'symbol': contract.get('symbol') or 'UNKNOWN',
            'explorerUrls': [],
            'price': contract.get('price'),
            'marketCap': contract.get('marketCap'),
            'imgUrl': contract.get('imgUrl') or EMPTY_TOKEN_IMG
        }

    for contract in contracts:
        chain = contract['chainId']
        returned_chains.add(chain)
        if chain not in chains:
            continue

        address = contract['address']
        data['explorerUrls'].append(get_explorer_link(contract['chainId'], address, SearchConstants.token))
        if contract.get('tokenHealth'):
            data['tokenHealth'] = contract['tokenHealth']

        if chain_id:
            data['address'] = address

    data['chains'] = list(returned_chains)
    return json({
        'id': token_id,
        **data
    })


@tokens_bp.get('/<token_id>/overview')
@openapi.tag("Token")
@openapi.summary("Get token overview information")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_overview(request: Request, token_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    projection = [
        'address', 'chainId', 'idCoingecko', 'tags', 'name', 'symbol', 'decimals',
        'price', 'marketCap', 'tradingVolume', 'totalSupply', 'numberOfHolders', 'tokenHealth'
    ]
    contracts = db.get_tokens_by_id(token_id, chains=chains, projection=projection)
    data = {}
    for contract in contracts:
        address = contract['address']
        if not data:
            data = {
                'idCoingecko': contract.get('idCoingecko'),
                'name': contract.get('name') or short_address(address),
                'symbol': contract.get('symbol') or 'UNKNOWN',
                'decimals': contract.get('decimals') or 18,
                'chains': [],
                'explorerUrls': [],
                'price': contract.get('price'),
                'marketCap': contract.get('marketCap'),
                'tradingVolume': contract.get('tradingVolume'),
                'totalSupply': contract.get('totalSupply'),
                'numberOfHolders': 0,
            }

        data['chains'].append(contract['chainId'])
        data['numberOfHolders'] += contract.get('numberOfHolders') or 0
        data['explorerUrls'].append(get_explorer_link(contract['chainId'], address, SearchConstants.token))

        if chain_id is not None:
            data['address'] = address

        if contract.get('tokenHealth'):
            data['tokenHealth'] = contract['tokenHealth']

    data['chains'] = list(set(data.get('chains', [])))
    if data.get('idCoingecko'):
        market_service = MarketService()
        social_info = market_service.get_token_info(data.pop('idCoingecko'))
        data.update(social_info)

    return json({
        'id': token_id,
        **data
    })


@tokens_bp.get('/<token_id>/transfers')
@openapi.tag("Token")
@openapi.summary("Get token transfers")
@openapi.parameter(name="pageSize", description="Number of documents per page. Default: 25", schema=int, location="query")
@openapi.parameter(name="page", description="Page 1-based index. Default: 1", schema=int, location="query")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=TransfersQuery)
async def get_transfers(request: Request, token_id, query: TransfersQuery):
    wallet_transactions_with_pagination(query)

    chain_id = query.chain
    chains = get_chains(chain_id)
    skip, limit = parse_pagination(query.page, query.pageSize)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    transfer_db: TokenTransferDB = request.app.ctx.transfer_db
    tx_service = TransactionService(graph=db, mongo=mongo)

    contracts = db.get_tokens_by_id(token_id, chains=chains, projection=['chainId', 'address', 'tokenDailyTransfers'])

    current_time = int(time.time())
    timestamp_30_days_ago = round_timestamp(current_time) - TimeConstants.DAYS_30

    transfers_objs = []
    daily_transfers = []
    for contract in contracts:
        chain = contract['chainId']
        start_block = Blocks().block_numbers(chain, timestamp_30_days_ago)

        # For exactly
        # number_of_transfers_ = transfer_db.count_event_transfer_by_contract(
        #     chain_id=chain, contract_address=contract['address'],
        #     from_block=start_block
        # )
        # number_of_transfers += number_of_transfers_[0]['number_of_events']

        if contract.get('tokenDailyTransfers'):
            daily_transfers.append(sort_log(contract['tokenDailyTransfers']))

        transfers = transfer_db.get_event_transfer_by_contract(
            chain_id=chain,
            contract_address=contract['address'],
            from_block=start_block, skip=skip, limit=limit
        )
        transfers = tx_service.transfers_info(chain, transfers)
        tx_service.update_transfers_tx_info(transfers, chain)
        transfers_objs.extend(transfers)

    transfers_objs = sorted(transfers_objs, key=lambda x: x.timestamp or 0, reverse=True)[:limit]
    transfers = [transfer.to_dict() for transfer in transfers_objs]

    end_time = round_timestamp(current_time, TimeConstants.A_DAY)
    daily_transfers = combined_logs(*daily_transfers, handler_func=sum, default_value=0)
    daily_transfers = coordinate_logs(daily_transfers, start_time=timestamp_30_days_ago, end_time=end_time, frequency=TimeConstants.A_DAY)
    number_of_transfers = sum(daily_transfers.values())

    return json({
        'id': token_id,
        'numberOfTransfers': number_of_transfers,
        'dailyTransfers': daily_transfers,
        'transfers': transfers
    })


@tokens_bp.get('/<token_id>/holders')
@openapi.tag("Token")
@openapi.summary("Get token holders")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_token_holders(request: Request, token_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    projection = [
        'address', 'chainId', 'idCoingecko', 'tags',
        'price', 'totalSupply', 'numberOfHolders', 'topHolders'
    ]
    contracts = db.get_tokens_by_id(token_id, chains=chains, projection=projection)

    number_of_holders = 0
    holders = {}
    price = 0
    total_supply = 0
    for contract in contracts:
        price = get_value_with_default(contract, key='price', default=price)
        total_supply = get_value_with_default(contract, key='totalSupply', default=total_supply)

        chain = contract['chainId']
        top_holders = get_value_with_default(contract, key='topHolders', default={})

        number_of_holders += get_value_with_default(contract, key='numberOfHolders', default=0)
        for w_address, holder_info in top_holders.items():
            id_ = w_address
            type_ = SearchConstants.wallet
            if holder_info.get('isContract'):
                id_ = f'{chain}_{w_address}'
                type_ = SearchConstants.contract

            if id_ not in holders:
                holders[id_] = {
                    'id': id_,
                    'address': w_address,
                    'type': type_,
                    'balance': 0,
                    'isContract': holder_info.get('isContract', False)
                }
            holders[id_]['balance'] += holder_info['balance']

    for holder in holders.values():
        holder['value'] = holder['balance'] * price
        holder['percentage'] = 100 * holder['balance'] / total_supply if total_supply else 0

    holders = list(sorted(holders.values(), key=lambda x: x['balance'], reverse=True))
    return json({
        'id': token_id,
        'numberOfHolders': number_of_holders,
        'numberOfTopHolders': len(holders),
        'holders': holders
    })


@tokens_bp.get('/<token_id>/exchanges')
@openapi.tag("Token")
@openapi.summary("Get token exchanges")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_token_exchanges(request: Request, token_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    projection = ['address', 'chainId', 'idCoingecko', 'tags']
    contracts = db.get_tokens_by_id(token_id, chains=chains, projection=projection)
    if (not contracts) or (not contracts[0].get('idCoingecko')):
        json({'id': token_id, 'numberOfExchanges': 0, 'exchanges': []})

    id_coingecko = contracts[0]['idCoingecko']
    chains_by_address = {contract['address']: contract['chainId'] for contract in contracts}

    market_service = MarketService()
    token_exchanges = market_service.get_token_exchanges(id_coingecko)

    exchanges = []
    token_keys = []
    for exchange in token_exchanges:
        exchange_project_info = EXCHANGE_MAPPING.get(exchange['id'])
        if not exchange_project_info:
            continue

        exchange.update({
            'id': exchange_project_info['project_id'],
            'type': SearchConstants.project,
            'projectType': ProjectTypes.mapping[exchange_project_info['project_type']]
        })

        base = exchange['base'].lower()
        target = exchange['target'].lower()
        is_dex = Web3.isAddress(base)
        if is_dex:
            chain = get_value_with_default(chains_by_address, key=target, default=chains_by_address.get(base))
            if not chain:
                continue

            token_keys.append(f'{chain}_{base}')
            if Web3.isAddress(target):
                token_keys.append(f'{chain}_{target}')

        exchange['isDex'] = is_dex
        exchanges.append(exchange)
        if len(exchanges) >= 10:
            break

    token_keys = list(set(token_keys))
    tokens = db.get_contracts_by_keys(token_keys, projection=['address', 'symbol'])
    tokens = {t['address']: t['symbol'] for t in tokens}

    for exchange in exchanges:
        base = exchange.pop('base').lower()
        target = exchange.pop('target').lower()
        base = tokens.get(base, base)
        target = tokens.get(target, target)
        exchange['pair'] = f'{base}/{target}'.upper()

    return json({
        'id': token_id,
        'numberOfExchanges': len(exchanges),
        'exchanges': exchanges
    })


@tokens_bp.get('/<token_id>/token-health')
@openapi.exclude()  # TODO: ignore
@openapi.tag("Token")
@openapi.summary("Get token health information")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_token_health(request: Request, token_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    projection = ['address', 'chainId', 'idCoingecko', 'tags']
    contracts = db.get_tokens_by_id(token_id, chains=chains, projection=projection)
    if (not contracts) or (not contracts[0].get('idCoingecko')):
        raise

    id_coingecko = contracts[0].get('idCoingecko')
    token = token_db.get_token(id_coingecko)
    if not token:
        raise

    # TODO: get token information, rank, score

    return json({
        'id': token_id,
        "name": "Tether",
        "address": None,
        "symbol": "USDT",
        "creditScore": 734,
        "categories": [
            "Token",
            "Stablecoins",
            "USD Stablecoin"
        ],
        "price": 0.99877,
        "highestPrice": 1.32,
        "priceStability": 99.88,
        "holder": 9072311,
        "holderDistribution": 9.023729892233419,
        "marketCap": 70975423192,
        "tradingVolume24h": 36947510643,
        "dailyTransaction": 461545,
        "rankMarketCap": 2,
        "rankHolders": 3,
        "rankDailyTransactions": 2,
        "rankStable": 11,
        "rankCreditScore": 2,
        "rankTradingVolume24h": 1,
        "rankTradingVolume7d": 1,
        "rankTradingVolume100d": 1,
        "marketCapScore": 854,
        "priceOverHighestScore": 757,
        "numberOfTransactionScore": 998,
        "tradingOverCapScore": 665,
        "holdersScore": 691,
        "holderDistributionScore": 527,
        "priceStabilityScore": 532,
        "imgUrl": "https://storage.googleapis.com/tokenhealth-abb94.appspot.com/tokens/USDT.png"
    })


@tokens_bp.get('/<token_id>/score-history')
@openapi.exclude()  # TODO: ignore
@openapi.tag("Token")
@openapi.summary("Get token health history")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_score_history(request: Request, token_id, query: OverviewQuery):
    chain_id = query.chain

    # TODO: query token database to get history

    keys = [
        'creditScoreHistory', 'dailyTransactionHistory', 'holderDistributionHistory', 'holderHistory',
        'marketCapHistory', 'priceHistory', 'priceStabilityHistory', 'tradingVolume24hHistory',
        'numberOfTransactionScoreHistory', 'holderDistributionScoreHistory', 'holdersScoreHistory',
        'marketCapScoreHistory', 'priceOverHighestScoreHistory', 'priceStabilityScoreHistory', 'tradingScoreHistory'
    ]
    data = {}
    timestamp_15d_ago = int(time.time()) - 15 * TimeConstants.A_DAY
    for key in keys:
        history = []
        for idx in range(15):
            history.append([timestamp_15d_ago + idx * TimeConstants.A_DAY, random.randint(0, 1000)])
        data[key] = history

    return json({
        'id': token_id,
        **data
    })


@tokens_bp.get('/<token_id>/visualize')
@openapi.tag("Token")
@openapi.summary("Get token visualize information")
@openapi.parameter(name="chain", description=f"Chain ID", location="query")
@openapi.parameter(name="token_id", description=f"Token ID", location="path", required=True)
@validate(query=OverviewQuery)
async def get_visualize(request: Request, token_id, query: OverviewQuery):
    chain_id = query.chain
    chains = get_chains(chain_id)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    contracts = db.get_tokens_by_id(token_id, chains=chains, projection=['chainId', 'name', 'topHolders', 'idCoingecko'])
    if not contracts:
        return json({'id': token_id, 'nodes': [], 'links': []})

    visualize = Visualization()

    # Token node
    node = Node.token_node(contracts[0])
    visualize.focus(node)

    # Holder
    holders = {}
    for contract in contracts:
        chain = contract['chainId']
        top_holders = get_value_with_default(contract, key='topHolders', default={})

        for w_address, holder_info in top_holders.items():
            id_ = w_address
            type_ = SearchConstants.wallet
            if holder_info.get('isContract'):
                id_ = f'{chain}_{w_address}'
                type_ = SearchConstants.contract

            if id_ not in holders:
                holders[id_] = {
                    'id': id_,
                    'address': w_address,
                    'type': type_,
                    'balance': 0,
                    'isContract': holder_info.get('isContract')
                }
            holders[id_]['balance'] += holder_info['balance']

    holders = list(sorted(holders.values(), key=lambda x: x['balance'], reverse=True))
    holders = holders[:10]

    holder_is_contract_keys = [w['id'] for w in holders if w['isContract']]
    holder_is_contracts = db.get_contracts_by_keys(holder_is_contract_keys, projection=['address', 'chainId', 'name'])
    holder_is_contracts = {f"{w['chainId']}_{w['address']}": w for w in holder_is_contracts}

    for holder in holders:
        info = holder_is_contracts.get(holder['id']) or {}
        holder.update(info)

        holder_node = Node.contract_node(holder)
        visualize.add_node(holder_node)
        visualize.link_from_node(source=holder_node, type_=RelationshipType.hold)

    # Exchange
    market_service = MarketService()
    token_exchanges = market_service.get_token_exchanges(contracts[0]['idCoingecko'])

    for exchange in token_exchanges:
        exchange_project_info = EXCHANGE_MAPPING.get(exchange['id'])
        if not exchange_project_info:
            continue

        exchange_node = Node.project_node({
            'key': exchange_project_info['project_id'],
            'type': SearchConstants.project,
            'name': exchange_project_info['name'],
            'projectType': ProjectTypes.mapping[exchange_project_info['project_type']]
        })
        visualize.add_node(exchange_node)
        visualize.link_to_node(target=exchange_node, type_=RelationshipType.exchange)

    return json({
        'id': token_id,
        **visualize.to_dict()
    })
