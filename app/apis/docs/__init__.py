from sanic import Blueprint

from app.apis.docs.docs_blueprint import docs_bp

docs_api = Blueprint.group(docs_bp, url_prefix='/')
