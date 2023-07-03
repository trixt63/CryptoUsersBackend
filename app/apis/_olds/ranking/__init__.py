from sanic import Blueprint

from app.apis._olds.ranking.rankings_blueprint import rankings_bp

ranking_api = Blueprint.group(rankings_bp, url_prefix='/ranking')
