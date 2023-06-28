import time
from typing import Optional, List, Union, Dict

from pydantic import BaseModel

from app.models.entity.contract import Contract
from app.models.entity.transfer import Transfer
from app.models.entity.wallet import Wallet
from app.services.blockchain.decode_tx import decode_func_name
from app.utils.logger_utils import get_logger

logger = get_logger('Transaction')


class OverviewQuery(BaseModel):
    chain: Optional[str] = None


class Transaction:
    def __init__(self, tx_hash, chain_id):
        self.hash = tx_hash
        self.chain_id = chain_id
        self.block_number = 0
        self.block_timestamp = int(time.time())
        self.transaction_index = 0
        self.from_address = ''
        self.to_address = ''
        self.value = 0
        self.input = '0x'
        self.method = '0x'
        self.status = True
        self.gas_used = 0
        self.gas_price = 0
        self.gas_limit = 0

        self.from_ = None
        self.to_ = None

        self.transfers: List[Transfer] = []

    @classmethod
    def from_dict(cls, json_dict, chain_id=None):
        tx_hash = json_dict['hash']
        self = cls(tx_hash, chain_id)

        self.block_number = json_dict['block_number']
        self.block_timestamp = json_dict['block_timestamp']
        self.transaction_index = json_dict.get('transaction_index', 0)

        self.from_address = json_dict['from_address']
        self.to_address = json_dict.get('to_address') or json_dict.get('receipt_contract_address')
        self.value = int(json_dict.get('value')) / 10 ** 18
        self.input = json_dict.get('input', '0x')
        self.method = self.input[:10]
        self.status = json_dict.get('receipt_status')

        self.gas_used = int(json_dict.get('receipt_gas_used', 0))
        self.gas_price = int(json_dict.get('gas_price', 0))
        self.gas_limit = int(json_dict.get('gas', 0))

        return self

    def to_dict(self):
        return {
            "id": f'{self.chain_id}_{self.hash}',
            "chain": self.chain_id,
            "hash": self.hash,
            "status": self.status,
            "blockNumber": self.block_number,
            "timestamp": self.block_timestamp,
            "fromAddress": self.from_address,
            "toAddress": self.to_address,
            "value": self.value,
            "method": self.method,
            "input": self.input,
            "gas": self.gas_used,
            "gasLimit": self.gas_limit,
            "gasPrice": self.gas_price,
            "from": self.from_.to_dict() if self.from_ is not None else None,
            "to": self.to_.to_dict() if self.to_ is not None else None
        }

    def decode_transaction_method(self, contract_abi):
        try:
            self.method = decode_func_name(contract_abi, self.input)
        except ValueError:
            pass
        except Exception as ex:
            logger.warning(f'Fail to get transaction method: {ex}')

    def get_transfers_dict(self):
        transfers_obj = sorted(self.transfers, key=lambda x: x.log_index)

        transfers = []
        for transfer in transfers_obj:
            transfers.append(transfer.to_dict())
        return transfers

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
