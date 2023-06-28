from configparser import ConfigParser

from tests.utils.common_utils import split_config

config = ConfigParser()
config.read('tests/.config/parameters.ini')


class AuthParams:
    _params = dict(config.items('auth'))
    _params['nonce'] = int(_params['nonce'])
    names, values = split_config(_params)


class SearchTransactionParams:
    _params = dict(config.items('search'))
    names = ['tx_hash']
    values = [_params.get('tx_hash')]


class SearchBlockParams:
    _params = dict(config.items('search'))
    names = 'block'
    values = [_params.get('block_number'), _params.get('block_hash')]


class TransactionParams:
    _params = dict(config.items('transaction'))
    names = ['tx_id']
    values = [_params.get('tx_id')]


class BlockParams:
    _params = dict(config.items('block'))
    names = ['block_id']
    values = [_params.get('block_id')]
