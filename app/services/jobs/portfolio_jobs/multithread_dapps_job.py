import logging
import time
from typing import Dict, Union

from multithread_processing.base_job import BaseJob

from app.constants.contract_constants import ContractConst
from app.constants.network_constants import ProviderURI
from app.constants.search_constants import SearchConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.services.artifacts.lending_pool_info import LendingPoolInfo, LendingFork
from app.services.blockchain.protocols.alpaca_getter import AlpacaGetter
from app.services.blockchain.protocols.comptroller_getter import ComptrollerGetter
from app.services.blockchain.protocols.geist_getter import GeistGetter
from app.services.blockchain.protocols.trava_getter import TravaGetter
from app.services.state_service import StateService
from app.utils.logger_utils import get_logger

logger = get_logger('Multithread Dapps Job')


class MultithreadDappsJob(BaseJob):
    def __init__(self, wallet_address, dapps, db: Union[MongoDB, KLGDatabase], batch_size=100, bc_services: Dict[str, StateService] = None, log_progress=False):
        self.db = db

        self.wallet_address = wallet_address
        self.query_batch_size = batch_size

        self.mapper = LendingPoolInfo.mapper
        self.chains = list(self.mapper.keys())
        self.bc_services = bc_services

        self.dapps = dapps

        self._setup_log(log_progress)

        work_iterable = self._get_work_iterable()
        super().__init__(work_iterable=work_iterable, batch_size=1, max_workers=len(dapps))

    def _get_work_iterable(self):
        work_iterable = []
        for chain_id, dapps in self.mapper.items():
            for dapp_address, dapp in dapps.items():
                dapp_info = self.dapps.get(f'{chain_id}_{dapp_address}')
                if not dapp_info:
                    continue
                work_iterable.append({'chain': chain_id, 'address': dapp_address, 'dapp_info': dapp_info, 'dapp': dapp})
        return work_iterable

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

    def _end(self):
        self.batch_executor.shutdown()

    def get_dapps(self):
        dapps = list(self._data.values())
        dapps = sorted(dapps, key=lambda x: x['value'], reverse=True)
        return dapps

    def _execute_batch(self, works):
        for work in works:
            chain_id = work['chain']
            dapp_info = work['dapp_info']
            dapp = work['dapp']

            service = self.bc_services.get(chain_id)
            if not service:
                continue

            kwargs = {
                'chain_id': chain_id,
                'pool_address': work['address'],
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

            tvl = getter.get_tvl(self.wallet_address)
            if tvl:
                self._export(chain_id, dapp_info, tvl)

    def _export(self, chain_id, dapp_info, tvl):
        dapp_id = f'{chain_id}_{dapp_info["address"]}'
        self._data[dapp_id] = {
            'id': dapp_id,
            'type': SearchConstants.contract,
            'name': dapp_info['name'],
            'imgUrl': dapp_info['imgUrl'],
            'value': tvl
        }
