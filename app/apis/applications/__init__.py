from sanic import Blueprint

from app.apis.applications.cex_blueprint import bp as cex_bp
from app.apis.applications.dex_blueprint import bp as dex_bp

application_api = Blueprint.group(cex_bp, dex_bp, url_prefix='/')
