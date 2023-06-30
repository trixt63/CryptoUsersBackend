import os

from dotenv import load_dotenv

from app.constants.network_constants import Chain

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    RUN_SETTING = {
        'host': os.environ.get('SERVER_HOST', 'localhost'),
        'port': int(os.environ.get('SERVER_PORT', 8080)),
        'debug': os.getenv('DEBUG', False),
        "access_log": False,
        "auto_reload": True,
        'workers': int(os.getenv('SERVER_WORKERS', 4))
    }
    # uWSGI를 통해 배포되어야 하므로, production level에선 run setting을 건드리지 않음

    SECRET = os.environ.get('SECRET_KEY', 'example project')
    JWT_PASSWORD = os.getenv('JWT_PASSWORD', 'dev123')
    EXPIRATION_JWT = 2592000  # 1 month
    RESPONSE_TIMEOUT = 900  # seconds

    FALLBACK_ERROR_FORMAT = 'json'

    OAS_UI_DEFAULT = 'swagger'
    SWAGGER_UI_CONFIGURATION = {
        'apisSorter': "alpha",
        'docExpansion': "list",
        'operationsSorter': "alpha"
    }

    API_HOST = os.getenv('API_HOST', '0.0.0.0:8096')
    API_SCHEMES = os.getenv('API_SCHEMES', 'http')
    API_VERSION = os.getenv('API_VERSION', '0.1.0')
    API_TITLE = os.getenv('API_TITLE', 'Centic API')
    API_DESCRIPTION = os.getenv('API_DESCRIPTION', 'Swagger for Centic API')
    API_CONTACT_EMAIL = os.getenv('API_CONTACT_EMAIL', 'example@gmail.com')


class LocalDBConfig:
    pass


class RemoteDBConfig:
    pass


class ArangoDBGraphConfig:
    USERNAME = os.environ.get("ARANGO_GRAPH_USERNAME") or "just_for_dev"
    PASSWORD = os.environ.get("ARANGO_GRAPH_PASSWORD") or "password_for_dev"
    HOST = os.environ.get("ARANGO_GRAPH_HOST") or "localhost"
    PORT = os.environ.get("ARANGO_GRAPH_PORT") or "8529"

    CONNECTION_URL = os.getenv("ARANGO_GRAPH_URL") or f"arangodb@{USERNAME}:{PASSWORD}@http://{HOST}:{PORT}"

    DATABASE = os.getenv('ARANGO_GRAPH_DB', 'klg_database')


class MongoDBConfig:
    CONNECTION_URL = os.getenv("MONGODB_CONNECTION_URL")
    DATABASE = os.getenv('MONGODB_DATABASE', 'knowledge_graph')


class MongoDBCommunityConfig:
    CONNECTION_URL = os.getenv("MONGODB_COMMUNITY_CONNECTION_URL")
    DATABASE = os.getenv('MONGODB_COMMUNITY_DATABASE', 'TokenDatabase')


class ScoreArangoConfig:
    CONNECTION_URL = os.getenv("SCORE_ARANGO_URL")
    DATABASE = os.getenv('SCORE_ARANGO_DB', 'klg_database')


class RedisConfig:
    CONNECTION_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')


class BlockchainETLConfig:
    CONNECTION_URL = os.environ.get('BLOCKCHAIN_ETL_CONNECTION_URL')
    TEST_CONNECTION_URL = os.environ.get('TEST_BLOCKCHAIN_ETL_CONNECTION_URL')

    BNB_DATABASE = os.environ.get("BNB_DATABASE") or "blockchain_etl"
    ETHEREUM_DATABASE = os.environ.get("ETHEREUM_DATABASE") or "ethereum_blockchain_etl"
    FANTOM_DATABASE = os.environ.get("FANTOM_DATABASE") or "ftm_blockchain_etl"
    POLYGON_DATABASE = os.environ.get("POLYGON_DATABASE") or "polygon_blockchain_etl"


class ArangoDBLendingConfig:
    USERNAME = os.environ.get("ARANGO_LENDING_USERNAME") or "just_for_dev"
    PASSWORD = os.environ.get("ARANGO_LENDING_PASSWORD") or "password_for_dev"
    CONNECTION_URL = os.environ.get("ARANGO_LENDING_URL") or None


class TokenMongoDBConfig:
    MONGODB_HOST = os.environ.get("TOKEN_MONGO_HOST", '0.0.0.0')
    MONGODB_PORT = os.environ.get("TOKEN_MONGO_PORT", '27017')
    USERNAME = os.environ.get("TOKEN_MONGO_USERNAME", "admin")
    PASSWORD = os.environ.get("TOKEN_MONGO_PASSWORD", "admin123")
    CONNECTION_URL = os.environ.get('TOKEN_MONGO_CONNECTION_URL') or f'mongodb://{USERNAME}:{PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}'

    TOKEN_DATABASE = 'TokenDatabase'


class PostgresDBConfig:
    TRANSFER_EVENT_TABLE = os.environ.get("POSTGRES_TRANSFER_EVENT_TABLE", "transfer_event")
    CONNECTION_URL_1 = os.environ.get("POSTGRES_CONNECTION_URL_1", "postgresql://user:password@localhost:5432/database")
    CONNECTION_URL_2 = os.environ.get("POSTGRES_CONNECTION_URL_2", "postgresql://user:password@localhost:5432/database")

    CONNECTION_URLS = {
        CONNECTION_URL_1: [Chain.BSC, Chain.FTM],
        CONNECTION_URL_2: [Chain.ETH, Chain.POLYGON]
    }
