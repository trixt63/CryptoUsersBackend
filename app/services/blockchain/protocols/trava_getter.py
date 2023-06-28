from web3 import Web3

from app.constants.contract_constants import ContractConst
from app.decorators.time_exe import TimeExeTag, sync_log_time_exe
from app.services.artifacts.abis.erc20_abi import ERC20_ABI
from app.services.artifacts.abis.lending_pools.trava_pool.staked_incentives_abi import STAKED_INCENTIVES_ABI
from app.services.blockchain.batch_queries_services import add_rpc_call
from app.services.blockchain.protocols.base_getter import BaseGetter


class TravaGetter(BaseGetter):
    def __init__(self, chain_id, pool_address, db, provider_uri=None, pool_info=None, reserves_list=None):
        super().__init__(chain_id, pool_address, db, provider_uri, pool_info, reserves_list)

    def _start(self):
        self.token_addresses = list(self.reserves_list.keys())
        if self.pool_info.get(ContractConst.staked_token):
            self.token_addresses.append(self.pool_info[ContractConst.staked_token])

        self.td_tokens = []

    def get_wallet_state_calls(self, wallet_address, block_number='latest', list_rpc_call=None, list_call_id=None):
        if list_rpc_call is None:
            list_rpc_call = []
        if list_call_id is None:
            list_call_id = []

        # add_rpc_call(
        #     abi=TRAVA_LENDING_POOL_ABI, contract_address=self.pool_address, fn_name="getUserAccountData",
        #     fn_paras=wallet_address, block_number=block_number,
        #     list_call_id=list_call_id, list_rpc_call=list_rpc_call
        # )

        for token, token_info in self.reserves_list.items():
            self.td_tokens.extend([Web3.toChecksumAddress(token_info["tToken"]), Web3.toChecksumAddress(token_info["dToken"])])
            self.get_token_requests(
                list_rpc_call, list_call_id, wallet_address, token_info,
                block_number=block_number, token_address=token,
            )
        self.get_reward_requests(list_rpc_call, list_call_id, block_number=block_number, wallet_address=wallet_address)

        return list_rpc_call, list_call_id

    def get_token_requests(self, list_rpc_call, list_call_id, wallet_address, token_info, block_number='latest', **kwargs):
        token_address = kwargs['token_address']

        add_rpc_call(abi=ERC20_ABI, contract_address=token_info["tToken"], fn_paras=wallet_address,
                     block_number=block_number,
                     list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
        add_rpc_call(abi=ERC20_ABI, contract_address=token_info["dToken"], fn_paras=wallet_address,
                     block_number=block_number,
                     list_call_id=list_call_id, list_rpc_call=list_rpc_call, fn_name="balanceOf")
        add_rpc_call(abi=ERC20_ABI, contract_address=token_address, fn_name="decimals", block_number=block_number,
                     list_call_id=list_call_id, list_rpc_call=list_rpc_call)

    def get_reward_requests(self, list_rpc_call, list_call_id, wallet_address, block_number='latest', **kwargs):
        if self.pool_info.get(ContractConst.staked_incentive_address):
            add_rpc_call(
                abi=STAKED_INCENTIVES_ABI, contract_address=self.pool_info[ContractConst.staked_incentive_address],
                fn_name="getRewardsBalance", block_number=block_number, fn_paras=[self.td_tokens, wallet_address],
                list_call_id=list_call_id, list_rpc_call=list_rpc_call
            )

    def get_wallet_state_by_decoded_response(self, decoded_response, wallet_address, block_number='latest', **kwargs):
        data = {"deposit": 0, "borrow": 0}

        token_prices = self.get_token_prices(kwargs.get('token_prices'))

        tokens = {}
        for token, token_info in self.reserves_list.items():
            self.decode_token_info(
                decoded_response, wallet_address, token_info, block_number,
                token_address=token, tokens=tokens, token_prices=token_prices
            )
            data['deposit'] += tokens[token]['deposit']['valueInUSD']
            data['borrow'] += tokens[token]['borrow']['valueInUSD']

        data["tvl"] = data["deposit"] - data["borrow"]
        reward_amount, reward_in_usd = self.decode_reward_info(
            decoded_response, wallet_address, block_number, token_prices=token_prices)

        data.update({
            'tokens': tokens,
            'claimable': reward_in_usd
        })
        return data

    def decode_token_info(self, decoded_response, wallet_address, token_info, block_number='latest', *args, **kwargs):
        token_prices = kwargs['token_prices']
        token_address = kwargs['token_address']
        tokens = kwargs['tokens']

        get_decimals_id = f"decimals_{token_address}_{block_number}".lower()
        decimals = decoded_response[get_decimals_id]

        token_price = token_prices.get(token_address) or 0

        deposit_id = f"balanceOf_{token_info['tToken']}_{wallet_address}_{block_number}".lower()
        borrow_id = f"balanceOf_{token_info['dToken']}_{wallet_address}_{block_number}".lower()
        deposit_amount = decoded_response[deposit_id] / 10 ** decimals
        borrow_amount = decoded_response[borrow_id] / 10 ** decimals
        deposit_amount_in_usd = deposit_amount * token_price
        borrow_amount_in_usd = borrow_amount * token_price

        tokens[token_address] = {
            'deposit': {'amount': deposit_amount, 'valueInUSD': deposit_amount_in_usd},
            'borrow': {'amount': borrow_amount, 'valueInUSD': borrow_amount_in_usd}
        }

    def decode_reward_info(self, decoded_response, wallet_address, block_number='latest', *args, **kwargs):
        if not self.pool_info.get(ContractConst.staked_incentive_address):
            return 0, 0

        token_prices = kwargs['token_prices']

        reward_id = f'getRewardsBalance_{self.pool_info[ContractConst.staked_incentive_address]}_{[self.td_tokens, wallet_address]}_{block_number}'.lower()
        reward_amount = decoded_response[reward_id] / 10 ** 18

        token_price = token_prices.get(self.pool_info[ContractConst.staked_token].lower()) or 0
        reward_in_usd = reward_amount * token_price
        return reward_amount, reward_in_usd

    def get_reserve_data(self, trava_idx=True):
        w3 = Web3(Web3.HTTPProvider(self.client_querier.provider_url))
        contract = w3.eth.contract(Web3.toChecksumAddress(self.pool_address), abi=self.pool_info[ContractConst.lending_abi])
        reserves = contract.functions.getReservesList().call()

        reserves_list = {}
        for token_address in reserves:
            info = contract.functions.getReserveData(Web3.toChecksumAddress(token_address)).call()
            if trava_idx:
                t_token = info[6].lower()
                d_token = info[7].lower()
            else:
                t_token = info[7].lower()
                d_token = info[9].lower()

            reserves_list[token_address.lower()] = {
                'tToken': t_token,
                'dToken': d_token,
            }
        return reserves_list

    @sync_log_time_exe(tag=TimeExeTag.blockchain)
    def get_tvl(self, wallet_address, block_number='latest'):
        list_rpc_call = []
        list_call_id = []
        add_rpc_call(
            abi=self.pool_info[ContractConst.lending_abi], contract_address=self.pool_address, fn_name="getUserAccountData",
            fn_paras=wallet_address, block_number=block_number,
            list_call_id=list_call_id, list_rpc_call=list_rpc_call
        )

        decoded_response = self.request_data(list_rpc_call, list_call_id)

        get_user_info_id = f"getUserAccountData_{self.pool_address}_{wallet_address}_{block_number}".lower()
        user_info = decoded_response[get_user_info_id]
        data = {
            "deposit": user_info[0] / 10 ** self.pool_info["decimals"],
            "borrow": user_info[1] / 10 ** self.pool_info["decimals"]
        }
        return data['deposit'] - data['borrow']
