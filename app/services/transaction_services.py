import time
from typing import List, Union

from app.constants.mongodb_events_constants import TxConstants
from app.constants.time_constants import TimeConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.async_blockchain_etl import AsyncBlockchainETL
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.blocks_mapping_timestamp import Blocks
from app.models.entity.token import Token
from app.models.entity.transaction import Transaction
from app.models.entity.transfer import Transfer
from app.services.artifacts.exchange_addresses import EXCHANGE_ADDRESSES
from app.services.blockchain.decode_tx import decode_func_name
from app.utils.format_utils import short_address, pretty_tx_method
from app.utils.logger_utils import get_logger
from app.utils.search_data_utils import get_smart_contract_type, is_contract

logger = get_logger('Transaction Service')


class TransactionService:
    def __init__(self, graph: Union[MongoDB, KLGDatabase], mongo: BlockchainETL = None, async_mongo: AsyncBlockchainETL = None):
        self.graph = graph
        self.mongo = mongo

        self.async_mongo = async_mongo

    def get_transactions_with_value(self, chain_id, address, start_block):
        transactions = self.mongo.get_transactions_by_address(
            chain_id, address, start_block=start_block, projection=['value', 'block_timestamp', 'hash'])

        values = []
        transactions_with_time = []
        for tx in transactions:
            values.append(int(tx['value']) / 10 ** 18)
            transactions_with_time.append({
                'chain_id': chain_id,
                'hash': tx['hash'],
                'timestamp': tx['block_timestamp']
            })
        return values, transactions_with_time

    def get_transactions(self, chain_id, address, start_block, sort_by=TxConstants.block_number, reverse=True, skip=0, limit=50, count=True, decode_tx_method=True):
        contract = False
        if is_contract(chain_id, address):
            contract = True

        result = {}
        if count:
            # Count total transaction
            result['numberOfTransactions'] = self.mongo.count_documents_by_address(
                chain_id, address, start_block=start_block, is_contract=contract)

        # Get transaction with pagination
        transactions = self.mongo.get_transactions_by_address(
            chain_id, address, start_block=start_block, is_contract=contract,
            sort_by=sort_by, reverse=reverse, skip=skip, limit=limit
        )
        result['transactions'] = self.transactions_info(chain_id, transactions, decode_tx_method=decode_tx_method)
        return result

    async def async_get_transactions(self, chain_id, address, start_block, sort_by=TxConstants.block_number, reverse=True, skip=0, limit=50):
        contract = False
        if is_contract(chain_id, address):
            contract = True

        # Count total transaction
        number_of_transactions = await self.async_mongo.count_documents_by_address(
            chain_id, address, start_block=start_block, is_contract=contract)

        # Get transaction with pagination
        transactions = await self.async_mongo.get_transactions_by_address(
            chain_id, address, start_block=start_block, is_contract=contract,
            sort_by=sort_by, reverse=reverse, skip=skip, limit=limit
        )
        data = self.transactions_info(chain_id, transactions)
        return {
            'numberOfTransactions': number_of_transactions,
            'transactions': data
        }

    def get_transactions_(self, chain_id, hashes, reverse=True):
        transactions = self.mongo.get_transactions_by_hashes(chain_id, hashes)
        data = self.transactions_info(chain_id, transactions)
        data = sorted(data, key=lambda x: x.timestamp, reverse=reverse)
        return data

    def transactions_info(self, chain_id, transactions, decode_tx_method=True):
        # Add from/to address information
        transaction_objs = []
        for tx in transactions:
            transaction = Transaction.from_dict(tx, chain_id=chain_id)
            transaction_objs.append(transaction)

        self.decode_tx(transaction_objs, chain_id, decode_tx_method=decode_tx_method)
        return transaction_objs

    def get_wallet_money_flow(self, chain_id, address):
        timestamp_a_day_ago = int(time.time()) - TimeConstants.A_DAY
        start_block = Blocks().block_numbers(chain_id, timestamp_a_day_ago)

        transfer_in_events = self.mongo_transfers.get_transfer_in_events(chain_id, address, start_block)
        transfer_out_events = self.mongo_transfers.get_transfer_out_events(chain_id, address, start_block)

        cex_addresses = get_exchange_filter(is_dex=False, address=address)

        transfers = {}
        tradings = {}
        for events, direct in zip([transfer_in_events, transfer_out_events], ['input', 'output']):
            for event in events:
                token_address = event['contract_address']
                if token_address not in transfers:
                    transfers[token_address] = {'input': 0, 'output': 0}
                transfers[token_address][direct] += int(event['value'])
                wallet_trading_cex(cex_addresses, event, tradings)

        contracts = self.graph.get_smart_contracts(chain_id, list(transfers.keys()))
        contracts = {c['address']: c for c in contracts}
        tokens = []
        for token_address, info in transfers.items():
            token = contracts.get(token_address)
            if not token:
                logger.warning(f'Miss token {token_address}')

            decimals = token.get('decimals') or 18
            price = token.get('price') or 0
            input_amount = info['input'] / 10 ** decimals
            output_amount = info['output'] / 10 ** decimals

            tokens.append({
                'id': token_address,
                'type': 'token',
                'name': token.get('name') or short_address(token_address),
                'address': token_address,
                'symbol': token.get('symbol'),
                'input': {'amount': input_amount, 'valueInUSD': input_amount * price},
                'output': {'amount': output_amount, 'valueInUSD': output_amount * price},
                'transferVolume': (input_amount + output_amount) * price
            })
        tokens = sorted(tokens, key=lambda x: x['transferVolume'], reverse=True)

        exchanges = get_exchanges_info(tradings, contracts)
        return tokens, exchanges

    def get_wallet_dexes(self, chain_id, address):
        timestamp_a_day_ago = int(time.time()) - TimeConstants.A_DAY
        start_block = Blocks().block_numbers(chain_id, timestamp_a_day_ago)

        dex_addresses = get_exchange_filter(is_dex=True, address=address)

        transactions_out = self.mongo.get_transactions_from_address(chain_id, from_address=address, start_block=start_block)
        tradings = {}
        for transaction in transactions_out:
            for exchange_name, exchange_addresses in dex_addresses.items():
                for dex_address in exchange_addresses:
                    if transaction['to_address'] == dex_address:
                        if exchange_name not in tradings:
                            tradings[exchange_name] = {'hashes': [], 'transactions': 0}
                        tradings[exchange_name]['transactions'] += 1
                        tradings[exchange_name]['hashes'].append(transaction['hash'])

        tx_hashes = []
        for info in tradings.values():
            tx_hashes.extend(info['hashes'])

        events = self.mongo_transfers.get_transfer_events_by_hashes(chain_id, tx_hashes)
        events_by_hash = {}
        token_addresses = {}
        for event in events:
            if (event['from'] != address) and (event['to'] != address):
                continue

            tx_hash = event['transaction_hash']
            if tx_hash not in events_by_hash:
                events_by_hash[tx_hash] = {}

            token_address = event['contract_address']
            if token_address not in events_by_hash[tx_hash]:
                events_by_hash[tx_hash][token_address] = 0
                token_addresses[token_address] = 1

            events_by_hash[tx_hash][token_address] += int(event['value'])

        contracts = self.graph.get_smart_contracts(chain_id, token_addresses)
        contracts = {c['address']: c for c in contracts}

        exchanges = []
        for exchange_name, info in tradings.items():
            hashes = info['hashes']
            trading_volume = 0
            for tx_hash in hashes:
                tx_tokens = events_by_hash.get(tx_hash)
                if tx_tokens:
                    for token_address, amount in tx_tokens.items():
                        token = contracts.get(token_address, {})
                        decimals = token.get('decimals') or 18
                        price = token.get('price') or 0
                        trading_volume += price * (amount / 10 ** decimals)

            exchanges.append({
                'name': exchange_name,
                'tradingVolume': trading_volume,
                'transactions': info['transactions']
            })
        return exchanges

    def decode_tx(self, transactions: Union[List[Transaction], Transaction], chain_id, decode_tx_method=True):
        if not isinstance(transactions, list):
            transactions = [transactions]

        contract_addresses = {transaction.to_address: 1 for transaction in transactions}
        contract_keys = [f'{chain_id}_{address}' for address in contract_addresses]
        contracts = self.graph.get_contracts_by_keys(contract_keys, projection=['name', 'chainId', 'address', 'tags', 'keyABI'])
        contracts = {contract["address"]: contract for contract in contracts}

        abis = {}
        if decode_tx_method:
            abi_keys = []
            for contract_address, contract in contracts.items():
                if contract.get('keyABI'):
                    abi_keys.append(contract['keyABI'])
            abi_keys = list(set(abi_keys))

            abis = self.graph.get_abi(abi_keys)
            abis = {abi['name']: abi['abi'] for abi in abis}

        for transaction in transactions:
            to_address = transaction.to_address
            contract = contracts.get(to_address) or {'chainId': chain_id, 'address': to_address}
            contract_type = get_smart_contract_type(contract)

            if contract_type:
                contract['type'] = 'contract'
                if decode_tx_method and contract.get('keyABI'):
                    contract_abi = abis.get(contract['keyABI'], [])
                    transaction.decode_transaction_method(contract_abi)

            transaction.update_addresses({to_address: contract})

    def transfers_info(self, chain_id, transfers):
        # Add from/to address information
        transfers_objs = []
        for event in transfers:
            transaction = Transfer.from_dict(event, chain_id=chain_id)
            transfers_objs.append(transaction)

        self.update_transfers_address(transfers_objs, chain_id)
        return transfers_objs

    def update_transfers_address(self, transfers: Union[List[Transfer], Transfer], chain_id):
        if not isinstance(transfers, list):
            transfers = [transfers]

        addresses = set()
        for transfer in transfers:
            addresses.update([transfer.from_address, transfer.to_address, transfer.contract_address])
        contract_keys = [f'{chain_id}_{address}' for address in addresses]

        cursor = self.graph.get_contracts_by_keys(contract_keys, projection=['name', 'chainId', 'address', 'tags', 'symbol', 'price', 'imgUrl'])
        contracts = {}
        for contract in cursor:
            contract_type = get_smart_contract_type(contract)
            if contract_type:
                contract['type'] = 'contract'
            contracts[contract['address']] = contract

        for transfer in transfers:
            transfer.update_addresses(contracts)

            token = contracts.get(transfer.contract_address) or {'chainId': chain_id, 'address': transfer.contract_address}
            token_node = Token.from_dict(token)
            transfer.update_token(token_node)

    def update_transfers_tx_info(self, transfers: List[Transfer], chain_id):
        transaction_hashes = [transfer.tx_hash for transfer in transfers]
        transactions = self.mongo.get_transactions_by_hashes(chain_id, transaction_hashes)
        transactions = {tx['hash']: Transaction.from_dict(tx, chain_id) for tx in transactions}

        for transfer in transfers:
            tx_hash = transfer.tx_hash
            transaction = transactions.get(tx_hash)
            if transaction:
                transfer.update_tx_method(transaction)


def get_exchanges_info(tradings, contracts):
    exchanges = []
    for exchange_name, info in tradings.items():
        trading_tokens = info['tokens']
        trading_volume = 0
        for token_address, amount in trading_tokens.items():
            token = contracts.get(token_address, {})
            decimals = token.get('decimals') or 18
            price = token.get('price') or 0
            trading_volume += price * (amount / 10 ** decimals)

        exchanges.append({
            'name': exchange_name,
            'tradingVolume': trading_volume,
            'transactions': info['transactions']
        })
    return exchanges


def wallet_trading_cex(exchanges, event, tradings):
    for exchange_name, exchange_addresses in exchanges.items():
        for address in exchange_addresses:
            if event['from'] == address or event['to'] == address:
                if exchange_name not in tradings:
                    tradings[exchange_name] = {'tokens': {}, 'transactions': 0}

                tradings[exchange_name]['transactions'] += 1
                token = event['contract_address']
                if token not in tradings[exchange_name]['tokens']:
                    tradings[exchange_name]['tokens'][token] = 0
                tradings[exchange_name]['tokens'][token] += int(event['value'])


def get_exchange_filter(is_dex, address=None):
    exchanges = {}
    for exchange_id, exchange in EXCHANGE_ADDRESSES.items():
        if exchange['isDex'] == is_dex:
            addresses = exchange['addresses']
            exchanges[exchange['name']] = [ex_address['address'] for ex_address in addresses if (address is None) or (ex_address != addresses)]
    return exchanges


def get_tx_method(tx_input, abi):
    func_name = tx_input[:10]
    if abi:
        try:
            func_name = decode_func_name(contract_abi=abi, tx_input=tx_input)
            func_name = pretty_tx_method(func_name)
        except Exception as ex:
            logger.warning(f"{ex}")

    return func_name
