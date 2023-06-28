from typing import Union

from sanic import Blueprint, Request
from sanic import json
from sanic.exceptions import NotFound
from sanic_ext import openapi

from app.constants.search_constants import SearchConstants, RelationshipType
from app.databases.arangodb.klg_database import KLGDatabase
from app.databases.mongodb.blockchain_etl import BlockchainETL
from app.databases.mongodb.mongodb_klg import MongoDB
from app.databases.postgresdb.token_transfer import TokenTransferDB
from app.models.entity.transaction import Transaction
from app.models.explorer.link import Link
from app.models.explorer.visualization import Visualization
from app.services.transaction_services import TransactionService
from app.utils.format_utils import short_address
from app.utils.search_data_utils import get_explorer_link

transactions_bp = Blueprint('transactions_blueprint', url_prefix='/transactions')


@transactions_bp.get('/<id_>/introduction')
@openapi.tag("Transaction")
@openapi.summary("Get transaction introduction")
@openapi.parameter(name="id_", description="Transaction ID", location="path", required=True)
async def get_transaction_introduction(request: Request, id_):
    chain_id, tx_hash = id_.lower().split('_')

    # To check if tx hash exists
    _ = _get_transaction(
        request, tx_hash, chain_id,
        get_transfer=False, get_decode_tx_method=False
    )

    return json({
        "id": id_,
        "hash": tx_hash,
        "name": short_address(tx_hash, n_start=18, n_end=-len(tx_hash)),
        "explorerUrls": [get_explorer_link(chain_id, tx_hash, SearchConstants.transaction)],
        "chains": [chain_id]
    })


@transactions_bp.get('/<id_>/overview')
@openapi.tag("Transaction")
@openapi.summary("Get transaction information")
@openapi.parameter(name="id_", description="Transaction ID", location="path", required=True)
async def get_transaction(request: Request, id_):
    chain_id, tx_hash = id_.lower().split('_')

    transaction = _get_transaction(
        request, tx_hash, chain_id,
        get_transfer=False, get_decode_tx_method=True
    )

    data = transaction.to_dict()
    to_address_type = transaction.to_.type if transaction.to_ else 'wallet'
    data.update({
        "explorerUrl": get_explorer_link(chain_id, tx_hash, type_=SearchConstants.transaction),
        "fromAddressExplorerUrl": get_explorer_link(chain_id, transaction.from_address, type_=SearchConstants.wallet),
        "toAddressExplorerUrl": get_explorer_link(chain_id, transaction.to_address, type_=to_address_type)
    })

    return json(data)


@transactions_bp.get('/<id_>/transfers')
@openapi.tag("Transaction")
@openapi.summary("Get transaction's transfer")
@openapi.parameter(name="id_", description="Transaction ID", location="path", required=True)
async def get_transfers(request: Request, id_):
    chain_id, tx_hash = id_.lower().split('_')

    transaction = _get_transaction(
        request, tx_hash, chain_id,
        get_transfer=True, get_decode_tx_method=False
    )
    transfers = transaction.get_transfers_dict()

    return json({
        'id': id_,
        'numberOfTransfers': len(transfers),
        'transfers': transfers
    })


@transactions_bp.get('/<id_>/visualize')
@openapi.tag("Transaction")
@openapi.summary("Get transaction visualize information")
@openapi.parameter(name="id_", description="Transaction ID", location="path", required=True)
async def get_visualize(request: Request, id_):
    chain_id, tx_hash = id_.lower().split('_')

    transaction = _get_transaction(
        request, tx_hash, chain_id,
        get_transfer=True, get_decode_tx_method=False
    )

    visualize = Visualization()
    from_node = transaction.from_.to_node()
    visualize.add_node(from_node)

    to_node = transaction.to_.to_node()
    visualize.add_node(to_node)

    link_type = RelationshipType.transfer if to_node.type == SearchConstants.wallet else RelationshipType.call_contract
    link = Link.from_dict({'source': from_node.id, 'target': to_node.id, 'type': link_type})
    visualize.add_link(link)

    for transfer in transaction.transfers:
        transfer_from_node = transfer.from_.to_node()
        visualize.add_node(transfer_from_node)

        transfer_to_node = transfer.to_.to_node()
        visualize.add_node(transfer_to_node)

        transfer_link = Link.from_dict({'source': transfer_from_node.id, 'target': transfer_to_node.id, 'type': RelationshipType.transfer})
        visualize.add_link(transfer_link)

    return json({
        'id': id_,
        **visualize.to_dict()
    })


def _get_transaction(request: Request, tx_hash, chain_id, get_transfer=False, get_decode_tx_method=True) -> Transaction:
    db: Union[MongoDB, KLGDatabase] = request.app.ctx.db
    mongo: BlockchainETL = request.app.ctx.mongo
    etl: BlockchainETL = request.app.ctx.etl
    transfer_db: TokenTransferDB = request.app.ctx.transfer_db
    tx_service = TransactionService(graph=db, mongo=mongo)

    tx = mongo.get_transaction(chain_id, tx_hash)
    if not tx:
        tx = etl.get_transaction(chain_id, tx_hash)
        if not tx:
            NotFound(f'Transaction with hash {tx_hash}')

    transaction = Transaction.from_dict(tx, chain_id=chain_id)
    tx_service.decode_tx(transaction, chain_id, decode_tx_method=get_decode_tx_method)

    if get_transfer:
        transfers = transfer_db.get_event_transfer_by_transaction(chain_id=chain_id, tx_hash=transaction.hash)
        transaction.transfers = tx_service.transfers_info(chain_id, transfers)
        for transfer in transaction.transfers:
            transfer.update_tx_method(transaction)

    return transaction
