from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic_ext import openapi, validate

from app.apis.portfolio.utils.utils import get_chains
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.explorer.search import SearchQuery, SuggestionQuery
from app.services.search_service import SearchService

search_bp = Blueprint('search_blueprint', url_prefix='/search')


@search_bp.get('/')
@openapi.tag("Search")
@openapi.summary("Search keyword in blockchain space. Filter by chain and type of blockchain entity.")
@openapi.parameter(name="chain", description="Chain ID", schema=str, location="query")
@openapi.parameter(name="type", description="Type: transaction, block, wallet, text.", schema=str, location="query")
@openapi.parameter(name="keyword", description="Search keyword", schema=str, location="query", required=True)
@validate(query=SearchQuery)
async def search(request: Request, query: SearchQuery):
    chain_id = query.chain
    keyword = query.keyword.lower()
    type_ = query.type

    chains = get_chains(chain_id)

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    etl: BlockchainETL = request.app.ctx.etl
    search_service = SearchService(db, mongo, etl)

    results = search_service.search(keyword, chains, type_)
    return json({
        'keyword': keyword,
        'results': results
    })


@search_bp.get('/suggestion')
@openapi.tag("Search")
@openapi.summary("Suggest keywords for users to search")
@openapi.parameter(name="limit", description="Limit suggestions. Default: 5", schema=int, location="query")
@openapi.parameter(name="keyword", description="Text for search", schema=str, location="query", required=True)
@validate(query=SuggestionQuery)
async def suggest(request: Request, query: SuggestionQuery):
    keyword = query.keyword.lower()
    limit = query.limit

    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    etl: BlockchainETL = request.app.ctx.etl
    search_service = SearchService(db, mongo, etl)

    chains = get_chains(None)
    results = search_service.search_text(keyword, chains, limit=limit)

    return json({
        'keyword': keyword,
        'results': results
    })
