import sys

import pymongo
from pymongo import MongoClient

from app.constants.mongodb_events_constants import MongoEventsCollections, MongoIndex, Event
from app.constants.network_constants import Chain
from app.constants.time_constants import TimeConstants
from app.constants.mongodb_events_constants import TxConstants, BlockConstants
from app.utils.logger_utils import get_logger
from config import BlockchainETLConfig

logger = get_logger('Main MongoDB')


class MongoEvents:
    def __init__(self, connection_url=None):
        if connection_url is None:
            connection_url = BlockchainETLConfig.CONNECTION_URL

        self.connection_url = connection_url.split('@')[-1]
        try:
            self.client = MongoClient(connection_url)
            logger.info(f"Connected to MongoDB Main")
        except Exception as ex:
            logger.warning(f"Failed connecting to MongoDB Main")
            logger.exception(ex)
            sys.exit(1)

        self.bnb_db = self.client[BlockchainETLConfig.BNB_DATABASE]
        self.ethereum_db = self.client[BlockchainETLConfig.ETHEREUM_DATABASE]
        self.fantom_db = self.client[BlockchainETLConfig.FANTOM_DATABASE]
        self.polygon_db = self.client[BlockchainETLConfig.POLYGON_DATABASE]

        self._bnb_col = self.bnb_db[MongoEventsCollections.LENDING_EVENTS]
        self._ethereum_col = self.ethereum_db[MongoEventsCollections.LENDING_EVENTS]
        self._fantom_col = self.fantom_db[MongoEventsCollections.LENDING_EVENTS]

    def _create_index(self, database_name, collection_name):
        _db = self.client[database_name]
        _col = _db[collection_name]
        if MongoIndex.ADDRESS_CONFIGS not in _col.index_information():
            _col.create_index([('address', 'hashed')], name=MongoIndex.ADDRESS_CONFIGS)
        logger.info('Indexed !!!')

    def _get_collection(self, chain_id, collection_name=MongoEventsCollections.TRANSACTIONS):
        collection = None
        if chain_id == Chain.BSC:
            collection = self.bnb_db[collection_name]
        elif chain_id == Chain.ETH:
            collection = self.ethereum_db[collection_name]
        elif chain_id == Chain.FTM:
            collection = self.fantom_db[collection_name]
        return collection

    def get_transaction(self, chain_id, transaction_hash):
        _filter = {
            TxConstants.id: f"transaction_{transaction_hash.lower()}"
        }
        _return = {
            TxConstants.id: False,
        }
        for key in TxConstants.data:
            _return[key] = True

        collection = self._get_collection(chain_id)
        if collection:
            return collection.find_one(_filter, _return)

        return None

    def get_transactions_by_block(self, chain_id, block_number):
        tx_collection = self._get_collection(chain_id)
        _filter = {
            "block_number": block_number
        }
        _return = {
            TxConstants.id: False,
        }
        for key in TxConstants.data:
            _return[key] = True

        tx_data = tx_collection.find(_filter)
        if tx_data:
            return tx_data

        return None

    def get_block(self, chain_id, block):
        if not block.isnumeric():
            _filter = {
                "_id": f"block_{block.lower()}"
            }
        else:
            _filter = {
                "number": int(block)
            }

        _return = {
            BlockConstants.id: False
        }
        for key in BlockConstants.data:
            _return[key] = True

        tx_collection, b_collection = None, None
        if chain_id == Chain.BSC:
            tx_collection = self.bnb_db[MongoEventsCollections.TRANSACTIONS]
            b_collection = self.bnb_db[MongoEventsCollections.BLOCKS]

        if chain_id == Chain.ETH:
            tx_collection = self.ethereum_db[MongoEventsCollections.TRANSACTIONS]
            b_collection = self.bnb_db[MongoEventsCollections.BLOCKS]

        if chain_id == Chain.FTM:
            tx_collection = self.fantom_db[MongoEventsCollections.TRANSACTIONS]
            b_collection = self.bnb_db[MongoEventsCollections.BLOCKS]

        if tx_collection and b_collection:
            block_data = b_collection.find_one(_filter, _return)

            return block_data

        return None

    def get_transactions_by_hashes(self, chain_id, hashes: list):
        _filter = {"_id": {'$in': [f'transaction_{tx_hash}' for tx_hash in hashes]}}
        collection = self._get_collection(chain_id)

        _return = {
            TxConstants.id: False,
        }
        for key in TxConstants.data:
            _return[key] = True

        return list(collection.find(_filter, _return))

    def get_transactions_by_pair_address(self, chain_id, from_, to, limit=10):
        # if not time_limit:
        #     time_limit = int(time.time() - 3600*24*30)
        _filter = {
            "from_address": from_.lower(),
            "to_address": to.lower(),
            # "block_timestamp": {"$gte": time_limit}
        }
        collection = self._get_collection(chain_id)

        _return = {
            TxConstants.id: False,
        }
        for key in TxConstants.data:
            _return[key] = True

        return list(collection.find(_filter, _return).sort(TxConstants.block_number, pymongo.DESCENDING).limit(limit))

    def get_event_by_pair_address(self, chain_id, from_, to_, start_block=None, limit=10):
        if not start_block:
            last_synced_block = self.get_last_synced_block(chain_id)
            block_second = 3  # TODO: for bsc
            start_block = last_synced_block - int(TimeConstants.DAYS_30 / block_second)

        _filter = {
            "from": from_.lower(),
            "to": to_.lower(),
            "block_number": {"$gte": start_block}
        }
        collection = self._get_collection(chain_id, MongoEventsCollections.TOKEN_TRANSFERS)

        _return = {
            Event.id: False,
        }
        for key in Event.data:
            _return[key] = True

        return list(collection.find(_filter, _return).sort(Event.block_number, pymongo.DESCENDING).limit(limit))

    def get_last_synced_block(self, chain_id):
        collection = self._get_collection(chain_id, MongoEventsCollections.COLLECTORS)

        collector = collection.find_one({'_id': 'streaming_collector'})
        if collector:
            return collector['last_updated_at_block_number']

    def get_transactions_by_address(self, chain_id, address, is_contract=False, start_block=None,
                                    start_block_timestamp=None, limit=20):
        if is_contract:
            _filter = {'to_address': address}
        else:
            _filter = {'$or': [{'from_address': address}, {'to_address': address}]}

        if start_block:
            _filter['block_number'] = {'$gte': start_block}

        if start_block_timestamp:
            _filter['block_timestamp'] = {'$gte': start_block_timestamp}
        logger.debug(f'Filter: {_filter}')

        collection = self._get_collection(chain_id, MongoEventsCollections.TRANSACTIONS)

        _return = {
            TxConstants.id: False,
        }
        for key in TxConstants.data:
            _return[key] = True

        cursor = collection.find(_filter, _return).sort(TxConstants.block_number, pymongo.DESCENDING).limit(
            limit).batch_size(100)
        return list(cursor)

    def get_latest_transactions(self, chain_id, limit=10):
        collection = self.bnb_db[MongoEventsCollections.TRANSACTIONS]
        if chain_id == Chain.ETH:
            collection = self.ethereum_db[MongoEventsCollections.TRANSACTIONS]

        if chain_id == Chain.FTM:
            collection = self.fantom_db[MongoEventsCollections.TRANSACTIONS]
        _return = {
            TxConstants.id: False,
        }
        for key in TxConstants.data:
            _return[key] = True
        cursor = collection.find({}, _return).sort(TxConstants.block_number, -1).limit(limit)
        return list(cursor)

    def get_transactions_from_address(self, chain_id, from_address=None, to_address=None, start_block=None, start_block_timestamp=None, limit=None):
        _filter = {}
        if from_address is not None:
            _filter['from_address'] = from_address
        if to_address is not None:
            _filter['to_address'] = to_address
        if start_block:
            _filter['block_number'] = {'$gte': start_block}
        if start_block_timestamp:
            _filter['block_timestamp'] = {'$gte': start_block_timestamp}

        collection = self._get_collection(chain_id)

        cursor = collection.find(_filter).sort(TxConstants.block_number, pymongo.DESCENDING)
        if limit is not None:
            cursor = cursor.limit(limit)
        return cursor.batch_size(1000)

    def get_sort_txs_in_range(self, chain_id, start_timestamp, end_timestamp):
        filter_ = {
            'block_timestamp': {
                "$gte": start_timestamp,
                "$lte": end_timestamp
            }
        }
        collection = self._get_collection(chain_id)
        projection = ["from_address", "to_address"]
        cursor = collection.find(filter_, projection).batch_size(10000)
        return cursor

    def get_transactions_between_block(self, chain_id, start_block, end_block):
        filter_ = {
            'block_number': {
                "$gte": start_block,
                "$lte": end_block
            }
        }
        collection = self._get_collection(chain_id)
        projection = ["from_address", "to_address"]
        cursor = collection.find(filter_, projection).batch_size(10000)
        return cursor
