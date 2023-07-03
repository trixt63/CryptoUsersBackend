from sanic import Blueprint

from app.apis._olds.portfolio.alerts_blueprint import alerts_bp
from app.apis._olds.portfolio.assets_blueprint import assets_bp
from app.apis._olds.portfolio.dapps_blueprint import dapps_bp

portfolio_api = Blueprint.group(assets_bp, dapps_bp, alerts_bp, url_prefix='/portfolio')
