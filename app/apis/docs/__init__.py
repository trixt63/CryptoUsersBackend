from sanic import Blueprint

from app.apis._olds.docs.docs_blueprint import docs_bp

docs_api = Blueprint.group(docs_bp, url_prefix='/')
