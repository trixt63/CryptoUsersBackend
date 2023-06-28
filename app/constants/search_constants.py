class SearchConstants:
    transaction = 'transaction'
    block = 'block'
    wallet = 'wallet'
    token = 'token'
    contract = 'contract'
    project = 'project'
    text = 'text'


class Tags:
    address = 'address'
    contract = 'contract'
    dapp = 'dapp'
    lending = 'lending'
    vault = 'vault'
    dex = 'dex'
    token = 'token'
    pair = 'pair'

    all = [contract, dapp, lending, vault, dex, token, pair]


class RelationshipType:
    # Wallet
    deposit = 'deposit'  # => Lending
    borrow = 'borrow'  # => Lending
    swap = 'swap'  # => Vault
    transfer = 'transfer'  # => Wallet
    liquidate = 'liquidate'  # => Wallet
    call_contract = 'call_contract'  # => Contract
    hold = 'hold'  # => Token
    use = 'use'  # => DApp
    tracker = 'tracker'  # => Contract

    # Project
    release = 'release'  # => Token
    subproject = 'subproject'  # => Project
    has_contract = 'has_contract'  # => Contract

    # Contract
    forked_from = 'forked_from'  # => Contract
    addon_contract = 'addon_contract'  # => Contract
    support = 'support'  # => Token
    reward = 'reward'  # => Token
    include = 'include'  # => Token
    exchange = 'exchange'  # => Project
