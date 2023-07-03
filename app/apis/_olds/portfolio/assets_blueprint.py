import time
from typing import Union

from redis import Redis
from sanic import Blueprint, Websocket, Request
from sanic import json
from sanic.log import logger
from sanic_ext import openapi, validate

from app.apis._olds.portfolio.utils.utils import check_address, get_chains
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.decorators.auth import protected, check_token
from app.models.portfolio.assets import CreditScoreQuery, TokenBalanceQuery, TokensQuery
from app.services.cached.cache_tokens import CacheTokens
from app.services.jobs.portfolio_jobs.async_tokens_job import AsyncTokensJob
from app.utils.list_dict_utils import sort_log, merge_logs, get_change_rate, combined_logs, \
    get_percentage_on_top, combined_token_change_logs_func, coordinate_logs

assets_bp = Blueprint('assets_blueprint', url_prefix='/')


@assets_bp.get('/<address>/credit-score')
@openapi.tag("Portfolio")
@openapi.summary("Get wallet credit score, history of wallet credit score with balance.")
@openapi.parameter(name="history", description="Whether to return credit score history. Default: False.", schema=bool, location="query")
@openapi.parameter(name="duration", description="Duration to return credit score history. Default: 30 days.", schema=int, location="query")
@openapi.parameter(name="chain", description="Chain ID. If not set, return data in all chains.", schema=str, location="query")
@openapi.parameter(name="address", description="Wallet address", schema=str, location="path", required=True)
@openapi.secured('Authorization')
@protected
@validate(query=CreditScoreQuery)
async def get_credit_score(request: Request, address, query: CreditScoreQuery):
    history = query.history
    duration = query.duration
    chain_id = query.chain

    current_time = int(time.time())
    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    wallets = db.get_wallet_by_address(
        address, chain_id=chain_id,
        projection=['chainId', 'newTarget', 'balanceInUSD', 'balanceChangeLogs']
    )

    # Get balance information
    balance = sum([w.get('balanceInUSD') or 0 for w in wallets])
    balance_change_logs = []
    news = []
    for w in wallets:
        if w.get('newTarget'):
            chain = w['chainId']
            news.append(chain)

        balance_change_logs_ = sort_log(w.get('balanceChangeLogs', {}))
        balance_change_logs_ = coordinate_logs(
            balance_change_logs_, start_time=current_time - duration,
            frequency=int(duration / 100), fill_start_value=True, default_start_value=0
        )
        balance_change_logs.append(balance_change_logs_)
    balance_history = combined_logs(*balance_change_logs)

    # Get balance change rate in duration
    balances = list(balance_history.values())
    if balances:
        balance_change_rate = get_change_rate(balances[0], balances[-1])
    else:
        balance_change_rate = 0

    credit_score, credit_score_history = db.get_score_change_logs(address)
    score_histogram = db.get_score_histogram()
    top_percentage = get_percentage_on_top(credit_score, score_histogram)

    data = {
        'address': address,
        'creditScore': credit_score,
        'topCreditScorePercentage': top_percentage,
        'balance': balance,
        'balanceChangeRate': balance_change_rate
    }

    if news:
        data['newChains'] = news

    if history:
        credit_score_history = coordinate_logs(
            credit_score_history, start_time=current_time - duration,
            frequency=int(duration / 100), fill_start_value=True, default_start_value=0
        )

        data_history = merge_logs({'balance': balance_history, 'creditScore': credit_score_history}, default_value=0)
        data['creditScoreHistory'] = data_history

    return json(data)


@assets_bp.websocket('/<address>/tokens')
@openapi.tag("Portfolio")
@openapi.summary("Get the list of tokens that the wallet holds")
@openapi.parameter(name="chain", description="Chain ID. If not set, return data in all chains.", schema=str, location="query")
@openapi.parameter(name="address", description="Wallet address", schema=str, location="path", required=True)
@validate(query=TokensQuery)
async def get_tokens(request: Request, ws: Websocket, address, query: TokensQuery):
    jwt = await ws.recv(timeout=5)
    check_token(request, jwt, address)

    start_time = int(time.time())
    chain_id = query.chain
    chains = get_chains(chain_id)
    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    wallets = db.get_wallet_by_address(address, chain_id=chain_id, projection=['chainId', 'elite'])
    wallets = {w['chainId']: w for w in wallets}

    r: Redis = request.app.ctx.redis
    tokens_by_chain = CacheTokens.get_top_tokens_by_chain(r, db, chains)

    # Send with jobs
    job = AsyncTokensJob(ws, address, wallets, tokens_by_chain, batch_size=20)
    new_wallets = await job.run()

    if new_wallets:
        db.insert_new_wallets(new_wallets)
    logger.info(f'End request {request.id} {round(time.time() - start_time, 3)}s')


@assets_bp.get('/<address>/tokens/<token_id>')
@openapi.tag("Portfolio")
@openapi.summary("Get token balance change logs of the wallet.")
@openapi.parameter(name="duration", description="Duration to return balance history. Default: 30 days.", schema=int, location="query")
@openapi.parameter(name="chain", description="Chain ID. If not set, return data in all chains.", schema=str, location="query")
@openapi.parameter(name="token_id", description="Token ID", schema=str, location="path", required=True)
@openapi.parameter(name="address", description="Wallet address", schema=str, location="path", required=True)
@openapi.secured('Authorization')
@protected
@validate(query=TokenBalanceQuery)
async def get_token_balance(request, address, token_id, query: TokenBalanceQuery):
    duration = query.duration
    chain_id = query.chain

    address = check_address(address)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    wallets = db.get_wallet_by_address(address, chain_id=chain_id, projection=['chainId', 'tokenChangeLogs'])

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
        chain = wallet['chainId']
        token_change_logs = wallet.get('tokenChangeLogs') or {}

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

    token_change_logs = combined_logs(*balance_logs, handler_func=combined_token_change_logs_func, default_value=None)
    return json({
        'address': address,
        'tokenId': token_id,
        'tokenBalanceHistory': token_change_logs
    })
