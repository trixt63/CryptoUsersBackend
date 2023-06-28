import logging
import time
from typing import Dict

from multithread_processing.base_job import BaseJob

from app.constants.network_constants import ProviderURI
from app.constants.search_constants import SearchConstants
from app.services.state_service import StateService
from app.utils.logger_utils import get_logger

logger = get_logger('Multithread Tokens Job')


class MultithreadTokensJob(BaseJob):
    def __init__(self, wallet_address, tokens, batch_size=100, bc_services: Dict[str, StateService] = None, log_progress=False):
        self.wallet_address = wallet_address
        self.query_batch_size = batch_size
        self.chains = list(tokens.keys())

        self.bc_services = bc_services
        self._convert_tokens_format(tokens)

        self._setup_log(log_progress)

        work_iterable = self._get_work_iterable(tokens)
        super().__init__(work_iterable=work_iterable, batch_size=1, max_workers=len(tokens))

    def _get_work_iterable(self, tokens: Dict[str, list]):
        work_iterable = []
        for chain_id, tokens_list in tokens.items():
            for idx in range(0, len(tokens_list), self.query_batch_size):
                work_iterable.append({'chain': chain_id, 'tokens_list': tokens_list[idx:idx + self.query_batch_size]})
        return work_iterable

    def _convert_tokens_format(self, tokens):
        self.tokens = {}
        for chain_id, tokens_list in tokens.items():
            self.tokens.update({f"{t['chainId']}_{t['address']}": t for t in tokens_list})

    @classmethod
    def _setup_log(cls, log_progress=False):
        if not log_progress:
            logging.getLogger('ProgressLogger').setLevel(logging.WARNING)
            logging.getLogger('BatchWorkExecutor').setLevel(logging.WARNING)

    def _start(self):
        self.start_time = time.time()
        if self.bc_services is None:
            self.bc_services = {}

        for chain in self.chains:
            if chain not in self.bc_services:
                self.bc_services[chain] = StateService(ProviderURI.mapping[chain])

        self._data = {}
        self._chains = {}

    def _end(self):
        self.batch_executor.shutdown()

    def get_assets(self):
        assets = list(self._data.values())
        assets = sorted(assets, key=lambda x: x['valueInUSD'], reverse=True)
        return assets

    def get_chains(self):
        return list(self._chains.keys())

    def _execute_batch(self, works):
        for work in works:
            chain_id = work['chain']
            tokens_list = work['tokens_list']

            service = self.bc_services.get(chain_id)
            if not service:
                continue

            tokens_balance = service.batch_balance_of(self.wallet_address, tokens_list)
            if tokens_balance:
                self._export(chain_id, tokens_balance)

    def _export(self, chain_id, tokens_balance):
        self._chains[chain_id] = True

        for token_address, amount in tokens_balance.items():
            token = self.tokens[f'{chain_id}_{token_address}']
            token_id = token['idCoingecko']
            token_price = token.get('price') or 0
            if token_id not in self._data:
                self._data[token_id] = {
                    'id': token_id,
                    'type': SearchConstants.token,
                    'name': token['name'],
                    'symbol': token['symbol'],
                    'imgUrl': token['imgUrl'],
                    'amount': 0,
                    'valueInUSD': 0
                }

            self._data[token_id]['amount'] += amount
            self._data[token_id]['valueInUSD'] += amount * token_price
