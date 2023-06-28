import time

from multithread_processing.base_job import BaseJob

from app.databases.mongodb_events import MongoEvents
from app.utils.logger_utils import get_logger

logger = get_logger('Transactions Job')


class TransactionsJob(BaseJob):
    def __init__(
            self, _mongo: MongoEvents, chain_id, address, start_timestamp, end_timestamp,
            period, batch_size, max_workers
    ):
        self._mongo = _mongo

        self.chain_id = chain_id
        self.address = address

        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.period = period
        work_iterable = range(self.start_timestamp, self.end_timestamp, self.period)

        super().__init__(work_iterable, batch_size, max_workers)

    def _start(self):
        self._contract_n_txs = {}

    def _end(self):
        self.batch_executor.shutdown()
        self._contract_n_txs = dict(sorted(self._contract_n_txs.items(), key=lambda x: x[1], reverse=True))
        logger.info(f'There are {len(self._contract_n_txs)} addresses')

    def get_top_users(self):
        return self._contract_n_txs

    def _execute_batch(self, works):
        start_time = int(time.time())
        start_timestamp = works[0]
        end_timestamp = min(start_timestamp + self.period, self.end_timestamp)
        transactions = self._mongo.get_sort_txs_in_range(
            self.chain_id, start_timestamp=start_timestamp, end_timestamp=end_timestamp)

        address_dict = {}
        for transaction in transactions:
            to_address = transaction.get('to_address')
            if to_address != self.address:
                continue

            from_address = transaction.get('from_address')
            if not address_dict.get(from_address):
                address_dict[from_address] = 0
            address_dict[from_address] += 1

        self._combine_result(address_dict)
        logger.info(f'Combine {len(self._contract_n_txs)} contract addresses, took {round(time.time() - start_time)}s')

    def _combine_result(self, contract_n_txs: dict):
        for address, n_tx in contract_n_txs.items():
            if address not in self._contract_n_txs:
                self._contract_n_txs[address] = 0
            self._contract_n_txs[address] += n_tx
