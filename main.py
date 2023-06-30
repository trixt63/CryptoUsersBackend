import datetime
import os
import time
import warnings

import redis
from sanic.response import text
from sanic_ext import openapi

from app import create_app
from app.apis import api
from app.databases.mongodb.async_blockchain_etl import AsyncBlockchainETL
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.mongodb.mongodb_community import MongoDBCommunity
from app.databases.postgresdb.token_transfer import TokenTransferDB
from app.misc.log import log
from config import Config, LocalDBConfig, RedisConfig, BlockchainETLConfig

warnings.filterwarnings('ignore')

app = create_app(Config, LocalDBConfig)
app.ext.openapi.add_security_scheme('Authorization', 'apiKey', location='header', name='Authorization')
app.blueprint(api)


@app.before_server_start
async def setup_db(_):
    app.ctx.db = MongoDB()
    log(f'Connected to KLG Database {app.ctx.db.connection_url}')

    app.ctx.community_db = MongoDBCommunity()
    log(f'Connected to Community Database {app.ctx.community_db.connection_url}')

    app.ctx.mongo = BlockchainETL(BlockchainETLConfig.TEST_CONNECTION_URL)
    app.ctx.etl = BlockchainETL(BlockchainETLConfig.CONNECTION_URL)
    app.ctx.async_mongo = AsyncBlockchainETL(BlockchainETLConfig.TEST_CONNECTION_URL)

    app.ctx.transfer_db = TokenTransferDB()


@app.before_server_start
async def setup_cache(_):
    app.ctx.redis = redis.from_url(RedisConfig.CONNECTION_URL)
    log(f'Setup Redis cached')


@app.route("/ping", methods={'GET'})
@openapi.tag("Ping")
@openapi.summary("Ping server !")
async def hello_world(request):
    return text("Hello, World !!!")


@app.middleware('request')
async def add_start_time(request):
    request.headers['start_time'] = time.time()


@app.middleware('response')
async def add_spent_time(request, response):
    try:
        if 'start_time' in request.headers:
            timestamp = request.headers['start_time']
            spend_time = round((time.time() - timestamp), 3)
            response.headers['latency'] = spend_time

            if response.status >= 400:
                log_level = 'ERROR'
            elif response.status >= 300:
                log_level = 'WARN'
            else:
                log_level = 'INFO'
            log("[{timestamp}] {status} {method} {path} {query} {latency}s".format(
                timestamp=datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                status=response.status,
                method=request.method,
                path=request.path,
                query=request.query_string,
                latency=spend_time
            ), keyword=log_level)
    except Exception as ex:
        log(ex.__str__(), 'ERROR')


if __name__ == '__main__':
    if 'SECRET_KEY' not in os.environ:
        log(message='SECRET KEY is not set in the environment variable.',
            keyword='WARN')

    try:
        app.run(**app.config['RUN_SETTING'])
    except (KeyError, OSError):
        log('End Server...')
