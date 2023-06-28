from sanic import Sanic

from app.misc.log import log


def register_extensions(sanic_app: Sanic):
    sanic_app.config.CORS_ORIGINS = "*"


def register_views(sanic_app: Sanic):
    from app.views import route

    route(sanic_app)


def register_hooks(sanic_app: Sanic):
    # from app.hooks.error import broad_exception_handler, sanic_exception_handler
    from app.hooks.request_context import after_request

    sanic_app.register_middleware(after_request, 'response')
    # sanic_app.error_handler.add(SanicException, sanic_app)
    # sanic_app.error_handler.add(Exception, broad_exception_handler)


def create_app(*config_cls) -> Sanic:
    log(message='Sanic application initialized with {}'.format(', '.join([config.__name__ for config in config_cls])),
        keyword='INFO')

    sanic_app = Sanic(__name__)

    for config in config_cls:
        sanic_app.config.update_config(config)

    register_extensions(sanic_app)
    # register_views(sanic_app)
    register_hooks(sanic_app)

    return sanic_app
