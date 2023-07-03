from sanic import Blueprint

from app.apis.applications.projects_blueprint import projects_bp

application_api = Blueprint.group(projects_bp, url_prefix='/')
