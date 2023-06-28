from query_state_lib.base.mappers.eth_call_balance_of_mapper import EthCallBalanceOf
from query_state_lib.base.mappers.get_balance_mapper import GetBalance
from query_state_lib.client.client_querier import ClientQuerier
from web3 import Web3
from web3.middleware import geth_poa_middleware

from app.constants.network_constants import BNB
from app.decorators.time_exe import sync_log_time_exe, TimeExeTag
from app.utils.logger_utils import get_logger
from app.services.artifacts.bep20_abi import BEP20_ABI

logger = get_logger('State Service')


class StateService:
    def __init__(self, provider_uri):
        self.provider_uri = provider_uri
        self._w3 = Web3(Web3.HTTPProvider(provider_uri))
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.client_querier = ClientQuerier(provider_url=provider_uri)

    def get_latest_block(self):
        return self._w3.eth.block_number

    def to_checksum(self, address):
        return self._w3.toChecksumAddress(address.lower())

    def balance_of(self, address, token, block_number='latest', decimals=None):
        if token != BNB:
            token_contract = self._w3.eth.contract(self._w3.toChecksumAddress(token), abi=BEP20_ABI)
            if decimals is None:
                decimals = token_contract.functions.decimals().call()
            balance = token_contract.functions.balanceOf(self._w3.toChecksumAddress(address)).call(block_identifier=block_number)
        else:
            balance = self._w3.eth.getBalance(self._w3.toChecksumAddress(address), block_identifier=block_number)
            if decimals is None:
                decimals = 18
        balance = balance / 10 ** decimals
        return token, balance

    def total_supply(self, token_address, block_number='latest'):
        token_contract = self._w3.eth.contract(self._w3.toChecksumAddress(token_address), abi=BEP20_ABI)
        decimals = token_contract.functions.decimals().call()
        total_supply = token_contract.functions.totalSupply().call(block_identifier=block_number) / 10 ** decimals
        return total_supply

    @sync_log_time_exe(tag=TimeExeTag.blockchain)
    def batch_balance_of(self, address, tokens, block_number='latest', batch_size=1000):
        tokens = {token['address'].lower(): token.get('decimals') or 18 for token in tokens}

        rpc_requests = []
        for token in tokens:
            query_id = f'{address}_{token}'
            if token != "0x" and token != BNB:
                call_balance_of = EthCallBalanceOf(
                    contract_address=token,
                    address=address,
                    block_number=block_number,
                    id=query_id
                )
            else:
                call_balance_of = GetBalance(
                    address=address,
                    block_number=block_number,
                    id=query_id
                )
            rpc_requests.append(call_balance_of)

        rpc_responses = self.client_querier.sent_batch_to_provider(rpc_requests, batch_size=batch_size)
        balances = {}
        for token, decimals in tokens.items():
            balance = rpc_responses.get(f'{address}_{token}').result
            balance = balance / 10 ** decimals
            if token == '0x':
                token = BNB
            if balance > 0:
                balances[token] = balance
        return balances
