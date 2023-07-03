from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound
from sanic_ext import openapi

from app.constants.search_constants import SearchConstants, RelationshipType
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.models.entity.block import Block
from app.models.entity.transaction import Transaction
from app.models.explorer.link import Link
from app.models.explorer.visualization import Visualization
from app.services.transaction_services import TransactionService
from app.utils.search_data_utils import get_explorer_link

blocks_bp = Blueprint('blocks_blueprint', url_prefix='/blocks')


@blocks_bp.get('/<id_>/introduction')
@openapi.tag("Block")
@openapi.summary("Get block introduction")
@openapi.parameter(name="id_", description="Entity ID", schema=str, location="path", required=True)
async def get_block_introduction(request: Request, id_):
    chain_id, block_hash = id_.lower().split('_')

    block = _get_block(request, block_hash, chain_id, get_transactions=False, get_decode_tx_method=False)
    return json({
        'id': id_,
        'number': block.number,
        'hash': block.hash,
        'name': block.number,
        "explorerUrls": [get_explorer_link(chain_id, block.number, SearchConstants.block)],
        "chains": [chain_id]
    })


@blocks_bp.get('/<id_>/overview')
@openapi.tag("Block")
@openapi.summary("Get block overview")
@openapi.parameter(name="id_", description="Block ID", schema=str, location="path", required=True)
async def get_block(request: Request, id_):
    chain_id, block_hash = id_.lower().split('_')

    block = _get_block(request, block_hash, chain_id, get_transactions=False, get_decode_tx_method=False)

    data = block.to_dict()

    data["explorerUrl"] = get_explorer_link(chain_id, block.number, type_=SearchConstants.block)
    if block.miner:
        data["validatedBy"] = {
            "id": block.miner,
            "type": "wallet",
            "address": block.miner,
            "explorerUrl": get_explorer_link(chain_id, block.miner, type_=SearchConstants.wallet)
        }
    
    return json(data)


@blocks_bp.get('/<id_>/transactions')
@openapi.tag("Block")
@openapi.summary("Get block's transactions")
@openapi.parameter(name="id_", description="Block ID", schema=str, location="path", required=True)
async def get_block_transactions(request: Request, id_):
    chain_id, block_hash = id_.lower().split('_')

    block = _get_block(request, block_hash, chain_id, get_transactions=True, get_decode_tx_method=True)
    transactions = block.get_transactions_dict()

    return json({
        'id': id_,
        'numberOfTransactions': block.transactions_count,
        'transactions': transactions
    })


@blocks_bp.get('/<id_>/visualize')
@openapi.tag("Block")
@openapi.summary("Get block visualize information")
@openapi.parameter(name="id_", description="Block ID", schema=str, location="path", required=True)
async def get_visualize(request: Request, id_):
    chain_id, block_hash = id_.lower().split('_')

    block = _get_block(request, block_hash, chain_id, get_transactions=True, get_decode_tx_method=False)

    visualize = Visualization()
    for transaction in block.transactions:
        from_node = transaction.from_.to_node()
        visualize.add_node(from_node)

        to_node = transaction.to_.to_node()
        visualize.add_node(to_node)

        link_type = RelationshipType.transfer if to_node.type == SearchConstants.wallet else RelationshipType.call_contract
        link = Link.from_dict({'source': from_node.id, 'target': to_node.id, 'type': link_type})
        visualize.add_link(link)

    return json({
        'id': id_,
        **visualize.to_dict()
    })


def _get_block(request: Request, block_hash, chain_id, get_transactions=False, get_decode_tx_method=True) -> Block:
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    etl: BlockchainETL = request.app.ctx.etl

    block_doc = mongo.get_block(chain_id, block_hash)
    use_mongo = True
    if not block_doc:
        block_doc = etl.get_block(chain_id, block_hash)
        use_mongo = False
        if not block_doc:
            NotFound(f'Block with hash {block_hash}')

    block = Block.from_dict(block_doc, chain_id=chain_id)

    if get_transactions:
        if use_mongo:
            transactions = mongo.get_transactions_by_block(chain_id=chain_id, block_number=block.number)
        else:
            transactions = etl.get_transactions_by_block(chain_id=chain_id, block_number=block.number)

        for tx in transactions:
            transaction = Transaction.from_dict(tx, chain_id=chain_id)
            block.transactions.append(transaction)

        tx_service = TransactionService(graph=db, mongo=mongo)
        tx_service.decode_tx(block.transactions, chain_id, decode_tx_method=get_decode_tx_method)

    return block
