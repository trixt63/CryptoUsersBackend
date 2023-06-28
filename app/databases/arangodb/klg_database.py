from arango import ArangoClient
from arango.http import DefaultHTTPClient

from app.constants.arangodb_graph_constants import ArangoDBGraphConstant
from app.constants.search_constants import SearchConstants
from app.decorators.time_exe import sync_log_time_exe, TimeExeTag
from app.utils.logger_utils import get_logger
from app.utils.parser import get_connection_elements
from app.utils.search_data_utils import get_smart_contract_type
from config import ArangoDBGraphConfig

logger = get_logger('KLG Database')


class KLGDatabase:
    def __init__(self, connection_url=None):
        if connection_url is None:
            connection_url = ArangoDBGraphConfig.CONNECTION_URL
        username, password, connection_url = get_connection_elements(connection_url)

        http_client = DefaultHTTPClient()
        http_client.REQUEST_TIMEOUT = 300

        self.connection_url = connection_url
        self.client = ArangoClient(hosts=connection_url, http_client=http_client)
        self.db = self.client.db(ArangoDBGraphConfig.DATABASE, username=username, password=password)

        self._projects_col = self.db.collection(ArangoDBGraphConstant.PROJECTS)
        self._smart_contracts_col = self.db.collection(ArangoDBGraphConstant.SMART_CONTRACTS)
        self._wallets_col = self.db.collection(ArangoDBGraphConstant.WALLETS)
        self._configs_col = self.db.collection(ArangoDBGraphConstant.CONFIGS)

    def count_documents(self, collection_name):
        query = f"""
            FOR doc IN {collection_name}
                COLLECT WITH COUNT INTO length
                RETURN length
        """
        cursor = self.db.aql.execute(query)
        return list(cursor)[0]

    #######################
    #      Project        #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_projects_by_type(self, type_=None, sort_by=None, reverse=False, skip=None, limit=None, chain=None, category=None, last_updated_at=None, projection=None):
        filter_statement = ""
        if type_ is not None:
            filter_statement += f"\n FILTER doc.sources.{type_} == true"
        if chain is not None:
            filter_statement += f"\n FILTER doc.deployedChains['{chain}'] == true"
        if category is not None:
            filter_statement += f"\n FILTER doc.category == '{category}'"
        if last_updated_at is not None:
            if type_ is not None:
                filter_statement += f"\n FILTER doc.lastUpdated.{type_} > {last_updated_at}"
            else:
                filter_statement += f"\n FILTER doc.lastUpdatedAt > {last_updated_at}"
        filter_statement += self.get_pagination_statement(sort_by, reverse, skip, limit)
        projection_statement = self.get_projection_statement(projection)

        query = f"""
            FOR doc IN {ArangoDBGraphConstant.PROJECTS}
            {filter_statement}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    @sync_log_time_exe(tag=TimeExeTag.database)
    def count_projects_by_type(self, type_=None, chain=None, category=None, last_updated_at=None):
        filter_statement = ""
        if type_ is not None:
            filter_statement += f"\n FILTER doc.sources.{type_} == true"
        if chain is not None:
            filter_statement += f"\n FILTER doc.deployedChains['{chain}'] == true"
        if category is not None:
            filter_statement += f"\n FILTER doc.category == '{category}'"
        if last_updated_at is not None:
            if type_ is not None:
                filter_statement += f"\n FILTER doc.lastUpdated.{type_} > {last_updated_at}"
            else:
                filter_statement += f"\n FILTER doc.lastUpdatedAt > {last_updated_at}"

        query = f"""
            FOR doc IN {ArangoDBGraphConstant.PROJECTS}
            {filter_statement}
                COLLECT WITH COUNT INTO length
                RETURN length
        """
        cursor = self.db.aql.execute(query)
        return list(cursor)[0]

    def get_project(self, project_id, projection=None):
        projection_statement = self.get_projection_statement(projection)
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.PROJECTS}
            FILTER doc._key == '{project_id}'
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query)
        projects = list(cursor)
        return projects[0] if projects else None

    #######################
    #      Contract       #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contracts_by_type(self, type_=None, chain_id=None, sort_by=None, reverse=False, skip=None, limit=None, projection=None, last_updated_at=None):
        filter_statement = ""
        if type_ is not None:
            if type_ == 'token':
                filter_statement += f"\n FILTER doc.idCoingecko != null"
            else:
                filter_statement += f"\n FILTER doc.tags.{type_} == true"
        if chain_id is not None:
            filter_statement += f"\n FILTER doc.chainId == '{chain_id}'"
        if last_updated_at is not None:
            if type_ is not None:
                filter_statement += f"\n FILTER doc.lastUpdated.{type_} > {last_updated_at}"
            else:
                filter_statement += f"\n FILTER doc.lastUpdatedAt > {last_updated_at}"
        filter_statement += self.get_pagination_statement(sort_by, reverse, skip, limit)

        projection_statement = self.get_projection_statement(projection)

        query = f"""
            FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
            {filter_statement}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    def count_contracts_by_type(self, type_=None, last_updated_at=None):
        filter_statement = ""
        if type_ is not None:
            if type_ == 'token':
                filter_statement += f"\n FILTER doc.idCoingecko != null"
            else:
                filter_statement += f"\n FILTER doc.tags.{type_} == true"
        if last_updated_at is not None:
            if type_ is not None:
                filter_statement += f"\n FILTER doc.lastUpdated.{type_} > {last_updated_at}"
            else:
                filter_statement += f"\n FILTER doc.lastUpdatedAt > {last_updated_at}"

        query = f"""
            FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
            {filter_statement}
                COLLECT WITH COUNT INTO length
                RETURN length
        """
        cursor = self.db.aql.execute(query)
        return list(cursor)[0]

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contracts_by_keys(self, keys, projection=None):
        projection_statement = self.get_projection_statement(projection)
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
            FILTER doc._key IN {keys}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contract_by_key(self, key, projection=None):
        projection_statement = self.get_projection_statement(projection)
        query = f"""
                FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
                FILTER doc._key == '{key}'
                RETURN {projection_statement}
            """
        cursor = self.db.aql.execute(query, batch_size=1000)
        contracts = list(cursor)
        if not contracts:
            return None
        return contracts[0]

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_protocols(self, projection=None):
        projection_statement = self.get_projection_statement(projection)
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
            FILTER doc.lendingInfo
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_contracts_by_address(self, address, chains, projection=None):
        keys = [f'{chain}_{address}' for chain in chains]
        projection_statement = self.get_projection_statement(projection)
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
            FILTER doc._key IN {keys}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    #######################
    #       Token         #
    #######################

    def get_token_by_id_coingecko(self, coin_id, chain_id=None, projection=None):
        filter_statement = f"FILTER doc.idCoingecko == '{coin_id}'"
        if chain_id is not None:
            filter_statement += f"\n FILTER doc.chainId == '{chain_id}'"

        projection_statement = self.get_projection_statement(projection)
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
            {filter_statement}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query)
        return cursor

    def get_tokens_by_id(self, token_id, chains, projection=None):
        chain_id = token_id.split('_')[0]
        if chain_id in chains:
            filter_statement = f"FILTER doc._key == '{token_id}'"
        else:
            filter_statement = f"FILTER doc.idCoingecko == '{token_id}' AND doc.chainId IN {chains}"

        if (projection is not None) and ('tags' not in projection):
            projection.append('tags')
        projection_statement = self.get_projection_statement(projection)
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.SMART_CONTRACTS}
            {filter_statement}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query)

        tokens = []
        for doc in cursor:
            contract_type = get_smart_contract_type(doc)
            if contract_type != SearchConstants.token:
                continue
            tokens.append(doc)
        return tokens

    #######################
    #      Wallet         #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_wallet_by_address(self, address, chain_id=None, projection=None):
        if chain_id:
            filter_statement = f"FILTER doc._key == '{chain_id}_{address}'"
        else:
            filter_statement = f"FILTER doc.address == '{address}'"

        projection_statement = self.get_projection_statement(projection)

        query = f"""
            FOR doc IN {ArangoDBGraphConstant.WALLETS}
            {filter_statement}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return list(cursor)

    def get_elite_wallets(self):
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.WALLETS}
            FILTER doc.elite == true
            RETURN doc.address
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    def insert_new_wallets(self, new_wallets):
        data = []
        configs = []
        for key in new_wallets:
            chain_id, address = key.split('_')
            data.append({
                '_key': key,
                'address': address,
                'chainId': chain_id,
                'newTarget': True
            })
            configs.append({
                '_key': f'wallet_flags_{chain_id}',
                'newTarget': {address: True}
            })
        self._wallets_col.import_bulk(data, on_duplicate='update')
        self._configs_col.import_bulk(configs, on_duplicate='update')

    # Get wallet credit score information
    # def get_wallet_credit_score(self, address):
    #     query = f"""
    #                 FOR doc IN {ArangoDBGraphConstant.WALLETS}
    #                 FILTER doc._key == '{address}'
    #                 RETURN doc
    #             """
    #     cursor = self.db.aql.execute(query, batch_size=1000)
    #     return cursor

    def get_wallets(self, keys: list, projection=None):
        projection_statement = self.get_projection_statement(projection)

        query = f"""
            FOR doc IN {ArangoDBGraphConstant.WALLETS}
            FILTER doc._key IN {keys}
            RETURN {projection_statement}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    def update_wallets(self, data):
        self._wallets_col.import_bulk(data, sync=True, on_duplicate='update', batch_size=1000)

    #######################
    #        ABI          #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_abi(self, abi_names):
        query = f"""
            FOR doc IN {ArangoDBGraphConstant.ABI}
            FILTER doc._key IN {abi_names}
            RETURN doc
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return cursor

    #######################
    #       Search        #
    #######################

    def get_project_contract_list_by_text(self, text, ngram_threshold=0.3, limit=20):
        for word in ["finance", "swap", "pool", "protocol", "dex"]:
            tmp = text.replace(word, "")
            if " " not in text:
                continue
            elif len(tmp) < 5:
                text = text.replace(" ", "")
            else:
                text = tmp

        query = f"""
            let projects = (FOR doc IN project_inv_text
            SEARCH doc.name IN TOKENS("{text}", "text_en")
            RETURN doc)
            let sc = (FOR doc IN sc_inv_text
            SEARCH doc.name IN TOKENS("{text}", "text_en")
            RETURN doc)
            return {{
                "projects": projects,
                "smart_contracts": sc
            }}
        """
        data = list(self.db.aql.execute(query, count=True))
        query = f'''
            let projects_start = (FOR doc IN project_inv_text
            SEARCH PHRASE(doc.name, {{STARTS_WITH: TOKENS("{text[0:3]}", "text_en")[0]}}, "text_en")
            RETURN doc)
            let projects_n_gram = (FOR doc IN project_ngram
                SEARCH NGRAM_MATCH(
                    doc.name,
                    "{text}",
                    {ngram_threshold},    // theshold
                    "trigram" 
                    )
                    limit {limit}
                RETURN doc)
            let projects = append(projects_start, projects_n_gram,true)
            let sc_start = (FOR doc IN sc_inv_text
            SEARCH PHRASE(doc.name, {{STARTS_WITH: TOKENS("{text[0:3]}", "text_en")[0]}}, "text_en")
            RETURN doc)
            let sc_n_gram = (FOR doc IN sc_inv_ngram
                SEARCH NGRAM_MATCH(
                    doc.name,
                    "{text}",
                    {ngram_threshold},    // theshold
                    "trigram" 
                    )
                    limit {limit}
                RETURN doc)
            let sc = append(sc_start, sc_n_gram,true)
            return {{
                "projects": projects,
                "smart_contracts": sc
            }}

        '''
        fuzzy_data = list(self.db.aql.execute(query, count=True))
        data[0]["projects"] += fuzzy_data[0]["projects"]
        data[0]["smart_contracts"] += fuzzy_data[0]["smart_contracts"]

        return data[0]

    #######################
    #       Configs       #
    #######################

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_config(self, key):
        try:
            config = self._configs_col.get({'_key': key})
            return config
        except Exception as ex:
            logger.exception(ex)
        return {}

    #######################
    #    Static method    #
    #######################

    @staticmethod
    def get_pagination_statement(sort_by, reverse: bool = False, skip: int = 0, limit: int = None):
        filter_statements = ''
        if sort_by is not None:
            filter_statements += f"\n SORT doc.{sort_by} {'DESC' if reverse else 'ASC'}"
        if limit is not None:
            if skip is not None:
                limit_statement = f'\n LIMIT {skip}, {limit}'
            else:
                limit_statement = f"\n LIMIT {limit}"
            filter_statements += limit_statement
        return filter_statements

    @staticmethod
    def get_projection_statement(projection: list = None):
        if projection is None:
            return 'doc'

        if '_key' not in projection:
            projection.append('_key')

        projection_statements = []
        for field in projection:
            if '.' in field:
                base_field, nested_field, *f = field.split('.')
                projection_statements.append(f'"{field}": doc.{base_field}["{nested_field}"]')
            else:
                projection_statements.append(f'"{field}": doc.{field}')

        statement = '{' + ','.join(projection_statements) + '}'
        return statement
