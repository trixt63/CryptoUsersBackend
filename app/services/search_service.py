from typing import Union

from web3 import Web3

from app.constants.search_constants import SearchConstants
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.utils.format_utils import short_address
from app.utils.list_dict_utils import check_intersect
from app.utils.search_data_utils import is_transaction_valid


class SearchService:
    def __init__(self, graph: Union[MongoDB, KLGDatabase], mongo: BlockchainETL, blockchain_etl: BlockchainETL, klg: KLGDatabase = None):
        self.graph = graph

        self.mongo = mongo
        self.blockchain_etl = blockchain_etl

        self.klg = klg

    def search(self, keyword, chains, type_=None):
        # Hash, number: Search keyword in multichain transactions, blocks data
        if is_transaction_valid(keyword) or keyword.isnumeric():
            return self.search_transaction_and_block(keyword, chains)

        # Address: Search in wallets, smart_contracts collection
        elif Web3.isAddress(keyword):
            return self.search_address(keyword, chains, type_=type_)

        # Text: Fuzzy search by entities name
        else:
            # Search text coming soon
            # return self.search_text(keyword, chains, type_=type_, limit=limit)
            return []

    def search_transaction_and_block(self, keyword, chains):
        for db in [self.mongo, self.blockchain_etl]:
            results = self.search_transaction(keyword, chains, db)
            if results:
                return results

            results = self.search_block(keyword, chains, db)
            if results:
                return results

        return []

    def search_block(self, keyword, chains, db=None):
        if db is None:
            db = self.mongo

        for chain in chains:
            block = db.get_block(chain, keyword)
            if block:
                # TODO: get all block by number in multiple chains
                return [{
                    'id': f"{chain}_{block['hash']}",
                    'type': SearchConstants.block,
                    'name': block['number'],
                    'chains': [chain]
                }]

        return []

    def search_transaction(self, keyword, chains, db=None):
        if db is None:
            db = self.mongo

        for chain in chains:
            tx = db.get_transaction(chain, keyword)
            if tx:
                return [{
                    'id': f'{chain}_{keyword}',
                    'type': SearchConstants.transaction,
                    'name': short_address(keyword, n_start=18, n_end=-len(keyword)),
                    'chains': [chain]
                }]

        return []

    def search_address(self, keyword, chains, type_=None):
        if not type_:
            return [{
                'id': keyword,
                'type': SearchConstants.wallet,
                'name': short_address(keyword),
                'chains': chains
            }]

        contracts = self.graph.get_contracts_by_address(
            keyword, chains,
            projection=['address', 'chainId', 'tags', 'name', 'idCoingecko']
        )
        results = []
        for contract in contracts:
            chain_id = contract['chainId']
            address = contract['address']
            tags = contract.get('tags') or []
            contract_type = SearchConstants.token if 'token' in tags else SearchConstants.contract
            if (contract_type == type_) and (chain_id in chains):
                id_ = contract['idCoingecko'] if contract.get('idCoingecko') else f"{chain_id}_{address}"
                results.append({
                    'id': id_,
                    'type': contract_type,
                    'name': contract.get('name') or short_address(address),
                    'chains': [chain_id]
                })

        return results

    def search_text(self, keyword, chains, type_=None, limit=10):
        data = self.klg.get_project_contract_list_by_text(keyword)
        projects = get_projects(data, chains, type_, limit)
        contracts = get_contracts(data, chains, type_, limit)
        results = list(projects.values()) + list(contracts.values())
        return results


def get_projects(data, chains, type_, limit):
    projects = {}
    if (not type_) or (type_ == SearchConstants.project):
        for project in data["projects"]:
            project_id = project['_key']
            chains_ = check_intersect(list(project.get("deployedChains", {}).keys()), chains)
            if chains_ and (len(projects) < limit):
                projects[project_id] = {
                    'id': project_id,
                    'type': SearchConstants.project,
                    'name': project['name'],
                    'chains': chains_
                }
    return projects


def get_contracts(data, chains, type_, limit):
    contracts = {}
    for smart_contract in data["smart_contracts"]:
        if (smart_contract["chainId"] in chains) and (len(contracts) < limit):
            contract_id = smart_contract['_key']
            tags = smart_contract.get('tags') or {}

            contract_address = smart_contract['address']
            contract_type = SearchConstants.token if tags.get('token') else SearchConstants.contract
            if type_ and contract_type != type_:
                continue

            id_ = contract_id
            if (contract_type == SearchConstants.token) and smart_contract.get('idCoingecko'):
                id_ = smart_contract.get('idCoingecko')

            contracts[contract_id] = {
                'id': id_,
                'type': contract_type,
                'chains': [smart_contract["chainId"]],
                'name': smart_contract.get('name') or short_address(contract_address)
            }

    return contracts
