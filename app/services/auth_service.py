import datetime
import random

import jwt
from eth_account import messages
from web3 import HTTPProvider
from web3 import Web3

from config import Config
from app.utils.logger_utils import get_logger

logger = get_logger('Auth Service')


class AuthService:
    def __init__(self, provider_uri):
        self.web3 = Web3(HTTPProvider(provider_uri))

    def recover_hash(self, message_hash, signature):
        address = self.web3.eth.account.recoverHash(
            message_hash=str(message_hash), signature=str(signature))
        return address

    def is_address(self, address):
        return self.web3.isAddress(address)

    def login_with_metamask(self, address, signature, nonce, role, secret_key):
        msg = f"I am signing my one-time nonce: {nonce}" + \
              "\n\n" + \
              "Note: Sign to log into your Centic account. This is free and will not require a transaction."

        message = messages.encode_defunct(text=msg)
        message_hash = messages._hash_eip191_message(message)
        hex_message_hash = Web3.toHex(message_hash)

        _address = self.recover_hash(message_hash=hex_message_hash, signature=signature)
        if (not _address) or (_address.lower() != address.lower()):
            raise ValueError

        jwt_ = generate_jwt(address, role, secret_key)
        return jwt_


def generate_jwt(wallet_address, role, secret_key, expire=Config.EXPIRATION_JWT):
    expiration_time = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=expire)

    token = jwt.encode(
        {
            "address": wallet_address,
            "exp": expiration_time,
            "role": role
        },
        secret_key
    )

    return str(token)


def random_nonce():
    return random.randint(0, 1000000)
