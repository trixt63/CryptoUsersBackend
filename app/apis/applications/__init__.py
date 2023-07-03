from sanic import Blueprint

from app.apis._olds.entities.blocks_blueprint import blocks_bp
from app.apis._olds.entities.contracts_blueprint import contracts_bp
from app.apis._olds.entities.projects_blueprint import projects_bp
from app.apis._olds.entities.relationships_blueprint import relationships_bp
from app.apis._olds.entities.tokens_blueprint import tokens_bp
from app.apis._olds.entities.transactions_blueprint import transactions_bp
from app.apis._olds.entities.wallets_blueprint import wallets_bp

entities_api = Blueprint.group(
    wallets_bp,
    tokens_bp,
    contracts_bp,
    projects_bp,
    transactions_bp,
    blocks_bp,
    relationships_bp,
    url_prefix='/')
