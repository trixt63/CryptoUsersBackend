import time
from typing import List

from app.models.entity.transaction import Transaction


class Block:
    def __init__(self, block_hash, chain_id):
        self.hash = block_hash
        self.chain_id = chain_id

        self.number = 0
        self.timestamp = int(time.time())
        self.transactions_count = 0
        self.difficulty = 0
        self.total_difficulty = 0
        self.size = 0
        self.gas_used = 0
        self.gas_limit = 0

        self.miner = ''

        self.transactions: List[Transaction] = []

    @classmethod
    def from_dict(cls, json_dict, chain_id=None):
        self = cls(json_dict['hash'], chain_id)

        self.number = json_dict['number']
        self.timestamp = json_dict['timestamp']
        self.transactions_count = json_dict['transaction_count']
        self.difficulty = json_dict['difficulty']
        self.total_difficulty = json_dict['total_difficulty']
        self.size = json_dict['size']
        self.gas_used = json_dict['gas_used']
        self.gas_limit = json_dict['gas_limit']

        self.miner = json_dict.get('miner')

        return self

    def to_dict(self):
        return {
            "id": f'{self.chain_id}_{self.hash}',
            "chain": self.chain_id,
            "number": self.number,
            "hash": self.hash,
            "timestamp": self.timestamp,
            "numberOfTransactions": self.transactions_count,
            "difficulty": self.difficulty,
            "totalDifficulty": self.total_difficulty,
            "size": self.size,
            "gasUsed": self.gas_used,
            "gasLimit": self.gas_limit
        }

    def get_transactions_dict(self) -> List[dict]:
        transactions_obj = sorted(self.transactions, key=lambda x: x.transaction_index)

        transactions = []
        for transaction in transactions_obj:
            transactions.append(transaction.to_dict())
        return transactions
