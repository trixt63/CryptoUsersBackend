from sanic import Blueprint

from app.apis.user.all_users_blueprint import bp as user_overview_bp

user_api = Blueprint.group(user_overview_bp, url_prefix='/user')
