from sanic import Blueprint, Request
from sanic import html
from sanic_ext import openapi

docs_bp = Blueprint('docs_blueprint', url_prefix='/apis')


@docs_bp.get('/')
@openapi.exclude()
async def docs(request: Request):
    config = request.app.config
    ui = 'swagger'

    version = getattr(config, f"OAS_UI_{ui}_VERSION".upper(), "")
    html_title = getattr(config, f"OAS_UI_{ui}_HTML_TITLE".upper())
    custom_css = getattr(config, f"OAS_UI_{ui}_CUSTOM_CSS".upper())

    with open('app/docs/swagger.html') as f:
        swagger = f.read()

    swagger = swagger.replace("__VERSION__", version)\
        .replace("__URL_PREFIX__", './docs')\
        .replace("__HTML_TITLE__", html_title)\
        .replace("__HTML_CUSTOM_CSS__", custom_css)
    return html(swagger)
