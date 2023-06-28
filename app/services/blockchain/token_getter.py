from app.services.artifacts.abis.erc20_abi import ERC20_ABI
from app.services.blockchain.protocols.base_getter import BaseGetter
from app.services.blockchain.batch_queries_services import add_rpc_call


class TokenGetter(BaseGetter):
    def __init__(self, chain_id, pool_address, token_db, provider_uri=None, contribute=False):
        super().__init__(chain_id, pool_address, token_db, provider_uri)

        self.contribute = contribute

    def get_wallet_state_calls(self, wallet_address, block_number='latest', list_rpc_call=None, list_call_id=None):
        if list_rpc_call is None:
            list_rpc_call = []
        if list_call_id is None:
            list_call_id = []

        add_rpc_call(
            abi=ERC20_ABI, contract_address=self.pool_address, fn_name="balanceOf", block_number=block_number,
            fn_paras=wallet_address, list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        add_rpc_call(
            abi=ERC20_ABI, contract_address=self.pool_address, fn_name="decimals", block_number=block_number,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        if self.contribute:
            add_rpc_call(
                abi=ERC20_ABI, contract_address=self.pool_address, fn_name="totalSupply", block_number=block_number,
                list_call_id=list_call_id, list_rpc_call=list_rpc_call
            )
        return list_rpc_call, list_call_id

    def get_wallet_state_by_decoded_response(self, decoded_response, wallet_address, block_number='latest'):
        get_decimals_id = f"decimals_{self.pool_address}_{block_number}".lower()
        get_balance_id = f"balanceOf_{self.pool_address}_{wallet_address}_{block_number}".lower()

        decimals = decoded_response.get(get_decimals_id)
        balance = decoded_response.get(get_balance_id) / 10 ** decimals

        token_prices = self.token_db.get_token_price(addresses=[self.pool_address])
        data = {
            "balance": balance,
            "value": balance * token_prices.get(self.pool_address, 0)
        }

        if self.contribute:
            get_supply_id = f"totalSupply_{self.pool_address}_{block_number}".lower()
            supply = decoded_response.get(get_supply_id) / 10 ** decimals
            data["contribute"] = balance / supply

        return data
