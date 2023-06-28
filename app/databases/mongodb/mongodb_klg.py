import sys

from pymongo import MongoClient, UpdateOne
from pymongo.cursor import Cursor

from app.constants.mongo_constants import MongoDBCollections
from app.constants.network_constants import DEFAULT_CREDIT_SCORE
from app.constants.score_constants import WalletCreditScoreWeightConstant
from app.constants.search_constants import SearchConstants
from app.decorators.time_exe import sync_log_time_exe, TimeExeTag
from app.utils.format_utils import about
from app.utils.list_dict_utils import sort_log
from app.utils.logger_utils import get_logger
from app.utils.search_data_utils import get_smart_contract_type
from config import MongoDBConfig

logger = get_logger('MongoDB')


class MongoDB:
    def __init__(self, connection_url=None, database=MongoDBConfig.DATABASE):
        if not connection_url:
            connection_url = MongoDBConfig.CONNECTION_URL

        self.connection_url = connection_url.split('@')[-1]
        try:
            self.connection = MongoClient(connection_url)
            self.mongo_db = self.connection[database]
        except Exception as e:
            logger.exception(f"Failed to connect to ArangoDB: {connection_url}: {e}")
            sys.exit(1)

        self._wallets_col = self.mongo_db[MongoDBCollections.wallets]
        self._multichain_wallets_col = self.mongo_db[MongoDBCollections.multichain_wallets]
        self._projects_col = self.mongo_db[MongoDBCollections.projects]
        self._smart_contracts_col = self.mongo_db[MongoDBCollections.smart_contracts]

        self._multichain_wallets_credit_scores_col = self.mongo_db[MongoDBCollections.multichain_wallets_credit_scores]

        self._abi_col = self.mongo_db[MongoDBCollections.abi]
        self._configs_col = self.mongo_db[MongoDBCollections.configs]
        self._is_part_ofs_col = self.mongo_db[MongoDBCollections.is_part_ofs]

    #######################
    #       Index         #
    #######################

    def _create_index(self):
        ...

    #######################
    #      Project        #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_projects_by_type(self, type_=None, sort_by=None, reverse=False, skip=None, limit=None, chain=None,
                             category=None, last_updated_at=None, projection=None):
        filter_statement = {}
        if type_ is not None:
            filter_statement.update({'sources': type_})
        if chain is not None:
            filter_statement.update({'deployedChains': chain})
        if category is not None:
            filter_statement.update({'category': category})
        # if last_updated_at is not None:
        #     if type_ is not None:
        #         filter_statement.update({f'lastUpdated.{type_}': {'$gt': last_updated_at}})
        #     else:
        #         filter_statement.update({f'lastUpdatedAt': {'$gt': last_updated_at}})
        projection_statement = self.get_projection_statement(projection)

        cursor = self._projects_col.find(filter_statement, projection=projection_statement, batch_size=1000)
        cursor = self.get_pagination_statement(cursor, sort_by, reverse, skip, limit)
        return cursor

    @sync_log_time_exe(tag=TimeExeTag.database)
    def count_projects_by_type(self, type_=None, chain=None, category=None, last_updated_at=None):
        filter_statement = {}
        if type_ is not None:
            filter_statement.update({'sources': type_})
        if chain is not None:
            filter_statement.update({'deployedChains': chain})
        if category is not None:
            filter_statement.update({'category': category})
        # if last_updated_at is not None:
        #     if type_ is not None:
        #         filter_statement.update({f'lastUpdated.{type_}': {'$gt': last_updated_at}})
        #     else:
        #         filter_statement.update({f'lastUpdatedAt': {'$gt': last_updated_at}})

        return self._projects_col.count_documents(filter_statement)

    def get_project(self, project_id, projection=None):
        projection_statement = self.get_projection_statement(projection)
        return self._projects_col.find_one({'_id': project_id}, projection=projection_statement)

    #######################
    #      Contract       #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contracts_by_type(self, type_=None, chain_id=None, sort_by=None, reverse=False, skip=None, limit=None,
                              projection=None, last_updated_at=None, batch_size=10000):
        filter_statement = {}
        if type_ is not None:
            if type_ == 'token':
                filter_statement.update({'idCoingecko': {'$exists': True}})
            else:
                filter_statement.update({'tags': type_})
        if chain_id is not None:
            filter_statement.update({'chainId': chain_id})
        if last_updated_at is not None:
            if type_ is not None:
                filter_statement.update({f'lastUpdated.{type_}': {'$gt': last_updated_at}})
            else:
                filter_statement.update({f'lastUpdatedAt': {'$gt': last_updated_at}})

        projection_statement = self.get_projection_statement(projection)

        cursor = self._smart_contracts_col.find(filter_statement, projection=projection_statement, batch_size=batch_size)
        cursor = self.get_pagination_statement(cursor, sort_by, reverse, skip, limit)
        return cursor

    @sync_log_time_exe(tag=TimeExeTag.database)
    def count_contracts_by_type(self, type_=None, last_updated_at=None):
        filter_statement = {}
        if type_ is not None:
            if type_ == 'token':
                filter_statement.update({'idCoingecko': {'$exists': True}})
            else:
                filter_statement.update({'tags': type_})
        if last_updated_at is not None:
            if type_ is not None:
                filter_statement.update({f'lastUpdated.{type_}': {'$gt': last_updated_at}})
            else:
                filter_statement.update({f'lastUpdatedAt': {'$gt': last_updated_at}})

        return self._smart_contracts_col.count_documents(filter_statement)

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contracts_by_keys(self, keys, projection=None):
        filter_statement = {'_id': {'$in': keys}}
        projection_statement = self.get_projection_statement(projection)
        cursor = self._smart_contracts_col.find(filter_statement, projection=projection_statement, batch_size=1000)
        return cursor

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contract_by_key(self, key, projection=None):
        projection_statement = self.get_projection_statement(projection)
        return self._smart_contracts_col.find_one({'_id': key}, projection=projection_statement)

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_protocols(self, projection=None):
        filter_statement = {'lendingInfo': {'$exists': True}}
        projection_statement = self.get_projection_statement(projection)
        cursor = self._smart_contracts_col.find(filter_statement, projection=projection_statement, batch_size=1000)
        return cursor

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contracts_by_address(self, address, chains=None, projection=None):
        if chains is not None:
            keys = [f'{chain}_{address}' for chain in chains]
            filter_statement = {'_id': {'$in': keys}}
        else:
            filter_statement = {'address': address}

        projection_statement = self.get_projection_statement(projection)
        cursor = self._smart_contracts_col.find(filter_statement, projection=projection_statement)
        return cursor

    #######################
    #       Token         #
    #######################

    def get_token_by_id_coingecko(self, coin_id, chain_id=None, projection=None):
        filter_statement = {'idCoingecko': coin_id}
        if chain_id is not None:
            filter_statement.update({'chainId': chain_id})
        projection_statement = self.get_projection_statement(projection)
        cursor = self._smart_contracts_col.find(filter_statement, projection=projection_statement)
        return cursor

    def get_tokens_by_id(self, token_id, chains, projection=None):
        filter_statement = {}
        chain_id = token_id.split('_')[0]
        if chain_id in chains:
            filter_statement.update({'_id': token_id})
        else:
            filter_statement.update({'idCoingecko': token_id, 'chainId': {'$in': chains}})

        if (projection is not None) and ('tags' not in projection):
            projection.append('tags')
        projection_statement = self.get_projection_statement(projection)

        cursor = self._smart_contracts_col.find(filter_statement, projection=projection_statement)

        tokens = []
        for doc in cursor:
            contract_type = get_smart_contract_type(doc)
            if contract_type != SearchConstants.token:
                continue
            tokens.append(doc)
        return tokens

    #######################
    #      Wallet         #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_wallet_by_address(self, address, chain_id=None, projection=None):
        filter_statement = {}
        if chain_id:
            filter_statement.update({'_id': f'{chain_id}_{address}'})
        else:
            filter_statement.update({'address': address})
        projection_statement = self.get_projection_statement(projection)
        cursor = self._wallets_col.find(filter_statement, projection=projection_statement)
        return list(cursor)

    def get_elite_wallets(self):
        filter_statement = {'elite': True}
        cursor = self._wallets_col.find(filter_statement, projection=['address'], batch_size=1000)
        return cursor

    def insert_new_wallets(self, new_wallets):
        wallet_operators = []
        config_operators = []
        for key in new_wallets:
            chain_id, address = key.split('_')
            wallet_operators.append(UpdateOne(
                {'_id': key, 'address': address},
                {
                    '_id': key,
                    'address': address,
                    'chainId': chain_id,
                    'newTarget': True
                },
                upsert=True
            ))
            config_operators.append(UpdateOne(
                {'_id': f'wallet_flags_{chain_id}'},
                {'_id': f'wallet_flags_{chain_id}', f'newTarget.{address}': True},
                upsert=True
            ))
        self._wallets_col.bulk_write(wallet_operators)
        self._configs_col.bulk_write(config_operators)

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_wallets(self, keys: list, projection=None):
        filter_statement = {'_id': {'$in': keys}}
        projection_statement = self.get_projection_statement(projection)
        cursor = self._wallets_col.find(filter_statement, projection=projection_statement, batch_size=1000)
        return cursor

    #######################
    #       Scores        #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_score_change_logs(self, address: str):
        filter_statement = {'_id': address}
        projection_statement = self.get_projection_statement(['creditScore', 'creditScoreChangeLogs'])
        doc = self._multichain_wallets_credit_scores_col.find_one(filter_statement, projection=projection_statement)
        if not doc:
            return DEFAULT_CREDIT_SCORE, {}

        credit_score = doc.get('creditScore') or DEFAULT_CREDIT_SCORE
        score_logs = sort_log(doc.get('creditScoreChangeLogs'))
        return credit_score, score_logs

    def get_score_details(self, address):
        filter_statement = {'_id': address}
        projection_statement = self.get_projection_statement(
            ['creditScorex1', 'creditScorex2', 'creditScorex3', 'creditScorex4', 'creditScorex5'])
        doc = self._multichain_wallets_credit_scores_col.find_one(filter_statement, projection=projection_statement)
        if (not doc) or (not doc.get('creditScorex1')):
            return {}

        x1 = WalletCreditScoreWeightConstant.b11 * doc['creditScorex1'][0] + \
            WalletCreditScoreWeightConstant.b12 * doc['creditScorex1'][1]

        x2 = WalletCreditScoreWeightConstant.b21 * doc['creditScorex2'][0] + \
            WalletCreditScoreWeightConstant.b22 * doc['creditScorex2'][1] + \
            WalletCreditScoreWeightConstant.b23 * doc['creditScorex2'][2] + \
            WalletCreditScoreWeightConstant.b24 * doc['creditScorex2'][3] + \
            WalletCreditScoreWeightConstant.b25 * doc['creditScorex2'][4]

        x3 = about(doc['creditScorex3'][0] - (1000 - doc['creditScorex3'][1]))

        x4 = WalletCreditScoreWeightConstant.b41 * doc['creditScorex4'][0]

        x5 = WalletCreditScoreWeightConstant.b51 * doc['creditScorex5'][0] + \
            WalletCreditScoreWeightConstant.b52 * doc['creditScorex5'][1]

        return {
            'assets': x1,
            'transactions': x2,
            'loan': x3,
            'circulatingAssets': x4,
            'trustworthinessAssets': x5
        }

    #######################
    #        ABI          #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_abi(self, abi_names):
        filter_statement = {'_id': {'$in': abi_names}}
        cursor = self._abi_col.find(filter_statement, batch_size=1000)
        return cursor

    #######################
    #       Configs       #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_config(self, key):
        config = self._configs_col.find_one({'_id': key})
        return config

    def get_score_histogram(self):
        config = self.get_config(key='multichain_wallets_scores')
        if not config:
            return {}
        return config['histogram']

    #######################
    #       Common        #
    #######################

    @sync_log_time_exe(TimeExeTag.database)
    def count_documents(self, collection_name):
        return self.mongo_db[collection_name].count_documents(filter={})

    @sync_log_time_exe(TimeExeTag.database)
    def count_documents_of_collection(self, collection_name):
        coll_stats = self.mongo_db.command('collStats', collection_name)
        return coll_stats['count']

    @staticmethod
    def get_projection_statement(projection: list = None):
        if projection is None:
            return None

        projection_statements = {}
        for field in projection:
            projection_statements[field] = True

        return projection_statements

    @staticmethod
    def get_pagination_statement(cursor: Cursor, sort_by=None, reverse: bool = False, skip: int = 0, limit: int = None):
        if sort_by is not None:
            cursor = cursor.sort(sort_by, -1 if reverse else 1)
        if skip is not None:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)
        return cursor

    def get_docs(self, collection, keys: list = None, filter_: dict = None, batch_size=1000,
                 projection=None):  # change filter_ to obj
        projection_statement = self.get_projection_statement(projection)

        filter_statement = {}
        if keys:
            filter_statement["_id"] = {"$in": keys}
        if filter_ is not None:
            filter_statement.update(filter_)

        cursor = self.mongo_db[collection].find(
            filter=filter_statement, projection=projection_statement, batch_size=batch_size)
        return cursor
