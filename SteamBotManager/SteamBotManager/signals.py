import logging.handlers
from urllib.parse import urlparse

from aiohttp import web, ClientSession, ClientTimeout, DummyCookieJar
from aiopg import sa
from prometheus_async.aio.web import start_http_server


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


def destroy_db_engine(app: web.Application) -> None:
    app['pg_engine'].close()
