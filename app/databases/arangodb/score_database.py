from arango import ArangoClient
from arango.http import DefaultHTTPClient

from app.constants.network_constants import DEFAULT_CREDIT_SCORE
from app.constants.score_constants import WalletCreditScoreWeightConstant
from app.decorators.time_exe import TimeExeTag, sync_log_time_exe
from app.utils.format_utils import about
from app.utils.list_dict_utils import sort_log
from app.utils.logger_utils import get_logger
from app.utils.parser import get_connection_elements
from config import ScoreArangoConfig

logger = get_logger('Score Database')

MULTICHAIN_WALLETS_CREDIT_SCORES = 'multichain_wallets_credit_scores'
CREDIT_SCORE_CONFIGS = 'credit_score_configs'


class ScoreDatabase:
    def __init__(self, connection_url=None):
        if connection_url is None:
            connection_url = ScoreArangoConfig.CONNECTION_URL
        username, password, connection_url = get_connection_elements(connection_url)

        http_client = DefaultHTTPClient()
        http_client.REQUEST_TIMEOUT = 300

        self.connection_url = connection_url
        self.client = ArangoClient(hosts=connection_url, http_client=http_client)
        self.db = self.client.db(ScoreArangoConfig.DATABASE, username=username, password=password)

        self._score_col = self.db.collection(MULTICHAIN_WALLETS_CREDIT_SCORES)
        self._config_col = self.db.collection(CREDIT_SCORE_CONFIGS)

    @sync_log_time_exe(tag=TimeExeTag.database)
    def get_score_change_logs(self, address: str):
        query = f"""
            FOR doc IN {MULTICHAIN_WALLETS_CREDIT_SCORES}
            FILTER doc._key == '{address.lower()}'
            RETURN {{
                creditScore: doc.creditScore,
                creditScoreChangeLogs: doc.creditScoreChangeLogs
            }}
        """
        cursor = self.db.aql.execute(query)
        docs = list(cursor)
        if not docs:
            return DEFAULT_CREDIT_SCORE, {}

        credit_score = docs[0].get('creditScore') or DEFAULT_CREDIT_SCORE
        score_logs = sort_log(docs[0].get('creditScoreChangeLogs'))
        return credit_score, score_logs

    def get_score_histogram(self):
        query = """
            FOR doc IN credit_score_configs
            FILTER doc._key == 'multichain_wallets_scores'
            RETURN doc
        """
        cursor = self.db.aql.execute(query)
        docs = list(cursor)
        if not docs:
            return {}

        return docs[0]['histogram']

    def get_elite_wallets(self):
        query = """
            FOR doc IN multichain_wallets
            FILTER doc.elite == true
            RETURN doc.address
        """
        cursor = self.db.aql.execute(query, batch_size=10000)
        return cursor

    def get_score_by_addresses(self, addresses: list):
        query = f"""
            FOR doc IN {MULTICHAIN_WALLETS_CREDIT_SCORES}
            FILTER doc._key IN {addresses}
            RETURN {{
                address: doc._key,
                creditScore: doc.creditScore
            }}
        """
        cursor = self.db.aql.execute(query, batch_size=1000)
        return list(cursor)

    def set_score_histogram(self, score_histogram):
        data = {
            '_key': 'multichain_wallets_scores',
            'histogram': score_histogram
        }
        self._config_col.import_bulk([data], on_duplicate='update')

    def get_score_details(self, address):
        query = f"""
            FOR doc IN {MULTICHAIN_WALLETS_CREDIT_SCORES}
            FILTER doc._key == '{address.lower()}'
            RETURN {{
                creditScorex1: doc.creditScorex1,
                creditScorex2: doc.creditScorex2,
                creditScorex3: doc.creditScorex3,
                creditScorex4: doc.creditScorex4,
                creditScorex5: doc.creditScorex5
            }}
        """
        cursor = self.db.aql.execute(query)
        docs = list(cursor)
        if (not docs) or (not docs[0].get('creditScorex1')):
            return {}

        doc = docs[0]

        x1 = WalletCreditScoreWeightConstant.b11 * doc['creditScorex1'][0] + \
            WalletCreditScoreWeightConstant.b12 * doc['creditScorex1'][1]

        x2 = WalletCreditScoreWeightConstant.b21 * doc['creditScorex2'][0] + \
            WalletCreditScoreWeightConstant.b22 * doc['creditScorex2'][1] + \
            WalletCreditScoreWeightConstant.b23 * doc['creditScorex2'][2] + \
            WalletCreditScoreWeightConstant.b24 * doc['creditScorex2'][3] + \
            WalletCreditScoreWeightConstant.b25 * doc['creditScorex2'][4]

        x3 = about(doc['creditScorex3'][0] - (1000 - doc['creditScorex3'][1]))

        x4 = WalletCreditScoreWeightConstant.b41 * doc['creditScorex4'][0]

        x5 = WalletCreditScoreWeightConstant.b51 * doc['creditScorex5'][0] + \
            WalletCreditScoreWeightConstant.b52 * doc['creditScorex5'][1]

        return {
            'assets': x1,
            'transactions': x2,
            'loan': x3,
            'circulatingAssets': x4,
            'trustworthinessAssets': x5
        }
