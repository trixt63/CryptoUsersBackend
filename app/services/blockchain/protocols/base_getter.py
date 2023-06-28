from typing import Tuple, Union

from query_state_lib.client.client_querier import ClientQuerier

from app.constants.network_constants import ProviderURI
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.mongodb_klg import MongoDB
from app.services.blockchain.batch_queries_services import decode_data_response
from app.utils.logger_utils import get_logger

logger = get_logger('Base Getter')


class BaseGetter:
    def __init__(self, chain_id, pool_address, db: Union[MongoDB, KLGDatabase], provider_uri=None, pool_info=None, reserves_list=None, batch_size=100):
        self.chain_id = chain_id
        self.pool_address = pool_address
        self.db = db

        if not provider_uri:
            provider_uri = ProviderURI.mapping[self.chain_id]
        self.client_querier = ClientQuerier(provider_url=provider_uri)

        self.token_addresses = None

        self.pool_info = pool_info
        self.reserves_list = reserves_list

        self.batch_size = batch_size

        self._start()

    def _start(self):
        # Start
        pass

    def get_wallet_state_calls(self, wallet_address, block_number='latest', list_rpc_call=None, list_call_id=None) -> Tuple[list, list]:
        # Get wallet state calls
        pass

    def get_wallet_state_by_decoded_response(self, decoded_response, wallet_address, block_number='latest', **kwargs) -> dict:
        # Get wallet state
        pass

    def request_data(self, list_rpc_call, list_call_id):
        data_response = self.client_querier.sent_batch_to_provider(list_rpc_call, batch_size=self.batch_size)
        decoded_data = decode_data_response(data_response, list_call_id)
        return decoded_data

    def get_wallet_state(self, wallet_address, block_number='latest', **kwargs):
        list_rpc_call, list_call_id = self.get_wallet_state_calls(wallet_address, block_number)
        decoded_data = self.request_data(list_rpc_call, list_call_id)
        data = self.get_wallet_state_by_decoded_response(decoded_data, wallet_address, block_number, **kwargs)
        return data

    def get_token_requests(self, list_rpc_call, list_call_id, wallet_address, token_info, block_number='latest', **kwargs):
        # Get request to query token deposit / borrow balance
        ...

    def get_reward_requests(self, list_rpc_call, list_call_id, wallet_address, block_number='latest', **kwargs):
        # Get request to query reward claimable
        ...

    def decode_token_info(self, decoded_response, wallet_address, token_info, block_number='latest', *args, **kwargs):
        # Get token deposit / borrow balance
        ...

    def decode_reward_info(self, decoded_response, wallet_address, block_number='latest', *args, **kwargs):
        # Get reward claimable
        ...

    def get_token_prices(self, token_prices):
        if token_prices is None:
            token_prices = {}

        token_keys = [f'{self.chain_id}_{address}' for address in self.token_addresses if address not in token_prices]
        if token_keys:
            cursor = self.db.get_contracts_by_keys(keys=token_keys, projection=['address', 'price'])
            token_prices.update({t['address']: t.get('price') or 0 for t in cursor})
        return token_prices
