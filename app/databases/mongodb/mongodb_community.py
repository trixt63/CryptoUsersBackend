from typing import List
import pymongo
from pymongo import MongoClient, UpdateOne
from pymongo.cursor import Cursor

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
        self._lp_tokens_col = self._db['lpTokens']
        self._wallets_col = self._db[wallet_col]
        self._projects_col = self._db[PROJECTS_COL]

        self._deposit_wallets_col = self._db['depositWallets']
        # self._deposit_connections_col = self._db['deposit_connections']
        self._users_social_col = self._db['users']
        self._social_deposit_col = self._db['userSocial_deposit']

        self._groups_col = self._db['groups']

        self._lp_deployers_col = self._db['lpDeployers']
        self._lp_traders_col = self._db['lpTraders']

        self._lending_wallets_col = self._db['lendingWallets']

        self._create_index()

    def _create_index(self):
        if 'wallets_number_of_txs_index_1' not in self._wallets_col.index_information():
            self._wallets_col.create_index([('number_of_txs', 1)], name='wallets_number_of_txs_index_1')

    #######################
    #       Home API      #
    #######################
    def count_projects_by_category(self, category: str):
        _filter = {'category': category}
        return self._projects_col.count_documents(_filter)

    def count_users_by_category(self, category: str):
        """Get number of users for Intro pages"""
        if category == 'Cexes':
            return self._deposit_wallets_col.estimated_document_count()
        elif category == 'Lending':
            logger.info(self._lending_wallets_col.estimated_document_count())
            return self._lending_wallets_col.estimated_document_count()
        elif category == 'Dexes':
            n_deployers = self._lp_deployers_col.estimated_document_count()
            n_traders = self._lp_traders_col.estimated_document_count()
            return n_deployers + n_traders
        return 0

    def get_applications(self, category: str, sort_by=None, reverse=False, skip=None, limit=None, chain=None,):
        """Get top applications for Intro pages"""
        _filter = {'category': category}
        if chain is not None:
            _filter.update({'deployedChains': chain})

        _projection = {
            'name': 1,
            'imgUrl': 1,
            'links': 1,
            'spotVolume': 1,
            'tvl': 1,
            'dexVolume': 1,
            'socialAccounts': 1
        }

        cursor = self._projects_col.find(_filter, projection=_projection)
        cursor = self.get_pagination_statement(cursor, sort_by, reverse, skip, limit)
        return cursor

    #######################
    #     Applications    #
    #######################
    def get_project_users(self, chain_id, project_id, projection=None):
        """Get number of users of project"""
        projection_statement = self.get_projection_statement(projection)
        project_data = self._projects_col.find_one(filter={'_id': project_id})
        if project_data['category'] == 'Cexes':
            return self._get_number_cex_users(chain_id, project_id)
        elif project_data['category'] == 'Dexes':
            return self._get_number_dex_users(project_id)
        elif project_data['category'] == 'Lending':
            return self._get_number_lending_users(project_id)
        else:
            return None

    # Cex application
    def _get_number_cex_users(self, chain_id, project_id):
        # TODO: add chainId
        _filter = {"depositedExchanges": project_id}
        return self._deposit_wallets_col.count_documents(_filter)

    def get_whales_list(self, project_id, chain_id):
        _filter = {"depositedExchanges": project_id}
        deposit_wallets = self._deposit_wallets_col.find(_filter).limit(100000)
        list_deposit_addresses = [deposit_wallet['address'] for deposit_wallet in deposit_wallets]
        users = self._groups_col.find({'Chain': chain_id, 'deposit_wallets': {'$in': list_deposit_addresses}}).limit(25)
        return users

    # Dex applications
    def _get_number_dex_users(self, project_id):
        _filter_trader = {f"tradedLPs.{project_id}": {"$exists": 1}}

        _filter_depoyer = {f"deployedLPs.{project_id}": {"$exists": 1}}
        n_deployers = self._lp_deployers_col.count_documents(_filter_trader)
        n_traders = self._lp_traders_col.count_documents(_filter_trader)
        return {
            "deployers": n_deployers,
            "traders": n_traders
        }

    def get_top_pairs(self, project_id, limit=25):
        _filter = {'dex': project_id}
        _projection = {'factory': 0, 'dex': 0, 'pairId': 0}
        _sort = ("pairBalanceInUSD", -1)
        cursor = self._lp_tokens_col.find(filter=_filter, projection=_projection).sort(*_sort).limit(limit)
        return cursor

    def get_dex_pair(self, chain_id, address):
        cursor = self._lp_tokens_col.find_one(filter={'_id': f"{chain_id}_{address}"})
        return cursor

    def get_number_pair_traders(self, chain_id, project_id, pair_address):
        # _filter = {f'tradedLPs.'}
        _filter = {f"tradedLPs.{project_id}": {'chainId': chain_id, 'address': pair_address}}
        n_traders = self._lp_traders_col.count_documents(_filter)
        return n_traders

    # Lending pools
    def _get_number_lending_users(self, project_id):
        _filter = {f"lendingPools.{project_id}": {"$exists": 1}}
        return self._lending_wallets_col.count_documents(_filter)

    # Sample top wallets
    def get_sample_dex_traders_wallets(self, chain_id, project_id):
        _filter = {f"lpTraded.{project_id}": {"$exists": 1}}
        cursor = self._lp_traders_col.find(_filter).limit(25)
        return cursor

    def get_sample_lending_wallets(self, chain_id, project_id):
        _filter = {f"lendingPools.{project_id}": {"$exists": 1}}
        cursor = self._lending_wallets_col.find(_filter).limit(25)
        return cursor

    def get_sample_traders_wallets(self, project_id, chain_id):
        # _filter = {f"tradedLPs.{project_id}.chainId" : chain_id}
        # cursor = self._lp_traders_col.find(_filter).limit(25)
        _filter = {f"tradedLPs.{project_id}": {"$exists": 1}}
        cursor = self._lp_traders_col.find(_filter).limit(25)
        return cursor

    def get_sample_pair_traders_wallets(self, project_id, chain_id, pair_address):
        _filter = {f"tradedLPs.{project_id}": {'chainId': chain_id, 'address': pair_address}}
        cursor = self._lp_traders_col.find(_filter).limit(25)
        return cursor

    #######################
    #   Analysis Purpose  #
    #######################
    def count_wallets(self, _filter):
        _count = self._wallets_col.count_documents(_filter)
        return _count

    def count_wallets_each_chain(self, field_id, project_id, chain_id='0x38'):
        """Count number of wallets of each project on each chain"""
        _filter = {f"{field_id}.{project_id}": {"$exists": 1}}
        _projection = {f"{field_id}.{project_id}": 1}
        deployments = self._wallets_col.find(_filter, _projection)
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
        _count = self._wallets_col.count_documents(_filter)
        return _count
    # end analysis #############

    # for LP pair
    def get_latest_pair_id(self, chain_id: str):
        filter_ = {'chainId': chain_id}
        try:
            latest_pair = self._lp_tokens_col.find_one(filter_, sort=[("pairId", pymongo.DESCENDING)])
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
        cursor = self._lp_tokens_col.find(filter_)
        return cursor

    #######################
    #       Common        #
    #######################
    @staticmethod
    def get_pagination_statement(cursor: Cursor, sort_by=None, reverse: bool = False, skip: int = 0, limit: int = None):
        if sort_by is not None:
            cursor = cursor.sort(sort_by, -1 if reverse else 1)
        if skip is not None:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)
        return cursor

    @staticmethod
    def get_projection_statement(projection: list = None):
        if projection is None:
            return None

        projection_statements = {}
        for field in projection:
            projection_statements[field] = True

        return projection_statements
