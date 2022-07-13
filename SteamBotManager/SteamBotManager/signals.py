import logging.handlers
from asyncio import get_running_loop
from urllib.parse import urlparse

from aiohttp import web, ClientSession, ClientTimeout, DummyCookieJar, TCPConnector
from aiopg import sa
from prometheus_async.aio.web import start_http_server

from SteamBotManager.SteamBotManager.services.captcha_resolver import CaptchaService

log = logging.getLogger(__name__)


async def init_metrics_server(app: web.Application) -> None:
    app_args = app['args']
    await start_http_server(port=app_args.metrics_port)
    log.info('Metrics web server started.')


async def init_session(app: web.Application) -> None:
    app['session'] = ClientSession(
        timeout=ClientTimeout(5),
        cookie_jar=DummyCookieJar(),
    )


async def destroy_session(app: web.Application) -> None:
    session: ClientSession = app['session']
    if not session.closed:
        await session.close()


async def create_db_engine(app: web.Application) -> None:
    config: dict = app['config']
    result = urlparse(config['postgres']['dsn'])
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    engine = await sa.create_engine(
        database=database,
        user=username,
        password=password,
        host=hostname,
        port=port,
    )
    app['pg_engine'] = engine


async def destroy_db_engine(app: web.Application) -> None:
    app['pg_engine'].close()


async def init_captcha_service(app: web.Application) -> None:
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    captcha_session = ClientSession(
        timeout=ClientTimeout(5),
        cookie_jar=DummyCookieJar(),
        headers=headers,
        connector=TCPConnector(loop=get_running_loop(), limit=10)
    )
    app['captcha_service'] = CaptchaService(
        app['config']['captcha']['api_key'],
        client_session=captcha_session
    )


async def destroy_captcha_service(app: web.Application) -> None:
    await app['captcha_service'].close()
