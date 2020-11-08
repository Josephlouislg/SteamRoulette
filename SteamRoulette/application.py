import logging
import os
from io import BytesIO
from time import time
from urllib.parse import urljoin

from flask import Flask, request, Response, url_for, Request as _Request, session as flask_session
from flask.cli import DispatchingApp, ScriptInfo
from prometheus_client import start_http_server
from werkzeug import run_simple
from werkzeug.exceptions import BadRequest
from werkzeug.routing import Rule
from werkzeug.serving import BaseWSGIServer
from werkzeug.utils import cached_property

from SteamRoulette.libs.encoders import CustomJSONEncoder
from SteamRoulette.prometheus_setup import app_exceptions, page_generation_time
from SteamRoulette.service.db import db


log = logging.getLogger(__name__)


def create_raw_app(config, app_name=__name__):
    app = App(app_name)
    db.init_app(app)
    return app


def setup_common_jinja_env(env, debug=False):
    """Setups common stuff for flask's and celery's jinja2 envs"""
    env.autoescape = True
    # env.add_extension('jinja2.ext.do')
    # env.add_extension('jinja2.ext.i18n')


def serve_production(options, create_app):
    app = create_app(options=options)
    wsgi = BaseWSGIServer(
        host=options.host,
        port=options.port,
        fd=options.fd,
        app=app
    )

    try:
        start_http_server(9100)
    except Exception as e:
        log.error(f'Prometheus client error, {e}')

    try:
        log.info("Server started at: %s:%s (fd: %s)",
                 options.host, options.port, options.fd)
        wsgi.serve_forever()
    except KeyboardInterrupt:
        print("Exiting...")


def serve_development(options, create_app):

    def adapted_create_app(info):
        # https://github.com/pallets/flask/issues/1246
        os.environ['PYTHONPATH'] = os.getcwd()
        try:
            return create_app(options=options)
        except Exception:
            import traceback
            traceback.print_exc()
            raise

    info = ScriptInfo(create_app=adapted_create_app)
    app = DispatchingApp(info.load_app, use_eager_loading=True)
    run_simple(options.host, options.port, app,
               use_reloader=True,
               use_debugger=True,
               passthrough_errors=True)


def serve(options, create_app):
    if options.debugger:
        serve_development(options, create_app)
    else:
        serve_production(options, create_app)


class Request(_Request):

    session = flask_session

    def _get_file_stream(self, *args, **kw):
        """Called to get a stream for the file upload."""
        return BytesIO()

    def replace_current_url(self, **kw):
        next_view_args = {**self.view_args, **kw}
        return url_for(self.endpoint, **next_view_args, **self.args)

    def get_from_json(self, key, default=None, type=None):
        d = self.get_json()
        if not isinstance(d, dict):
            raise BadRequest()
        try:
            rv = d[key]
            if type is not None:
                rv = type(rv)
        except (KeyError, ValueError, TypeError):
            rv = default
        return rv

    def getlist_from_json(self, key, type=None):
        try:
            v = self.get_json()[key]
        except (TypeError, ValueError, KeyError):
            return []
        if not isinstance(v, list):
            return []
        if type is None:
            return v
        out = []
        for item in v:
            try:
                out.append(type(item))
            except (ValueError, TypeError):
                pass
        return out

    @cached_property
    def response(self):
        return Response()

    @cached_property
    def is_robot(self) -> bool:
        agent = self.user_agent.string.lower()
        return (
            'googlebot' in agent
            or 'yandexbot' in agent
            or 'bingbot' in agent
        )

    @cached_property
    def is_desktop(self) -> bool:
        return self.user_agent.platform not in ('android', 'ios', 'ipad', 'iphone')

    @cached_property
    def is_moz_prefetch(self) -> bool:
        return self.headers.get('X-Moz', '') == 'prefetch'


class App(Flask):
    url_rule_class = Rule
    json_encoder = CustomJSONEncoder
    request_class = Request
    asset_hashes = None
    container = None
    ctx_extractors = []

    def __init__(self, *args, asset_hashes=None, **kw):
        super().__init__(*args, static_folder=None, **kw)
        self.asset_hashes = asset_hashes or {}

    @page_generation_time.time()
    def full_dispatch_request(self):
        """
        Log request execution time.

        Note that this DOES NOT include middlewares.
        """
        start = time()
        try:
            return super().full_dispatch_request()
        finally:
            gen_time = int((time() - start) * 1000)
            extra = {
                'flask_duration': gen_time,
                'flask_endpoint': request.endpoint,
            }
            for extractor in self.ctx_extractors:
                extra.update(extractor())
            log.info('request handled', extra=extra)

    def config_from_dict(self, config):
        """Configures application from dict."""
        for key, val in config.items():
            self.config[key] = val   # self.config is not a real dict

    def handle_exception(self, e):
        app_exceptions.inc()
        return super().handle_exception(e)

    def handle_url_build_error(self, error, endpoint, values):
        if endpoint != 'static':
            return super().handle_url_build_error(error, endpoint, values)
        filename = values['filename']
        base = self.config['ASSETS_BASE']  # flask.assets_base
        url = urljoin(base, filename)
        h = self.asset_hashes.get(filename)
        if h:
            url = f'{url}?r={h}'
        return url

    @cached_property
    def logger(self):
        """
        Flask creates its own log handlers, which
        whe don't want.
        """
        return logging.getLogger(__name__)
