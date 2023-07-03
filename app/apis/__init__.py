from sanic import Blueprint

from app.apis.auth_blueprint import auth_bp
# from app.apis._olds.entities import entities_api
# from app.apis._olds.ranking import ranking_api
from app.apis.homepage import homepage_api
from app.apis.applications import application_api

api = Blueprint.group(
    # portfolio_api,
    # explorer_api,
    # ranking_api,
    homepage_api,
    application_api,
    # entities_api,
    auth_bp
)
