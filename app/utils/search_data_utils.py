import re

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from app.constants.network_constants import Chain, BNB
from app.constants.search_constants import SearchConstants, Tags
from app.decorators.time_exe import sync_log_time_exe, TimeExeTag

eth_w3 = Web3(HTTPProvider("https://rpc.ankr.com/eth"))
eth_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

bsc_w3 = Web3(HTTPProvider("https://rpc.ankr.com/bsc"))
bsc_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

ftm_w3 = Web3(HTTPProvider("https://rpc.ankr.com/fantom"))
ftm_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

polygon_w3 = Web3(HTTPProvider("https://rpc.ankr.com/polygon"))
polygon_w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def get_w3(chain_id) -> Web3:
    if chain_id == Chain.BSC:
        return bsc_w3
    elif chain_id == Chain.ETH:
        return eth_w3
    elif chain_id == Chain.FTM:
        return ftm_w3
    elif chain_id == Chain.POLYGON:
        return polygon_w3

    raise ValueError(f'Chain {chain_id} not support')


def is_address(chain_id, address):
    w3 = get_w3(chain_id)
    return w3.isAddress(address)


def return_data(type_search, data):
    if data:
        links = data['links']
        nodes_dict = {node['id']: 1 for node in data['nodes']}
        links = filter(lambda link: (link['source'] in nodes_dict) and (link['target'] in nodes_dict), links)
        data['links'] = list(links)

        return {
            "type": type_search,
            "data": [data]
        }
    return {
        "type": type_search,
        "data": []
    }


def is_transaction_valid(tx_hash) -> bool:
    pattern = re.compile(r"^0x[a-fA-F0-9]{64}")
    return bool(re.fullmatch(pattern, tx_hash))


def get_smart_contract_type(smart_contract):
    if smart_contract:
        if smart_contract.get('tags'):
            tags = smart_contract['tags']
            if Tags.token in tags:
                return Tags.token
            elif Tags.contract in tags:
                return Tags.contract
        else:
            return smart_contract.get('type')

    return None


@sync_log_time_exe(tag=TimeExeTag.blockchain)
def is_contract(chain_id, address):
    w3 = get_w3(chain_id)
    code = w3.eth.getCode(w3.toChecksumAddress(address))
    code_str = code.hex()
    if code_str == '0x':
        return False
    else:
        return True


def get_explorer_link(chain_id, entity_id, type_):
    base_url = Chain.explorers.get(chain_id)
    if type_ == SearchConstants.block:
        url = f'{base_url}block/{entity_id}'
    elif type_ == SearchConstants.transaction:
        url = f'{base_url}tx/{entity_id}'
    elif type_ == SearchConstants.token:
        if entity_id != BNB:
            url = f'{base_url}token/{entity_id}'
        else:
            url = base_url
    else:
        url = f'{base_url}address/{entity_id}'
    return url
