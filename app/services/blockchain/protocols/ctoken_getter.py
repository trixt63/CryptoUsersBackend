from app.constants.network_constants import BNB
from app.services.artifacts.abis.erc20_abi import ERC20_ABI
from app.services.artifacts.abis.lending_pools.compound_abis.ctoken_abi import CTOKEN_ABI
from app.services.blockchain.protocols.base_getter import BaseGetter
from app.services.blockchain.batch_queries_services import add_rpc_call


class CtokenGetter(BaseGetter):
    def __init__(self, chain_id, pool_address, token_db, provider_uri=None, contribute=False):
        super().__init__(chain_id, pool_address, token_db, provider_uri)

        self.contribute = contribute

    def _start(self):
        self.underlying = self.ctokens[self.pool_address]
        if self.underlying == BNB:
            self.underlying = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
        self.token_addresses = [self.underlying]

    def get_wallet_state_calls(self, wallet_address, block_number='latest', list_rpc_call=None, list_call_id=None):
        if list_rpc_call is None:
            list_rpc_call = []
        if list_call_id is None:
            list_call_id = []

        add_rpc_call(
            abi=CTOKEN_ABI, contract_address=self.pool_address, fn_name="borrowBalanceCurrent",
            block_number=block_number, fn_paras=wallet_address,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        add_rpc_call(
            abi=CTOKEN_ABI, contract_address=self.pool_address, fn_name="balanceOfUnderlying",
            block_number=block_number, fn_paras=wallet_address,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        add_rpc_call(
            abi=ERC20_ABI, contract_address=self.underlying, fn_name="decimals", block_number=block_number,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        if self.contribute:
            add_rpc_call(
                abi=CTOKEN_ABI, contract_address=self.pool_address, fn_name="getCash", block_number=block_number,
                list_call_id=list_call_id, list_rpc_call=list_rpc_call
            )

        return list_rpc_call, list_call_id

    def get_wallet_state_by_decoded_response(self, decoded_response, wallet_address, block_number='latest', **kwargs):
        token_prices = self.token_db.get_token_price(addresses=self.token_addresses)

        get_total_deposit_id = f"balanceOfUnderlying_{self.pool_address}_{wallet_address}_{block_number}".lower()
        get_total_borrow_id = f"borrowBalanceCurrent_{self.pool_address}_{wallet_address}_{block_number}".lower()
        get_underlying_decimals_id = f'decimals_{self.underlying}_{block_number}'.lower()

        underlying_decimals = decoded_response[get_underlying_decimals_id]
        deposit_amount = decoded_response[get_total_deposit_id] / 10 ** underlying_decimals
        borrow_amount = decoded_response[get_total_borrow_id] / 10 ** underlying_decimals
        deposit_amount_in_usd = deposit_amount * token_prices.get(self.underlying, 0)
        borrow_amount_in_usd = borrow_amount * token_prices.get(self.underlying, 0)

        data = {
            "tvl": deposit_amount_in_usd - borrow_amount_in_usd,
            "deposit": deposit_amount_in_usd,
            "borrow": borrow_amount_in_usd
        }

        if self.contribute:
            get_cash_id = f"getCash_{self.pool_address}_{block_number}".lower()
            pool_tvl = decoded_response[get_cash_id] / 10 ** underlying_decimals
            data["contribute"] = (deposit_amount - borrow_amount) / pool_tvl

        return data
