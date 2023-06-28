from sanic import Blueprint

from app.apis.auth_blueprint import auth_bp
from app.apis.entities import entities_api
from app.apis.explorer import explorer_api
from app.apis.homepage import homepage_api
from app.apis.portfolio import portfolio_api
from app.apis.ranking import ranking_api

api = Blueprint.group(
    portfolio_api,
    explorer_api,
    ranking_api,
    homepage_api,
    entities_api,
    auth_bp
)
