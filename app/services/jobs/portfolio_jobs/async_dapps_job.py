import asyncio
import json
import logging
import time
from typing import Dict, Union

from sanic import Websocket

from app.constants.contract_constants import ContractConst
from app.constants.network_constants import ProviderURI
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.services.artifacts.lending_pool_info import LendingPoolInfo, LendingFork
from app.services.blockchain.protocols.alpaca_getter import AlpacaGetter
from app.services.blockchain.protocols.comptroller_getter import ComptrollerGetter
from app.services.blockchain.protocols.geist_getter import GeistGetter
from app.services.blockchain.protocols.trava_getter import TravaGetter
from app.services.state_service import StateService
from app.utils.logger_utils import get_logger

logger = get_logger("Async Dapps Job")


class AsyncDappsJob:
    def __init__(self, ws: Websocket, wallet_address, dapps, db: Union[MongoDB, KLGDatabase], batch_size=100, bc_services: Dict[str, StateService] = None, log_progress=False):
        self.ws = ws
        self.db = db

        self.wallet_address = wallet_address
        self.query_batch_size = batch_size

        self.mapper = LendingPoolInfo.mapper
        self.chains = list(self.mapper.keys())
        self.bc_services = self._get_bc_services(bc_services)

        self.dapps = dapps  # {dapp_id: {tokens: [{address: str(), price: float()}]}}

        self.start_time = None
        self._setup_log(log_progress)

    @classmethod
    def _setup_log(cls, log_progress=False):
        if not log_progress:
            logging.getLogger('ProgressLogger').setLevel(logging.WARNING)
            logging.getLogger('BatchWorkExecutor').setLevel(logging.WARNING)

    def _get_bc_services(self, bc_services):
        if bc_services is None:
            bc_services = {}

        for chain in self.chains:
            if chain not in bc_services:
                bc_services[chain] = StateService(ProviderURI.mapping[chain])
        return bc_services

    async def run(self, blocks_number_24h_ago):
        self.start_time = int(time.time())
        tasks = []
        for chain_id, dapps in self.mapper.items():
            task = asyncio.create_task(self.task(chain_id, dapps, blocks_number_24h_ago[chain_id]))
            tasks.append(task)

        for task in tasks:
            await task

    async def task(self, chain_id, dapps, block_number_24h_ago):
        service = self.bc_services.get(chain_id)
        if not service:
            return

        for dapp_address, dapp in dapps.items():
            dapp_info = self.dapps.get(f'{chain_id}_{dapp_address}')

            kwargs = {
                'chain_id': chain_id,
                'pool_address': dapp_address,
                'db': self.db,
                'provider_uri': service.provider_uri,
                'pool_info': dapp,
                'reserves_list': dapp_info['tokens']
            }

            if dapp[ContractConst.lending_fork] == LendingFork.AAVE_POOL:
                getter = TravaGetter(**kwargs)
            elif dapp[ContractConst.lending_fork] == LendingFork.COMPTROLLER_POOL:
                getter = ComptrollerGetter(**kwargs)
            elif dapp[ContractConst.lending_fork] == LendingFork.GEIST_POOL:
                getter = GeistGetter(**kwargs)
            elif dapp[ContractConst.lending_fork] == LendingFork.ALPACA_POOL:
                getter = AlpacaGetter(**kwargs)
            else:
                logger.warning(f'Unsupported protocol type: {dapp[ContractConst.lending_fork]}')
                continue

            token_prices = {t_address: t.get('price') or 0 for t_address, t in dapp_info['tokens'].items()}
            wallet_lending = getter.get_wallet_state(wallet_address=self.wallet_address, token_prices=token_prices)
            if wallet_lending['tvl']:
                wallet_lending['tvl24hAgo'] = getter.get_tvl(self.wallet_address, block_number=block_number_24h_ago)
                await self._export(chain_id, dapp_info, wallet_lending)

    async def _export(self, chain_id, dapp_info, wallet_lending):
        tokens_info = dapp_info['tokens']
        tokens_lending = wallet_lending['tokens']

        tokens = []
        avg_apr = {'value_in_usd': 0, 'apr': 0}
        for token_address, lending in tokens_lending.items():
            token_info = tokens_info[token_address]
            for lending_type, lending_info in lending.items():
                amount = lending_info['amount']
                if amount > 0:
                    price = token_info.get('price') or 0
                    value_in_usd = amount * price
                    token = {
                        'id': token_info['idCoingecko'],
                        'type': 'token',
                        'name': token_info['name'],
                        'symbol': token_info['symbol'],
                        'action': lending_type,
                        'chains': [chain_id],
                        'imgUrl': token_info['imgUrl'],
                        'tokenHealth': token_info.get('tokenHealth'),
                        'amount': amount,
                        'valueInUSD': value_in_usd,
                        'price': token_info.get('price'),
                        'priceChangeRate': token_info.get('priceChangeRate'),
                        'apy': token_info.get(f'{lending_type}Apy'),
                        'apr': token_info.get(f'{lending_type}Apr')
                    }
                    tokens.append(token)

                    if lending_type == 'borrow':
                        avg_apr['value_in_usd'] -= value_in_usd
                        avg_apr['apr'] -= value_in_usd * token.get('apy', 0)
                    else:
                        avg_apr['value_in_usd'] += value_in_usd
                        avg_apr['apr'] += value_in_usd * token.get('apy', 0)
                    avg_apr['apr'] += value_in_usd * token.get('apr', 0)

        dapp = {
            'id': f'{chain_id}_{dapp_info["address"]}',
            'type': 'dapp',
            'name': dapp_info['name'],
            'address': dapp_info['address'],
            'chains': [chain_id],
            'imgUrl': dapp_info['imgUrl'],
            'safetyIndex': dapp_info.get('safetyIndex'),
            'tvl': wallet_lending['tvl'],
            'tvl24hAgo': wallet_lending['tvl24hAgo'],
            'claimable': wallet_lending['claimable'],
            'avgAPR': avg_apr['apr'] / avg_apr['value_in_usd'] if avg_apr['value_in_usd'] else 0,
            'tokens': tokens
        }

        msg = json.dumps({
            'address': self.wallet_address,
            'dapps': [dapp]
        })

        await self.ws.send(msg)
        await asyncio.sleep(0.01)
