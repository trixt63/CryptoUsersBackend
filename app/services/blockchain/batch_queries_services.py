from query_state_lib.base.mappers.eth_call_mapper import EthCall
from query_state_lib.base.utils.encoder import encode_eth_call_data
from web3 import Web3


def add_rpc_call(abi, fn_name, contract_address, block_number=None, fn_paras=None, list_rpc_call=None,
                 list_call_id=None):
    args = []
    if fn_paras is not None:
        if type(fn_paras) is list:
            for i in range(len(fn_paras)):
                if Web3.isAddress(fn_paras[i]):
                    fn_paras[i] = Web3.toChecksumAddress(fn_paras[i])
            args = fn_paras
        else:
            if Web3.isAddress(fn_paras):
                fn_paras = Web3.toChecksumAddress(fn_paras)
            args = [fn_paras]

        call_id = f"{fn_name}_{contract_address}_{fn_paras}".lower()
    else:
        call_id = f"{fn_name}_{contract_address}".lower()

    data_call = encode_eth_call_data(abi=abi, fn_name=fn_name, args=args)
    if block_number:
        call_id = call_id+f"_{block_number}"
        eth_call = EthCall(to=Web3.toChecksumAddress(contract_address), block_number=block_number, data=data_call,
                           abi=abi, fn_name=fn_name, id=call_id)
    else:
        eth_call = EthCall(to=Web3.toChecksumAddress(contract_address), data=data_call,
                           abi=abi, fn_name=fn_name, id=call_id)

    if call_id not in list_call_id:
        list_rpc_call.append(eth_call)
        list_call_id.append(call_id)


def decode_data_response(data_responses, list_call_id):
    decoded_datas = {}
    for call_id in list_call_id:
        decoded_data = data_responses.get(call_id).decode_result()
        if len(decoded_data) == 1:
            decoded_datas[call_id] = decoded_data[0]
        else:
            decoded_datas[call_id] = decoded_data
    return decoded_datas
