from typing import Optional

from pydantic import BaseModel

from app.constants.search_constants import SearchConstants
from app.models.explorer.node import Node
from app.utils.format_utils import short_address
from app.utils.list_dict_utils import get_value_with_default, sort_log, combined_logs


class OverviewQuery(BaseModel):
    chain: Optional[str] = None


class TransactionsQuery(BaseModel):
    pageSize: int = 25
    page: int = 1


class Contract:
    def __init__(self, key):
        self.id = f'{SearchConstants.contract}/{key}'
        self.key = key
        self.name = ''
        self.address = ''
        self.type = SearchConstants.contract
        self.chains = []

        self.tx_and_user_metadata = None

    @classmethod
    def from_dict(cls, json_dict: dict):
        key = json_dict.get('_key') or f'{json_dict["chainId"]}_{json_dict["address"]}'
        contract = cls(key)
        contract.address = json_dict['address']
        contract.name = json_dict.get('name') or short_address(json_dict['address'])
        contract.chains = [json_dict['chainId']]
        return contract

    def to_dict(self):
        return {
            'id': self.key,
            'address': self.address,
            'name': self.name,
            'type': self.type,
            'chains': self.chains
        }

    def get_transactions_and_users_info(self, json_dict):
        self.tx_and_user_metadata = TxAndUserMetadata.from_dict(json_dict)

    def to_node(self) -> Node:
        node = Node(self.id)
        node.key = self.key
        node.type = self.type
        node.name = self.name
        return node


class TxAndUserMetadata:
    def __init__(self):
        self.number_of_transactions = 0
        self.number_of_active_wallets = 0
        self.number_of_daily_calls = {}

    @classmethod
    def from_dict(cls, json_dict):
        self = cls()
        self.number_of_transactions = json_dict.get('numberOfLastDayCalls')
        self.number_of_active_wallets = json_dict.get('numberOfLastDayActiveUsers')
        self.number_of_daily_calls = sort_log(get_value_with_default(json_dict, 'numberOfDailyCalls', {}))
        return self

    @classmethod
    def combine(cls, *metadata):
        combined = cls()
        daily_calls = []
        for obj in metadata:
            combined.number_of_transactions += obj.number_of_transactions or 0
            combined.number_of_active_wallets += obj.number_of_active_wallets or 0
            daily_calls.append(obj.number_of_daily_calls)

        combined.number_of_daily_calls = combined_logs(*daily_calls)
        return combined

    def to_dict(self):
        return {
            'numberOfActiveWallets': self.number_of_active_wallets,
            'numberOfTransactions': self.number_of_transactions,
            'numberOfDailyCalls': self.number_of_daily_calls
        }
