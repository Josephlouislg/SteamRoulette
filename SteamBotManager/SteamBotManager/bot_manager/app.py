import logging.handlers
import yaml
from aiohttp import web

from SteamBotManager.SteamBotManager.bot_manager.views.bots import bot_register
from SteamBotManager.SteamBotManager.signals import (
    init_metrics_server,
    init_session,
    destroy_session,
    create_db_engine,
    destroy_db_engine,
    init_captcha_service,
    destroy_captcha_service,
)

log = logging.getLogger(__name__)


async def healthcheck(request):
    return web.Response(status=200)


def deep_replace(target: dict, source: dict):
    for key in source:
        if key not in target:
            continue
        if isinstance(source[key], dict) and isinstance(target[key], dict):
            deep_replace(target[key], source[key])
        else:
            target[key] = source[key]


def get_config(config_path, secrets_path=None):
    with open(config_path, 'rt', encoding='UTF-8') as config_file:
        config = yaml.safe_load(config_file)
        if secrets_path:
            with open(secrets_path, 'rt', encoding='UTF-8') as secrets_file:
                secrets = yaml.safe_load(secrets_file)
                deep_replace(config, secrets)
        return config


async def create_app(args):
    config = get_config(args.config, args.secrets)
    middlewares = []
    logging.basicConfig(level=logging.DEBUG)
    app = web.Application(middlewares=middlewares)
    app['config'] = config
    app['args'] = args
    app.on_startup.extend((
        init_session,
        init_metrics_server,
        create_db_engine,
        init_captcha_service,
    ))

    app.on_cleanup.extend((
        destroy_session,
        destroy_db_engine,
        destroy_captcha_service,
    ))

    app.router.add_route(
        'GET', '/health', healthcheck
    )
    app.router.add_route(
        'GET', '/admin/api/bots/bot_register', bot_register
    )
    return app
