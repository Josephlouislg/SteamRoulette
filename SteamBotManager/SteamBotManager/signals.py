import logging.handlers

from aiohttp import web, ClientSession, ClientTimeout, DummyCookieJar
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
