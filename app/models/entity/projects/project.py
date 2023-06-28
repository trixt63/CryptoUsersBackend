from typing import List

from app.constants.network_constants import EMPTY_TOKEN_IMG
from app.models.entity.contract import Contract
from app.models.entity.token import Token
from app.models.explorer.node import Node


class ProjectTypes:
    defi = 'defi'
    nft = 'nft'
    exchange = 'exchange'

    mapping = {
        'defillama': defi,
        'nft': nft,
        'spot_exchange': exchange,
        'derivative_exchange': exchange
    }


class Project:
    def __init__(self, key, project_type=ProjectTypes.defi):
        self.id = f'project/{key}'
        self.key = key
        self.name = ''
        self.type = 'project'
        self.img_url = ''
        self.chains = []
        self.description = ''
        self.project_type = project_type
        self.rank = 0
        self.tags = []
        self.url = ''
        self.social_networks = {}
        self.tokens: List[Token] = []
        self.contracts: List[Contract] = []

        self.metadata = {}

    @classmethod
    def from_dict(cls, json_dict: dict, project_type=ProjectTypes.defi):
        key = json_dict['id']
        project = cls(key, project_type)
        project.name = json_dict.get('name')
        project.img_url = json_dict.get('imgUrl', EMPTY_TOKEN_IMG)
        project.chains = json_dict.get('deployedChains', [])
        project.description = json_dict.get('description')
        project.rank = cls.get_rank(json_dict, project_type)
        project.tags = [json_dict['category']] if json_dict.get('category') else []

        socials = json_dict.get('links', {})
        project.url = socials.pop('website', None) or json_dict.get('url')
        project.social_networks = socials

        tokens = json_dict.get('tokens', {})
        for chain_id, token_address in json_dict.get('tokenAddresses', {}).items():
            token_dict = tokens.get(f'{chain_id}_{token_address}')
            if token_dict:
                project.tokens.append(Token.from_dict(token_dict))

        contracts = json_dict.get('contracts', {})
        for contract_key in json_dict.get('contractAddresses', {}):
            contract_dict = contracts.get(contract_key)
            if contract_dict:
                project.contracts.append(Contract.from_dict(contract_dict))

        cls.get_metadata(project, json_dict)
        return project

    @classmethod
    def get_rank(cls, json_dict: dict, project_type):
        if project_type == ProjectTypes.defi:
            return json_dict.get('rankDefi')
        elif project_type == ProjectTypes.nft:
            return json_dict.get('rankNFT')
        elif project_type == ProjectTypes.exchange:
            return json_dict.get('rankExchange')
        return None

    def to_dict(self):
        tokens = [token.to_dict() for token in self.tokens]
        contracts = [contract.to_dict() for contract in self.contracts]

        return {
            'id': self.key,
            'projectId': self.key,
            'name': self.name,
            'imgUrl': self.img_url,
            'description': self.description,
            'chains': self.chains,
            'rank': self.rank,
            'projectType': self.project_type,
            'tags': self.tags,
            'url': self.url,
            'socialNetworks': self.social_networks,
            'tokens': tokens,
            'contracts': contracts
        }

    @classmethod
    def get_metadata(cls, obj, json_dict):
        ...

    def get_introduction(self):
        ...

    def get_overview(self):
        ...

    def get_stats(self, history=True):
        ...

    def get_visualize(self):
        ...

    def to_node(self) -> Node:
        node = Node(self.id)
        node.key = self.key
        node.type = self.type
        node.name = self.name
        node.metadata['projectType'] = self.project_type
        return node
