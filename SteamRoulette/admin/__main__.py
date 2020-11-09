import logging
import sys
from functools import partial

from dependency_injector.wiring import Provide
from werkzeug.middleware.proxy_fix import ProxyFix

from SteamRoulette.admin.app import create_admin_app
from SteamRoulette.admin.containers import AdminContainer
from SteamRoulette.application import serve, AdminRequest
from SteamRoulette.config import make_parser, load_config, config_trafaret
from SteamRoulette.containers import AppContainer
from SteamRoulette.libs.auth.middleware import AuthMiddleware
from SteamRoulette.libs.auth.service import AuthService
from SteamRoulette.service.taskqueue import init_celery

args = make_parser(config_trafaret)

logging.basicConfig()
logging.root.setLevel(logging.INFO)


def _init_admin_auth(config, app, auth: AuthService):
    app = AuthMiddleware(
        app.wsgi_app, auth,
        cookie_name=config['admin_auth']['cookie_name'],
        domain=config['flask']['SERVER_NAME'],
        httponly=config['admin_auth']['cookie_httponly'],
        secure=config['admin_auth']['cookie_secure'],
    )
    return app


def main(options):
    config = load_config(
        options.config,
        options.secrets,
        options.config_defaults
    )
    app_container = AppContainer()
    app_container.config.from_dict(config)
    modules = [m for m in sys.modules.values() if 'SteamRoulette' in m.__name__ and hasattr(m, '__path__')]
    app_container.wire(packages=modules)
    app_container.init_resources()

    container = AdminContainer()
    container.config.from_dict(config)
    container.wire(packages=modules)
    container.init_resources()

    init_celery(config)
    app = create_admin_app(config,)
    app.request_class = partial(AdminRequest, admin_provider=app_container.admin_provider())
    app.app_container = app_container
    app.admin_container = container
    app.wsgi_app = _init_admin_auth(config, app, app_container.admin_auth())
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app


if __name__ == '__main__':
    serve(args.parse_args(), main)
