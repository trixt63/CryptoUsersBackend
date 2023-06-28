import copy
from typing import List

from eth_utils import encode_hex, function_abi_to_4byte_selector
from hexbytes import HexBytes
from web3._utils.encoding import to_4byte_hex

from app.decorators.time_exe import sync_log_time_exe, TimeExeTag

METHOD_NOT_FOUND = ValueError('Could not find any function matching transaction input')


def check_func(fn_abi, signature_encode):
    return encode_hex(function_abi_to_4byte_selector(fn_abi)) == signature_encode


def get_signatures(contract_abi: List[dict]):
    func_abi = []
    for abi in contract_abi:
        if abi['type'] == 'function':
            _abi = copy.deepcopy(abi)
            _abi['signature'] = encode_hex(function_abi_to_4byte_selector(abi))
            func_abi.append(_abi)
    return func_abi


def decode_func_name(contract_abi, tx_input):
    data = HexBytes(tx_input)
    selector = data[:4]
    signature_encode = to_4byte_hex(selector)

    func_abi = get_signatures(contract_abi)
    fns = [abi['name'] for abi in func_abi if abi.get('signature') == signature_encode]
    if not fns:
        raise METHOD_NOT_FOUND

    return fns[0]
