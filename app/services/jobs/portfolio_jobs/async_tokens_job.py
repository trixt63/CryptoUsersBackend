import json
import logging
import time
from typing import Dict

import asyncio
from sanic import Websocket

from app.constants.network_constants import ProviderURI
from app.constants.time_constants import TimeConstants
from app.services.state_service import StateService
from app.utils.list_dict_utils import sort_log, coordinate_logs
from app.utils.logger_utils import get_logger

logger = get_logger("Async Tokens Job")


class AsyncTokensJob:
    def __init__(self, ws: Websocket, wallet_address, wallets, tokens, batch_size=100, bc_services: Dict[str, StateService] = None, log_progress=False):
        self.ws = ws

        self.wallet_address = wallet_address
        self.wallets = wallets

        self.query_batch_size = batch_size
        self.chains = list(tokens.keys())

        self.bc_services = self._get_bc_services(bc_services)
        self.tokens = tokens
        self.tokens_dict = self._convert_tokens_format(tokens)

        self.new_wallets = {}

        self.start_time = None
        self._setup_log(log_progress)

    def _get_bc_services(self, bc_services):
        if bc_services is None:
            bc_services = {}

        for chain in self.chains:
            if chain not in bc_services:
                bc_services[chain] = StateService(ProviderURI.mapping[chain])
        return bc_services

    @classmethod
    def _convert_tokens_format(cls, tokens):
        tokens_dict = {}
        for chain_id, tokens_list in tokens.items():
            tokens_dict.update({f"{t['chainId']}_{t['address']}": t for t in tokens_list})
        return tokens_dict

    @classmethod
    def _setup_log(cls, log_progress=False):
        if not log_progress:
            logging.getLogger('ProgressLogger').setLevel(logging.WARNING)
            logging.getLogger('BatchWorkExecutor').setLevel(logging.WARNING)

    async def run(self):
        self.start_time = int(time.time())
        tasks = []
        for chain_id, tokens_list in self.tokens.items():
            task = asyncio.create_task(self.task(chain_id, tokens_list))
            tasks.append(task)

        for task in tasks:
            await task

        await self._export_new_wallets()
        return [key for key, is_new in self.new_wallets.items() if is_new]

    async def task(self, chain_id, tokens_list):
        service = self.bc_services.get(chain_id)
        if not service:
            return

        for idx in range(0, len(tokens_list), self.query_batch_size):
            sub_tokens_list = tokens_list[idx:idx + self.query_batch_size]
            for token in sub_tokens_list:
                if token.get('decimals') is None:
                    token['decimals'] = 18
            tokens_balance = service.batch_balance_of(self.wallet_address, sub_tokens_list)
            if tokens_balance:
                wallet = self.wallets.get(chain_id)
                if (not wallet) or (not wallet.get('elite')):
                    self.new_wallets[f'{chain_id}_{self.wallet_address}'] = True
                else:
                    self.new_wallets[f'{chain_id}_{self.wallet_address}'] = False
                await self._export(chain_id, tokens_balance)

    async def _export(self, chain_id, tokens_balance):
        data = []
        current_time = int(time.time())
        for token_address, amount in tokens_balance.items():
            token = self.tokens_dict[f'{chain_id}_{token_address}']

            token_price = token.get('price') or 0

            price_change_logs = sort_log(token.get('priceChangeLogs') or {})
            price_change_logs = coordinate_logs(
                price_change_logs, start_time=current_time - TimeConstants.DAYS_7, end_time=current_time)

            balance = {
                'id': token['idCoingecko'],
                'type': 'token',
                'name': token['name'],
                'symbol': token['symbol'],
                'chains': [chain_id],
                'imgUrl': token['imgUrl'],
                'tokenHealth': token.get('tokenHealth'),
                'amount': amount,
                'valueInUSD': amount * token_price,
                'price': token.get('price'),
                'priceChangeRate': token.get('priceChangeRate'),
                'priceLast7Days': price_change_logs
            }
            data.append(balance)

        message = {
            'address': self.wallet_address,
            'numberOfTokens': len(data),
            'tokens': data
        }
        msg = json.dumps(message)

        await self.ws.send(msg)
        await asyncio.sleep(0.01)

    async def _export_new_wallets(self):
        is_new = all(list(self.new_wallets.values())) if self.new_wallets else False
        if is_new:
            message = {
                'address': self.wallet_address,
                'newWallet': True,
                'numberOfTokens': 0,
                'tokens': []
            }
            msg = json.dumps(message)
            await self.ws.send(msg)
