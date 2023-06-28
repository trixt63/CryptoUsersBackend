class MongoEventsCollections:
    CONFIGS = 'configs'
    LENDING_EVENTS = 'lending_events'
    TRANSACTIONS = "transactions"
    BLOCKS = "blocks"
    TOKEN_TRANSFERS = 'token_transfers'
    COLLECTORS = 'collectors'


class MongoIndex:
    ADDRESS_CONFIGS = 'address_configs'
    BLOCK_NUMBER_EVENTS = 'block_number_events'
    FROM_EVENTS = 'from_events'
    TO_EVENTS = 'to_events'
    BLOCK_NUMBER_TO_EVENTS = 'block_number_to_events'
    BLOCK_NUMBER_FROM_EVENTS = 'block_number_from_events'
    TX_HASH_EVENTS = 'transaction_hash_events'


class TxConstants:
    id = "_id"
    type = "type"
    hash = "hash"
    from_address = "from_address"
    to_address = "to_address"
    value = "value"
    gas = "gas"
    receipt_gas_used = 'receipt_gas_used'
    gas_price = "gas_price"
    block_number = "block_number"
    block_timestamp = "block_timestamp"
    status = "receipt_status"
    receipt_contract_address = 'receipt_contract_address'
    transaction_type = "transaction_type"
    input = "input"
    data = [type, hash, from_address, to_address, value, gas, receipt_gas_used, gas_price,
            block_number, block_timestamp, status, transaction_type, input, receipt_contract_address]


class BlockConstants:
    id = "_id"
    type = "type"
    number = "number"
    hash = "hash"
    miner = "miner"
    size = "size"
    gas_limit = "gas_limit"
    gas_used = "gas_used"
    timestamp = "timestamp"
    transaction_count = "transaction_count"
    difficult = "difficulty"
    total_difficult = "total_difficulty"
    data = [type, number, hash, miner, size, gas_limit, gas_used,
            timestamp, difficult, total_difficult, transaction_count]


class Event:
    id = '_id'
    type = 'type'
    from_address = 'from_address'
    to_address = 'to_address'
    token_address = 'token_address'
    value = 'value'
    transaction_hash = 'transaction_hash'
    log_index = 'log_index'
    block_number = 'block_number'

    data = [type, from_address, to_address, token_address, value, transaction_hash, log_index, block_number]
