from typing import List, Union

from web3 import Web3, HTTPProvider
from redis import Redis

from app.constants.network_constants import Chain, EMPTY_TOKEN_IMG, ProviderURI
from app.constants.time_constants import TimeConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.services.artifacts.lending_pool_info import LendingPoolInfo
from app.services.cached.constants import CachedKeys
from app.services.cached.redis_cached import RedisCached
from app.utils.logger_utils import get_logger

logger = get_logger('Cache DApps')


class CacheDApps(RedisCached):
    dapps_file = 'app/services/dapp_info/dapps.json'

    @classmethod
    def get_dapps(cls, r: Redis, db: Union[MongoDB, KLGDatabase], chains: List[str]):
        dapps = cls.get_cache(r, CachedKeys.dapp_protocols)

        # Check if cache miss
        if not dapps:
            dapps = cls.get_protocols(db)

            # Update cache with ttl 1 hour
            cls.set_cache(r, CachedKeys.dapp_protocols, dapps, ttl=TimeConstants.A_HOUR)

        dapps = dict(filter(lambda x: x[1]['chainId'] in chains, dapps.items()))
        return dapps

    @classmethod
    def get_protocols(cls, db: Union[MongoDB, KLGDatabase]):
        dapp_keys = []
        for chain_id, dapps in LendingPoolInfo.mapper.items():
            for dapp_address, dapp in dapps.items():
                dapp_keys.append(f'{chain_id}_{dapp_address}')

        cursor = db.get_contracts_by_keys(keys=dapp_keys, projection=['address', 'chainId', 'name', 'lendingInfo', 'imgUrl'])

        token_keys = {}
        protocols = {}
        for contract in cursor:
            chain_id = contract['chainId']
            address = contract['address']
            key = f'{chain_id}_{address}'

            lending_info = contract.get('lendingInfo') or {}
            reserves_list = lending_info.get('reservesList', {})

            for token_address in reserves_list:
                token_keys[f'{chain_id}_{token_address}'] = True

            protocols[key] = {
                'name': f'{contract["name"]} {Chain.chain_names[chain_id].upper()}',
                'address': address,
                'chainId': chain_id,
                'imgUrl': contract.get('imgUrl') or EMPTY_TOKEN_IMG,
                'safetyIndex': lending_info.get('safetyIndex'),
                'reservesList': reserves_list
            }

        projection = [
            'idCoingecko', 'name', 'symbol', 'decimals', 'chainId', 'address',
            'imgUrl', 'tokenHealth', 'price', 'priceChangeRate', 'priceChangeLogs'
        ]
        tokens = db.get_contracts_by_keys(list(token_keys.keys()), projection=projection)
        tokens = {f"{t['chainId']}_{t['address']}": t for t in tokens}

        for key, protocol in protocols.items():
            reserves_list = protocol.pop('reservesList', {})
            reserves = {}
            for token_address, reserve_data in reserves_list.items():
                token = tokens.get(f'{protocol["chainId"]}_{token_address}')
                if token:
                    reserve_data.update(token)
                    reserves[token_address] = reserve_data
            protocol['tokens'] = reserves

        return protocols

    @classmethod
    def block_number_24h_ago(cls, r: Redis, chains):
        blocks_number_24h_ago = cls.get_cache(r, CachedKeys.blocks_number_24h_ago)
        if not blocks_number_24h_ago:
            blocks_number_24h_ago = {}
            chains = Chain().get_all_chain_id()
            for chain in chains:
                provider_uri = ProviderURI.mapping[chain]
                w3 = Web3(HTTPProvider(provider_uri))
                last_block = w3.eth.block_number
                blocks_number_24h_ago[chain] = int(last_block - TimeConstants.A_DAY / Chain.estimate_block_time[chain])

            cls.set_cache(r, CachedKeys.blocks_number_24h_ago, blocks_number_24h_ago, ttl=TimeConstants.A_HOUR)

        blocks_number_24h_ago = dict(filter(lambda x: x[0] in chains, blocks_number_24h_ago.items()))
        return blocks_number_24h_ago
