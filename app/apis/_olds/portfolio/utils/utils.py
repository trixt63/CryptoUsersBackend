from sanic.exceptions import BadRequest
from web3 import Web3

from app.constants.network_constants import Chain


def check_address(address: str):
    if not Web3.isAddress(address):
        raise BadRequest(f'Invalid wallet address: {address}')
    return address.lower()


def get_chains(chain_id):
    all_chains = Chain().get_all_chain_id()
    if (chain_id is None) or (chain_id == 'all'):
        chains = all_chains
    elif chain_id not in all_chains:
        raise BadRequest(f'Not supported chain or invalid chain: {chain_id}')
    else:
        chains = [chain_id]
    return chains
