from app.constants.contract_constants import ContractConst
from app.constants.network_constants import BNB, WRAPPED_NATIVE_TOKENS
from app.decorators.time_exe import TimeExeTag, sync_log_time_exe
from app.services.artifacts.abis.erc20_abi import ERC20_ABI
from app.services.artifacts.abis.lending_pools.compound_abis.ctoken_abi import CTOKEN_ABI
from app.services.blockchain.protocols.base_getter import BaseGetter
from app.services.blockchain.batch_queries_services import add_rpc_call


class ComptrollerGetter(BaseGetter):
    def __init__(self, chain_id, pool_address, db, provider_uri=None, pool_info=None, reserves_list=None):
        super().__init__(chain_id, pool_address, db, provider_uri, pool_info, reserves_list)

    def _start(self):
        self.token_addresses = []
        for token in self.reserves_list:
            if token == BNB:
                self.token_addresses.append(WRAPPED_NATIVE_TOKENS.get(self.chain_id))
            else:
                self.token_addresses.append(token.lower())

    def get_wallet_state_calls(self, wallet_address, block_number='latest', list_rpc_call=None, list_call_id=None):
        if list_rpc_call is None:
            list_rpc_call = []
        if list_call_id is None:
            list_call_id = []

        for token, token_info in self.reserves_list.items():
            if token == BNB:
                token = WRAPPED_NATIVE_TOKENS.get(self.chain_id)
            self.get_token_requests(
                list_rpc_call, list_call_id, wallet_address, token_info, block_number, token_address=token)

        self.get_reward_requests(list_rpc_call, list_call_id, wallet_address, block_number)
        return list_rpc_call, list_call_id

    def get_token_requests(self, list_rpc_call, list_call_id, wallet_address, token_info, block_number='latest', **kwargs):
        ctoken = token_info['vToken']
        token_address = kwargs.get('token_address')

        add_rpc_call(
            abi=CTOKEN_ABI, contract_address=ctoken, fn_name="borrowBalanceCurrent",
            block_number=block_number, fn_paras=wallet_address,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        add_rpc_call(
            abi=CTOKEN_ABI, contract_address=ctoken, fn_name="balanceOfUnderlying",
            block_number=block_number, fn_paras=wallet_address,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        add_rpc_call(
            abi=ERC20_ABI, contract_address=token_address, fn_name="decimals", block_number=block_number,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )
        add_rpc_call(
            abi=CTOKEN_ABI, contract_address=ctoken, fn_name="getCash", block_number=block_number,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )

    def get_reward_requests(self, list_rpc_call, list_call_id, wallet_address, block_number='latest', **kwargs):
        if self.pool_info['name'] == "venus-bsc":
            fn_paras = [wallet_address, self.pool_info[ContractConst.comptroller_address]]
            add_rpc_call(
                abi=self.pool_info[ContractConst.lending_abi], fn_paras=fn_paras, block_number=block_number,
                contract_address=self.pool_info[ContractConst.lending_address], fn_name="pendingVenus",
                list_call_id=list_call_id, list_rpc_call=list_rpc_call
            )
        else:
            fn_paras = [
                self.pool_info[ContractConst.token],
                self.pool_info[ContractConst.comptroller_implementation_address],
                wallet_address
            ]
            add_rpc_call(
                abi=self.pool_info[ContractConst.lending_abi], fn_paras=fn_paras, block_number=block_number,
                contract_address=self.pool_info[ContractConst.lending_address], fn_name="getCompBalanceMetadataExt",
                list_call_id=list_call_id, list_rpc_call=list_rpc_call
            )

    def get_wallet_state_by_decoded_response(self, decoded_response, wallet_address, block_number='latest', **kwargs):
        token_prices = self.get_token_prices(kwargs.get('token_prices'))

        data = {"deposit": 0, "borrow": 0}
        tokens = {}
        for token, token_info in self.reserves_list.items():
            self.decode_token_info(
                decoded_response, wallet_address, token_info, block_number,
                token_address=token, token_prices=token_prices, tokens=tokens
            )
            data['deposit'] += tokens[token]['deposit']['valueInUSD']
            data['borrow'] += tokens[token]['borrow']['valueInUSD']

        data['tvl'] = data['deposit'] - data['borrow']
        data['tokens'] = tokens

        reward_amount, reward_in_usd = self.decode_reward_info(
            decoded_response, wallet_address, block_number, token_prices=token_prices)
        data['claimable'] = reward_in_usd

        return data

    def decode_token_info(self, decoded_response, wallet_address, token_info, block_number='latest', *args, **kwargs):
        token_address = kwargs.get('token_address')
        token_prices = kwargs.get('token_prices')
        tokens = kwargs.get('tokens')

        ctoken = token_info['vToken']
        underlying = token_address
        if token_address == BNB:
            underlying = WRAPPED_NATIVE_TOKENS.get(self.chain_id)

        token_price = token_prices.get(underlying) or 0

        get_total_deposit_id = f"balanceOfUnderlying_{ctoken}_{wallet_address}_{block_number}".lower()
        get_total_borrow_id = f"borrowBalanceCurrent_{ctoken}_{wallet_address}_{block_number}".lower()
        get_decimals_id = f"decimals_{underlying}_{block_number}".lower()
        decimals = decoded_response[get_decimals_id]
        deposit_amount = decoded_response[get_total_deposit_id] / 10 ** decimals
        borrow_amount = decoded_response[get_total_borrow_id] / 10 ** decimals
        deposit_in_usd = deposit_amount * token_price
        borrow_in_usd = borrow_amount * token_price

        tokens[token_address] = {
            'deposit': {'amount': deposit_amount, 'valueInUSD': deposit_in_usd},
            'borrow': {'amount': borrow_amount, 'valueInUSD': borrow_in_usd}
        }

    def decode_reward_info(self, decoded_response, wallet_address, block_number='latest', *args, **kwargs):
        token_prices = kwargs.get('token_prices')

        if self.pool_info['name'] == 'venus-bsc':
            fn_paras = [wallet_address, self.pool_info[ContractConst.comptroller_address]]
            get_reward_id = f"pendingVenus_{self.pool_info[ContractConst.lending_address]}_{fn_paras}_{block_number}".lower()
            reward_amount = decoded_response[get_reward_id] / 10 ** 18
        else:
            fn_paras = [
                self.pool_info[ContractConst.token],
                self.pool_info[ContractConst.comptroller_implementation_address],
                wallet_address
            ]
            get_reward_id = f"getCompBalanceMetadataExt_{self.pool_info[ContractConst.lending_address]}_{fn_paras}_{block_number}".lower()
            reward_amount = decoded_response[get_reward_id][-1] / 10 ** 18

        token_price = token_prices.get(self.pool_info[ContractConst.token].lower()) or 0
        reward_in_usd = reward_amount * token_price
        return reward_amount, reward_in_usd

    @sync_log_time_exe(tag=TimeExeTag.blockchain)
    def get_tvl(self, wallet_address, block_number='latest'):
        list_rpc_call = []
        list_call_id = []

        for token, token_info in self.reserves_list.items():
            ctoken = token_info['vToken']

            add_rpc_call(
                abi=CTOKEN_ABI, contract_address=ctoken, fn_name="borrowBalanceCurrent",
                block_number=block_number, fn_paras=wallet_address,
                list_call_id=list_call_id, list_rpc_call=list_rpc_call
            )
            add_rpc_call(
                abi=CTOKEN_ABI, contract_address=ctoken, fn_name="balanceOfUnderlying",
                block_number=block_number, fn_paras=wallet_address,
                list_call_id=list_call_id, list_rpc_call=list_rpc_call
            )
            if token != BNB:
                add_rpc_call(
                    abi=ERC20_ABI, contract_address=token, fn_name="decimals", block_number=block_number,
                    list_call_id=list_call_id, list_rpc_call=list_rpc_call
                )

        decoded_response = self.request_data(list_rpc_call, list_call_id)

        tvl = 0
        for token, token_info in self.reserves_list.items():
            token_price = token_info.get('price') or 0
            ctoken = token_info['vToken']

            get_total_deposit_id = f"balanceOfUnderlying_{ctoken}_{wallet_address}_{block_number}".lower()
            get_total_borrow_id = f"borrowBalanceCurrent_{ctoken}_{wallet_address}_{block_number}".lower()
            get_decimals_id = f"decimals_{token}_{block_number}".lower()

            decimals = decoded_response.get(get_decimals_id, 18)
            deposit_amount = decoded_response[get_total_deposit_id] / 10 ** decimals
            borrow_amount = decoded_response[get_total_borrow_id] / 10 ** decimals
            tvl += (deposit_amount - borrow_amount) * token_price

        return tvl
