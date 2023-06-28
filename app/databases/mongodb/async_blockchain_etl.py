import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

from app.constants.mongodb_events_constants import MongoEventsCollections, TxConstants
from app.constants.network_constants import Chain
from app.decorators.time_exe import sync_log_time_exe, TimeExeTag
from app.utils.logger_utils import get_logger
from config import BlockchainETLConfig

logger = get_logger('Async Blockchain ETL')


class AsyncBlockchainETL:
    def __init__(self, connection_url=None):
        if connection_url is None:
            connection_url = BlockchainETLConfig.CONNECTION_URL

        self.connection_url = connection_url.split('@')[-1]
        self.client = AsyncIOMotorClient(connection_url, server_api=ServerApi('1'))

        self.bnb_db = self.client[BlockchainETLConfig.BNB_DATABASE]
        self.ethereum_db = self.client[BlockchainETLConfig.ETHEREUM_DATABASE]
        self.fantom_db = self.client[BlockchainETLConfig.FANTOM_DATABASE]
        self.polygon_db = self.client[BlockchainETLConfig.POLYGON_DATABASE]

    def _get_collection(self, chain_id, collection_name=MongoEventsCollections.TRANSACTIONS):
        if chain_id == Chain.BSC:
            collection = self.bnb_db[collection_name]
        elif chain_id == Chain.ETH:
            collection = self.ethereum_db[collection_name]
        elif chain_id == Chain.FTM:
            collection = self.fantom_db[collection_name]
        elif chain_id == Chain.POLYGON:
            collection = self.polygon_db[collection_name]
        else:
            raise ValueError(f'Chain {chain_id} is not supported')
        return collection

    @sync_log_time_exe(tag=TimeExeTag.database)
    async def get_transactions_by_address(
            self, chain_id, address, is_contract=False, projection=TxConstants.data,
            start_block=None, start_block_timestamp=None,
            sort_by=TxConstants.block_number, reverse=True, skip=0, limit=None
    ):
        if is_contract:
            _filter = {'to_address': address}
        else:
            _filter = {'$or': [{'from_address': address}, {'to_address': address}]}

        if start_block:
            _filter['block_number'] = {'$gte': start_block}

        if start_block_timestamp:
            _filter['block_timestamp'] = {'$gte': start_block_timestamp}

        collection = self._get_collection(chain_id, MongoEventsCollections.TRANSACTIONS)

        _return = {
            TxConstants.id: False,
        }
        for key in projection:
            _return[key] = True

        direction = pymongo.DESCENDING if reverse else pymongo.ASCENDING
        cursor = collection.find(_filter, _return).sort(sort_by, direction).skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)

        # cursor = cursor.batch_size(100)
        docs = [doc async for doc in cursor.batch_size(100)]
        return docs

    @sync_log_time_exe(tag=TimeExeTag.database)
    async def count_documents_by_address(self, chain_id, address, is_contract=False, start_block=None):
        if is_contract:
            _filter = {'to_address': address}
        else:
            _filter = {'$or': [{'from_address': address}, {'to_address': address}]}

        if start_block:
            _filter['block_number'] = {'$gte': start_block}

        collection = self._get_collection(chain_id, MongoEventsCollections.TRANSACTIONS)
        n_docs = await collection.count_documents(_filter)
        return n_docs
