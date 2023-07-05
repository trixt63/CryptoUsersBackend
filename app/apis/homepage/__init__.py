from sanic import Blueprint

# from app.apis.homepage.home_blueprint import home_bp
from app.apis.homepage.homepage_blueprint import bp as homepage_bp

homepage_api = Blueprint.group(homepage_bp, url_prefix='/homepage')
