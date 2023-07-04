from sanic import Blueprint

from app.apis.applications.cex_blueprint import bp as cex_bp
from app.apis.applications.dex_blueprint import bp as dex_bp
from app.apis.applications.dex_pair_blueprint import bp as pair_bp
from app.apis.applications.lending_blueprint import bp as lending_bp

application_api = Blueprint.group(cex_bp, dex_bp, pair_bp, lending_bp, url_prefix='/')
