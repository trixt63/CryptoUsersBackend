import time

from app.constants.mongodb_token_constants import MongoDBTokenConstant
from app.constants.network_constants import BNB
from app.constants.time_constants import TimeConstants
from app.utils.list_dict_utils import sort_log, get_logs_in_time
from app.utils.logger_utils import get_logger
from config import TokenMongoDBConfig

from pymongo import MongoClient

logger = get_logger('MongoDB Token')


class MongoDBToken:
    def __init__(self, graph=None):
        if graph is None:
            graph = TokenMongoDBConfig.CONNECTION_URL

        self.mongo = MongoClient(graph)
        self._db = self.mongo[TokenMongoDBConfig.TOKEN_DATABASE]

        self._tokens_col = self._db[MongoDBTokenConstant.TOKENS_COL]
        self._merged_tokens_col = self._db[MongoDBTokenConstant.MERGED_TOKENS_COL]
        self._token_price_col = self._db[MongoDBTokenConstant.TOKEN_PRICE_COL]
        self._merged_token_price_col = self._db[MongoDBTokenConstant.MERGED_TOKEN_PRICE_COL]

    def get_merged_token_prices(self, token_ids):
        if not token_ids:
            return dict()

        filter_ = {'_id': {'$in': token_ids}}
        cursor = self._merged_token_price_col.find(filter_).batch_size(10000)

        tokens_price = dict()
        for token_price in cursor:
            key = token_price.get("_id")
            tokens_price[key] = token_price
        return tokens_price

    def get_token_price(self, keys=None, addresses=None):
        if keys is not None:
            filter_ = {'_id': {'$in': keys}}
        else:
            filter_ = {'address': {'$in': addresses or []}}

        cursor = self._tokens_col.find(filter_, projection=['address', 'price']).batch_size(1000)

        prices = {}
        for doc in cursor:
            prices[doc['address']] = doc.get('price') or 0
        if '0x' in prices:
            prices[BNB] = prices.pop('0x')
        return prices

    def get_token_price_change_logs(self, keys=None, addresses=None, start_time=None):
        if keys is None:
            filter_ = {'_id': {'$in': [f"0x38_{address}" for address in addresses] if addresses else []}}
        else:
            filter_ = {'_id': {'$in': keys}}

        cursor = self._token_price_col.find(filter_).batch_size(1000)

        prices = {}
        if start_time is None:
            start_time = int(time.time()) - TimeConstants.DAYS_30
        for doc in cursor:
            address = doc['_id'].split('_')[-1]
            price_logs = sort_log(doc.get('priceChangeLogs', {}))
            price_logs = get_logs_in_time(price_logs, start_time=start_time)
            prices[address] = {
                'address': address,
                'price': doc.get('price') or 0,
                'price_change_logs': price_logs
            }
        if '0x' in prices:
            bnb_price_info = prices.pop('0x')
            bnb_price_info['address'] = BNB
            prices[BNB] = bnb_price_info
        return prices

    def get_token_health_by_keys(self, keys=None):
        filter_ = {}
        if keys is not None:
            filter_ = {'_id': {'$in': keys or []}}
        cursor = self._merged_tokens_col.find(filter_, projection=['tokenId', 'creditScore']).batch_size(1000)
        tokens = {}
        for doc in cursor:
            token_id = doc['tokenId']
            health = doc.get('creditScore') or 0
            tokens[token_id] = health
        return tokens

    def get_token_health(self, coin_id):
        token = self._merged_tokens_col.find_one({'_id': coin_id}, projection=['creditScore'])
        if not token:
            token = self._tokens_col.find_one({'tokenId': coin_id}, projection=['creditScore'])
            if not token:
                return None

        return token.get('creditScore')

    def get_token(self, coin_id):
        token = self._merged_tokens_col.find_one({'_id': coin_id})
        return token
