from typing import List

import pymongo
from pymongo import MongoClient, UpdateOne

from config import MongoDBCommunityConfig
# from constants.mongodb_constants import WALLETS_COL, CreatedPairEventsCollection
from app.utils.logger_utils import get_logger

logger = get_logger('MongoDB Community')
WALLETS_COL = 'test_lpTraders'
PROJECTS_COL = 'projects'


class MongoDBCommunity:
    def __init__(self, connection_url=None, wallet_col=WALLETS_COL):
        if not connection_url:
            connection_url = MongoDBCommunityConfig.CONNECTION_URL

        self.connection_url = connection_url.split('@')[-1]
        self.connection = MongoClient(connection_url)

        self._db = self.connection[MongoDBCommunityConfig.DATABASE]
        self.lp_tokens_col = self._db['lpTokens']
        self.wallets_col = self._db[wallet_col]
        self.projects_col = self._db[PROJECTS_COL]

        self._deposit_connections_col = self._db['deposit_connections']

        self._lp_deployers_col = self._db['lpDeployers']
        self._lp_traders_col = self._db['lpTraders']

        self._lending_wallets_col = self._db['lendingWallets']

        self._create_index()

    def _create_index(self):
        if 'wallets_number_of_txs_index_1' not in self.wallets_col.index_information():
            self.wallets_col.create_index([('number_of_txs', 1)], name='wallets_number_of_txs_index_1')

    # Home API
    def count_projects_by_category(self, category: str):
        _filter = {'category': category}
        return self.projects_col.count_documents(_filter)

    def count_cex_users(self):
        return self._deposit_connections_col.estimated_document_count()

    def count_dex_users(self):
        n_deployers = self._lp_deployers_col.estimated_document_count()
        n_traders = self._lp_traders_col.estimated_document_count()
        return n_deployers + n_traders

    def count_lending_users(self):
        return self._lending_wallets_col.estimated_document_count()

    # The next 3 functions are for analysis purpose ###
    def count_wallets(self, _filter):
        _count = self.wallets_col.count_documents(_filter)
        return _count

    def count_wallets_each_chain(self, field_id, project_id, chain_id='0x38'):
        """Count number of wallets of each project on each chain"""
        _filter = {f"{field_id}.{project_id}": {"$exists": 1}}
        _projection = {f"{field_id}.{project_id}": 1}
        deployments = self.wallets_col.find(_filter, _projection)
        _count = 0
        for _depl in deployments:
            for project in _depl[field_id][project_id]:
                if project['chainId'] == chain_id:
                    _count += 1
                    continue
        return _count

    def count_exchange_deposit_wallets_each_chain(self, field_id, project_id, chain_id='0x38'):
        """Each CEX project stores a list of chain_ids, instead a list of objects like other type of project,
        so I need a separate function to handle this"""
        _filter = {f"{field_id}.{project_id}": chain_id}
        _count = self.wallets_col.count_documents(_filter)
        return _count
    # end analysis #############

    # for LP pair
    def get_latest_pair_id(self, chain_id: str):
        filter_ = {'chainId': chain_id}
        try:
            latest_pair = self.lp_tokens_col.find_one(filter_, sort=[("pairId", pymongo.DESCENDING)])
            return latest_pair.get('pairId')
        except AttributeError as attr_e:
            logger.warning(f"Cannot get latest pairId from {chain_id}")
        return None

    def get_lps_by_pair_ids(self, chain_id, start_pair_id, end_pair_id):
        filter_ = {
            'chainId': chain_id,
            'pairId': {
                '$gte': start_pair_id,
                '$lt': end_pair_id
            }
        }
        cursor = self.lp_tokens_col.find(filter_)
        return cursor
