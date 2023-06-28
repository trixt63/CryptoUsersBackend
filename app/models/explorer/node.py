import copy

from app.constants.search_constants import SearchConstants, Tags
from app.utils.format_utils import short_address
from app.utils.search_data_utils import get_smart_contract_type


class Node:
    def __init__(self, id_):
        self.id = id_
        self.key: str = ''
        self.type: str = ''
        self.name: str = ''

        self.metadata = {}

    @classmethod
    def from_dict(cls, json_dict):
        id_ = f"{json_dict['type']}/{json_dict['key']}"
        node = Node(id_)
        node.key = json_dict['key']
        node.type = json_dict['type']
        node.name = json_dict.get('name')
        return node

    def to_dict(self):
        return copy.deepcopy(self.__dict__)

    @classmethod
    def wallet_node(cls, address):
        return cls.from_dict({'key': address, 'type': SearchConstants.wallet, 'name': short_address(address)})

    @classmethod
    def token_node(cls, contract):
        key = contract.get('idCoingecko') or contract.get('_key') or contract.get('_id') or contract.get('id')
        if not key:
            key = f"{contract['chainId']}_{contract['address']}"
        name = contract.get('name') or short_address(contract['address'])
        return cls.from_dict({'key': key, 'type': SearchConstants.token, 'name': name})

    @classmethod
    def contract_node(cls, contract):
        contract_type = get_smart_contract_type(contract)
        if contract_type == Tags.token:
            return cls.token_node(contract)
        elif contract_type == Tags.contract:
            key = contract.get('_key') or contract.get('_id') or contract.get('id') or f"{contract['chainId']}_{contract['address']}"
            name = contract.get('name') or short_address(contract['address'])
            return cls.from_dict({'key': key, 'type': SearchConstants.contract, 'name': name})
        else:
            return cls.wallet_node(contract['address'])

    @classmethod
    def project_node(cls, project):
        self = cls.from_dict(project)
        self.metadata['projectType'] = project.get('projectType')
        return self

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
