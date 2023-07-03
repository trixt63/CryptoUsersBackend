import time
from typing import Union

from redis import Redis
from sanic import Blueprint, Websocket
from sanic import json
from sanic.exceptions import BadRequest
from sanic.log import logger
from sanic_ext import openapi, validate

from app.apis._olds.portfolio.utils.utils import get_chains, check_address
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.decorators.auth import protected, check_token
from app.models.portfolio.dapps import DAppsQuery, DAppLendingBalanceQuery
from app.services.cached.cache_dapps import CacheDApps
from app.services.jobs.portfolio_jobs.async_dapps_job import AsyncDappsJob
from app.utils.list_dict_utils import sort_log, combined_logs, combined_token_change_logs_func, coordinate_logs

dapps_bp = Blueprint('dapps_blueprint', url_prefix='/')


@dapps_bp.websocket('/<address>/dapps')
@openapi.tag("Portfolio")
@openapi.summary("Get the list of dapps that the wallet uses")
@openapi.parameter(name="chain", description="Chain ID. If not set, return data in all chains.", schema=str, location="query")
@openapi.parameter(name="address", description="Wallet address", schema=str, location="path", required=True)
@validate(query=DAppsQuery)
async def get_dapps(request, ws: Websocket, address, query: DAppsQuery):
    jwt = await ws.recv(timeout=5)
    check_token(request, jwt, address)

    start_time = int(time.time())
    chain_id = query.chain
    chains = get_chains(chain_id)
    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    r: Redis = request.app.ctx.redis
    dapps = CacheDApps.get_dapps(r, db, chains)
    block_number_24h_ago = CacheDApps.block_number_24h_ago(r, chains)

    job = AsyncDappsJob(ws, db=db, wallet_address=address, dapps=dapps)
    await job.run(block_number_24h_ago)
    logger.info(f'End request {request.id} {round(time.time() - start_time, 3)}s')


@dapps_bp.get('/<address>/dapp/<dapp_id>/<token_id>')
@openapi.tag("Portfolio")
@openapi.summary("Get dapp token balance change logs of the wallet.")
@openapi.parameter(name="duration", description="Duration to return balance history. Default: 30 days.", schema=int, location="query")
@openapi.parameter(name="chain", description="Chain ID. If not set, return data in all chains.", schema=str, location="query")
@openapi.parameter(name="action", description="Action (deposit/borrow). Default: deposit.", schema=str, location="query")
@openapi.parameter(name="token_id", description="Token ID", schema=str, location="path", required=True)
@openapi.parameter(name="dapp_id", description="DApp ID", schema=str, location="path", required=True)
@openapi.parameter(name="address", description="Wallet address", schema=str, location="path", required=True)
@openapi.secured('Authorization')
@protected
@validate(query=DAppLendingBalanceQuery)
async def get_dapp_token_balance(request, address, dapp_id, token_id, query: DAppLendingBalanceQuery):
    duration = query.duration
    chain_id = query.chain
    action = query.action

    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db

    pool_addresses = get_pools(db, dapp_id)
    wallets = db.get_wallet_by_address(address, chain_id=chain_id, projection=['chainId', 'lendings'])

    tokens_cursor = list(db.get_token_by_id_coingecko(token_id, chain_id=chain_id, projection=['address', 'chainId']))
    tokens = {}
    for t in tokens_cursor:
        chain = t['chainId']
        if chain not in tokens:
            tokens[chain] = []
        tokens[chain].append(t['address'])

    current_time = int(time.time())
    balance_logs = []
    for wallet in wallets:
        balance_logs_ = get_balance_logs(
            wallet=wallet, pool_addresses=pool_addresses, action=action,
            tokens=tokens, current_time=current_time, duration=duration
        )
        balance_logs.extend(balance_logs_)

    token_change_logs = combined_logs(*balance_logs, handler_func=combined_token_change_logs_func, default_value=None)
    return json({
        'address': address,
        'dappId': dapp_id,
        'tokenId': token_id,
        'action': action,
        'dappTokenBalanceHistory': token_change_logs
    })


def get_pools(db: Union[MongoDB, KLGDatabase], dapp_id):
    pool_address = dapp_id.split('_')[-1]
    contract = db.get_contract_by_key(key=dapp_id, projection=['lendingInfo'])
    if not contract:
        raise BadRequest('Invalid DApp')

    lending_info = contract.get('lendingInfo') or {}
    lending_fork = lending_info.get('lendingFork')
    if lending_fork == 'comptroller_pool':
        pool_addresses = [t['vToken'] for t in lending_info['reservesList'].values()]
    else:
        pool_addresses = [pool_address]

    return pool_addresses


def get_balance_logs(wallet, pool_addresses, action, tokens, current_time, duration):
    chain = wallet['chainId']
    lendings = wallet.get('lendings') or {}
    balance_logs = []
    for lending_key, lending in lendings.items():
        if lending_key not in pool_addresses:
            continue

        token_change_logs = lending.get(f'{action}TokenChangeLogs', {})

        token_addresses = tokens.get(chain, [])
        for token_address in token_addresses:
            token_change_log = sort_log(token_change_logs.get(token_address, {}))
            if not token_change_log:
                continue

            token_change_log = coordinate_logs(
                token_change_log, start_time=current_time - duration,
                frequency=int(duration / 100), fill_start_value=True, default_start_value=None
            )
            balance_logs.append(token_change_log)

    return balance_logs
