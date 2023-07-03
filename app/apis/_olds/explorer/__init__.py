from sanic import Blueprint

from app.apis.explorer.search_blueprint import search_bp

explorer_api = Blueprint.group(search_bp, url_prefix='/explorer')
