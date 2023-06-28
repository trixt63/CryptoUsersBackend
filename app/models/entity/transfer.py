from typing import Union, Dict

from app.models.entity.contract import Contract
from app.models.entity.token import Token
from app.models.entity.wallet import Wallet


class Transfer:
    def __init__(self, block_number, log_index, chain_id):
        self.block_number = block_number
        self.log_index = log_index
        self.chain_id = chain_id

        self.tx_hash = ''
        self.from_address = ''
        self.to_address = ''
        self.contract_address = ''
        self.value = 0

        self.timestamp = None
        self.method = '0x'
        self.token: Union[Token, None] = None
        self.from_ = None
        self.to_ = None

    @classmethod
    def from_dict(cls, json_dict, chain_id=None):
        self = cls(json_dict['block_number'], json_dict['log_index'], chain_id)

        self.tx_hash = json_dict['transaction_hash']
        self.from_address = json_dict['from_address']
        self.to_address = json_dict['to_address']
        self.contract_address = json_dict['contract_address']
        self.value = json_dict.get('value', 0)

        return self

    def update_token(self, token: Union[Token, dict]):
        if not isinstance(token, Token):
            token = Token.from_dict(token)
        self.token = token

    def update_tx_method(self, transaction):
        self.method = transaction.method
        self.timestamp = transaction.block_timestamp

    def update_addresses(self, objs: Dict[str, Union[Wallet, Contract, dict]]):
        from_obj = objs.get(self.from_address) or {'address': self.from_address}
        if isinstance(from_obj, dict):
            if from_obj.get('type') == 'contract':
                from_obj = Contract.from_dict(from_obj)
            else:
                from_obj = Wallet.from_dict(from_obj)
        self.from_ = from_obj

        to_obj = objs.get(self.to_address) or {'address': self.to_address}
        if isinstance(to_obj, dict):
            if to_obj.get('type') == 'contract':
                to_obj = Contract.from_dict(to_obj)
            else:
                to_obj = Wallet.from_dict(to_obj)
        self.to_ = to_obj

    def to_dict(self):
        return {
            "id": f"{self.chain_id}_{self.tx_hash}",
            "chain": self.chain_id,
            "transactionHash": self.tx_hash,
            "blockNumber": self.block_number,
            "timestamp": self.timestamp,
            "fromAddress": self.from_address,
            "toAddress": self.to_address,
            "token": self.token.to_dict() if self.token is not None else None,
            "value": self.value,
            "from": self.from_.to_dict() if self.from_ is not None else None,
            "to": self.to_.to_dict() if self.to_ is not None else None
        }
