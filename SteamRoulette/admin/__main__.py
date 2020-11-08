import logging
import sys

from werkzeug.middleware.proxy_fix import ProxyFix

from SteamRoulette.admin.app import create_admin_app
from SteamRoulette.containers import AppContainer
from SteamRoulette.application import serve
from SteamRoulette.config import make_parser, load_config, config_trafaret
from SteamRoulette.service.taskqueue import init_celery

args = make_parser(config_trafaret)

logging.basicConfig()
logging.root.setLevel(logging.INFO)


def main(options):
    config = load_config(
        options.config,
        options.secrets,
        options.config_defaults
    )
    container = AppContainer()
    container.config.from_dict(config)
    modules = [m for m in sys.modules.values() if 'SteamRoulette' in m.__name__ and hasattr(m, '__path__')]
    container.wire(packages=modules)
    container.init_resources()

    celery_app = init_celery(config)
    app = create_admin_app(config,)
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app


if __name__ == '__main__':
    serve(args.parse_args(), main)
