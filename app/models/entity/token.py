from typing import Optional

from pydantic import BaseModel

from app.constants.network_constants import EMPTY_TOKEN_IMG
from app.constants.time_constants import TimeConstants
from app.models.explorer.node import Node
from app.utils.format_utils import short_address
from app.utils.list_dict_utils import sort_log, get_logs_change_rate


class OverviewQuery(BaseModel):
    chain: Optional[str] = None


class TransfersQuery(BaseModel):
    chain: Optional[str] = None
    pageSize: int = 25
    page: int = 1


class Token:
    def __init__(self, key):
        self.id = f'token/{key}'
        self.key = key
        self.name = ''
        self.symbol = ''
        self.type = 'token'
        self.chains = []
        self.img_url = ''
        self.price = 0
        self.price_change_rate = 0
        self.token_health = 0

    @classmethod
    def from_dict(cls, json_dict: dict):
        id_coingecko = json_dict.get('idCoingecko')
        key = id_coingecko or f'{json_dict["chainId"]}_{json_dict["address"]}'
        token = cls(key)

        token.name = json_dict.get('name') or short_address(json_dict['address'])
        symbol = json_dict.get('symbol') or 'UNKNOWN'
        token.symbol = symbol.upper()
        token.chains = [json_dict['chainId']]
        token.img_url = json_dict.get('imgUrl') or EMPTY_TOKEN_IMG
        token.price = json_dict.get('price')
        token.price_change_rate = cls.get_price_change_rate(json_dict, 'priceChangeLogs')
        token.token_health = json_dict.get('tokenHealth')
        return token

    def to_dict(self):
        return {
            'id': self.key,
            'name': self.name,
            'type': self.type,
            'chains': self.chains,
            'symbol': self.symbol,
            'imgUrl': self.img_url,
            'price': self.price,
            'priceChangeRate': self.price_change_rate,
            'tokenHealth': self.token_health
        }

    @classmethod
    def get_price_change_rate(cls, json_dict: dict, change_log_field, duration=TimeConstants.A_DAY):
        change_log = json_dict.get(change_log_field) or {}
        change_log = sort_log(change_log)
        price_change_rate = get_logs_change_rate(change_log, duration=duration)
        return price_change_rate

    def to_node(self) -> Node:
        node = Node(self.id)
        node.key = self.key
        node.type = self.type
        node.name = self.name
        return node
