from sanic import Blueprint

from app.apis.homepage.home_blueprint import home_bp

homepage_api = Blueprint.group(home_bp, url_prefix='/homepage')
