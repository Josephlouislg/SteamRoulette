import logging

from http.cookies import SimpleCookie
from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Response


log = logging.getLogger(__name__)


def is_https(env):
    """Return a guess for whether 'wsgi.url_scheme' should be 'http' or 'https'
    """
    return ('https' == env.get('wsgi.url_scheme') or
            'https' == env.get('HTTP_X_FORWARDED_PROTO'))


class AuthMiddleware(object):

    def __init__(self, app, auth_service, *,
                 cookie_name='auth', max_age=3600 * 24 * 365,
                 domain=None, httponly=False,
                 path='/', secure=None, header_token=False):
        if domain == '.localhost':
            domain = None
        self._app = app
        self._auth_service = auth_service
        self._cookie_name = cookie_name
        self._max_age = max_age
        self._domain = domain
        self._httponly = httponly
        self._path = path
        self._secure = secure
        self._header_token = header_token

    def _get_session_key(self, environ):
        set_cookie = False
        session_key = None
        if environ.get('HTTP_COOKIE'):
            c = SimpleCookie()
            c.load(environ.get('HTTP_COOKIE'))
            if self._cookie_name in c:
                session_key = c.get(self._cookie_name).value
        if (
            # ios chat web view auth hack
            self._header_token
            and environ.get('HTTP_TOKEN')
            and environ.get('PATH_INFO', '').startswith('/cabinet/mobile/chat')
        ):
            set_cookie = True
            session_key = environ.get('HTTP_TOKEN')
        if not session_key and (not self._secure or is_https(environ)):
            set_cookie = True
            session_key = self._auth_service.gen_session_key()
        return set_cookie, session_key

    def __call__(self, environ, start_response):
        set_cookie, session_key = self._get_session_key(environ)

        with self._auth_service.using(session_key):
            if set_cookie:
                result = []

                def hook(status, headerslist, exc_info=None):
                    result.extend((status, headerslist, exc_info))

                app_iter = self._app(environ, hook)
                status, headerslist, exc_info = result
                if exc_info is None:
                    resp = Response(app_iter, status=status,
                                    headers=headerslist,
                                    direct_passthrough=True)
                    resp.set_cookie(self._cookie_name, session_key,
                                    max_age=self._max_age, path=self._path,
                                    domain=self._domain, secure=self._secure,
                                    httponly=self._httponly)
                    return resp(environ, start_response)
                else:
                    start_response(status, headerslist, exc_info)
                    return app_iter
            else:
                return self._app(environ, start_response)


class APIAuthMiddleware(object):
    def __init__(self, app, auth_service, debug=False):
        self._app = app
        self._auth_service = auth_service
        self._debug = debug

    def __call__(self, environ, start_response):
        try:
            authorization = environ['HTTP_AUTHORIZATION']
        except KeyError:
            session_key = self._auth_service.gen_session_key()
        else:
            if not authorization.startswith('token '):
                return BadRequest()(environ, start_response)
            session_key = authorization.split(' ', 2)[1]
            # There is a bug in older version of the iOS app
            # when authorization token would be '(null)'
            # which resulted in stolen sessions.
            # In this case we don't use that token
            # and generate a new one.
            if session_key == '(null)':
                log.info('(null) authorization token')
                session_key = self._auth_service.gen_session_key()

        with self._auth_service.using(session_key):
            return self._app(environ, start_response)
