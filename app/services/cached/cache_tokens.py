from typing import List, Union

from redis import Redis

from app.constants.network_constants import Chain
from app.constants.time_constants import TimeConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.services.artifacts.tokens import bsc_top_tokens
from app.services.cached.constants import CachedKeys
from app.services.cached.redis_cached import RedisCached
from app.utils.logger_utils import get_logger

logger = get_logger('Cache Tokens')

hard_top_tokens = {
    Chain.BSC: {f'{t["chain_id"]}_{t["address"]}': True for t in bsc_top_tokens}
}


class CacheTokens(RedisCached):
    @classmethod
    def get_top_tokens_by_chain(cls, r: Redis, db: Union[MongoDB, KLGDatabase], chains: List[str]):
        tokens_by_chain = cls.get_cache(r, CachedKeys.top_tokens_by_chain)

        # Check if cache miss
        if not tokens_by_chain:
            all_chains = Chain().get_all_chain_id()

            # Get all tokens and filter by chain
            keys = set()
            for chain in all_chains:
                top_tokens_config = db.get_config(f'top_tokens_{chain}')
                if not top_tokens_config or not top_tokens_config.get('tokens'):
                    keys_ = cls.get_top_tokens([chain], db)
                else:
                    keys_ = [f'{chain}_{t["address"]}' for t in top_tokens_config['tokens']]
                keys.update(keys_)

            # Get information of top tokens
            projection = [
                'idCoingecko', 'name', 'symbol', 'decimals', 'chainId', 'address',
                'imgUrl', 'tokenHealth', 'price', 'priceChangeRate', 'priceChangeLogs'
            ]
            tokens = db.get_contracts_by_keys(list(keys), projection=projection)
            tokens_by_chain = {chain: [] for chain in all_chains}
            for token in tokens:
                chain = token['chainId']
                if chain in tokens_by_chain:
                    tokens_by_chain[chain].append(token)

            # Update cache with ttl 1 hour
            cls.set_cache(r, CachedKeys.top_tokens_by_chain, tokens_by_chain, ttl=TimeConstants.A_HOUR)

        # Filter by chains and return
        tokens_dict = dict(filter(lambda x: x[0] in chains, tokens_by_chain.items()))
        return tokens_dict

    @classmethod
    def get_top_tokens(cls, all_chains, db: Union[MongoDB, KLGDatabase]):
        tokens_cursor = db.get_contracts_by_type('token', projection=['chainId', 'address', 'tokenHealth'])
        tokens = {chain: [] for chain in all_chains}
        for doc in tokens_cursor:
            chain = doc['chainId']
            token_address = doc['address']
            token_key = f'{chain}_{token_address}'
            if (chain in tokens) and doc.get('tokenHealth'):
                tokens[chain].append({'_key': token_key, 'tokenHealth': doc.get('tokenHealth')})

        # Limit top 100 highest-health tokens
        keys = []
        for chain in all_chains:
            hard_tops = hard_top_tokens.get(chain, {})
            keys.extend(list(hard_tops.keys()))

            tokens_ = [t for t in tokens[chain] if t['_key'] not in hard_tops]
            tokens_ = sorted(tokens_, key=lambda x: x['tokenHealth'] or 0, reverse=True)
            tokens_ = tokens_[:100 - len(hard_tops)]
            keys.extend([t['_key'] for t in tokens_])

        return keys
