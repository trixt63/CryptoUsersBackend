from typing import Optional

from pydantic import BaseModel

from app.constants.time_constants import TimeConstants
from app.models.explorer.node import Node
from app.utils.format_utils import short_address


class OverviewQuery(BaseModel):
    chain: Optional[str] = None


class CreditScoreQuery(BaseModel):
    chain: Optional[str] = None
    duration: int = TimeConstants.DAYS_30


class TransactionsQuery(BaseModel):
    chain: Optional[str] = None
    pageSize: int = 25
    page: int = 1


class Wallet:
    def __init__(self, key):
        self.id = f'wallet/{key}'
        self.key = key
        self.address = ''
        self.name = ''
        self.type = 'wallet'

    @classmethod
    def from_dict(cls, json_dict: dict):
        address = json_dict['address']

        wallet = cls(address)
        wallet.address = address
        wallet.name = json_dict.get('name') or short_address(address)
        return wallet

    def to_dict(self):
        return {
            'id': self.key,
            'address': self.address,
            'name': self.name,
            'type': self.type
        }

    def to_node(self) -> Node:
        node = Node(self.id)
        node.key = self.key
        node.type = self.type
        node.name = self.name
        return node
