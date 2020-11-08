import argparse
import glob
import json
import logging
import os
import pathlib
from datetime import timedelta

from celery.schedules import crontab as celery_crontab
import trafaret as t
import yaml
from trafaret.utils import unfold

logger = logging.getLogger(__name__)

# Yet can't get rid of this.
# There are too many `get_config` calls which needs to be refactored.
# So keeping this as private var.
_CONFIG = {}
_NO_DEFAULT_VALUE_CONFIG = ...


def _deep_replace(target: dict, source: dict):
    for key in source:
        if key not in target:
            continue
        if isinstance(source[key], dict) and isinstance(target[key], dict):
            _deep_replace(target[key], source[key])
        else:
            target[key] = source[key]


def init_config(config):
    """Initialize config with new values."""
    _CONFIG.clear()
    _CONFIG.update(config)
    return config


def _get_config(config_path, secrets_path=None):
    with open(config_path, 'rt', encoding='UTF-8') as config_file:
        config = yaml.safe_load(config_file)
        if secrets_path:
            with open(secrets_path, 'rt', encoding='UTF-8') as secrets_file:
                secrets = yaml.safe_load(secrets_file)
                _deep_replace(config, secrets)
        return config


def load_config(config_path, secrets_path=None, overrides=None):
    """Loads and parses config file.

    config_path: path to Yaml file to read;
    secrets_path: path to Yaml file with secrets;
    config_trafaret: trafaret to apply as validation;
    overrides: is a dict with dot-separated keys (see `get_config`)
               with replacements for original values in config.
    """
    if isinstance(config_path, pathlib.Path):
        config_path = str(config_path.resolve())

    with open(config_path, 'rt', encoding='UTF-8') as f:
        data = yaml.load(f)

    if secrets_path:
        if isinstance(secrets_path, pathlib.Path):
            secrets_path = str(secrets_path.resolve())
        with open(secrets_path, 'rt') as f:
            _deep_replace(data, yaml.load(f))

    if overrides:
        for key, value in overrides.items():
            *head, key = key.split('.')
            tmp = data
            for k in head:
                tmp = tmp.setdefault(k, {})
            tmp[key] = value

    try:
        config = config_trafaret(data)
    except t.DataError as err:
        _report_errors(err)
        raise

    return init_config(config)


def _report_errors(err):
    print("Error(s) in config:")
    errors = unfold(err.as_dict(), delimeter='.')
    for i, (k, e) in enumerate(sorted(errors.items())):
        print("{:>4}: {!r}: {!r}".format(i, k, e))
    raise SystemExit(1)


def _existing_file(x):
    path = pathlib.Path(x)
    if not path.exists():
        raise argparse.ArgumentTypeError('file {} does not exist'.format(x))
    return path


def make_parser(config_trafaret, default_config='config.yaml', root_dir=None):
    if not root_dir:
        root_dir = pathlib.Path(__file__)
        root_dir = root_dir.parent.parent

    ap = argparse.ArgumentParser(fromfile_prefix_chars='@')
    ap.add_argument('-c', '--config', type=_existing_file, metavar='PATH',
                    default=root_dir / 'config' / default_config,
                    help="Path to config file (default: `%(default)s`)")
    ap.add_argument('-s', '--secrets', type=pathlib.Path, metavar='PATH',
                    default=None, help="Path to file with secrets")
    ap.add_argument('-b', '--host', default='localhost', metavar='HOSTNAME',
                    help="Bind to host (default: `%(default)s`)")
    ap.add_argument('-p', '--port', default=5000, type=int, metavar='PORT',
                    help="Bind to port (default: `%(default)s`)")
    ap.add_argument('-f', '--listen-fd', type=int,
                    dest='fd', default=None,
                    help="Use socket from file descriptor"
                         " (default: `%(default)s`)")

    ap.add_argument('-D', dest="config_defaults", metavar="VARNAME=VALUE",
                    action=TrafaretValueAction, trafaret=config_trafaret,
                    help="Config overrides")
    ap.add_argument('--debugger', action='store_true',
                    help="Run with werkzeug debugger and autoreloading")
    ap.add_argument('-t', '--test-config', action='store_true', default=False,
                    help="Only test config and print errors if any.")
    ap.add_argument('-l', '--log', default='INFO',
                    help="Logger level")
    return ap


def unfold_keys(trafaret, *, delimiter='.'):
    def _gen():
        items = [((key.name,), key.trafaret) for key in trafaret.trafaret.keys]
        while items:
            prefix, traf = items.pop(0)
            if isinstance(traf, t.Dict):
                items[:0] = [(prefix + (k.name,), k.trafaret)
                             for k in traf.keys]
            else:
                yield '.'.join(prefix), traf
    return dict(_gen())


class MyDict(t.Dict):
    """Adds two extra methods to trafaret.Dict.

    >>> d = MyDict({
    ...         t.Key('foo'): t.Int,
    ...         t.Key('bar') >> 'to_name': t.Int,
    ...         }).uppercase()
    >>> d({'foo': 1, 'bar': 2})
    {'FOO': 1, 'to_name': 2}
    """

    def uppercase(self):
        """Convert all keys (which have no name overrides) to uppercase."""
        for key in self.keys:
            if key.to_name is None:
                key.to_name = key.name.upper()
        return self

    def prefix(self, prefix):
        """Prefix all keys."""
        for key in self.keys:
            key.to_name = '{}{}'.format(prefix, key.get_name())
        return self


class TrafaretValueAction(argparse.Action):
    """ArgumentParser action.

    Accept one extra argument `trafaret`.
    Trafaret is used to validate specified values
    so that later could be used in load_config.

    Parses values in form VARNAME=VALUE.
    Example:

    >>> config_traf = t.Dict({
    ...     t.Key('host'): t.String,
    ...     t.Key('port'): t.Int[0:65535],
    ...     t.Key('redis'): t.Dict({
    ...         t.Key('host'): t.String,
    ...         t.Key('port'): t.String,
    ...         }),
    ...     })
    >>> ap = argparse.ArgumentParser()
    >>> ap.add_argument('-D', action=TrafaretValueAction,
    ...                 dest='overrides',
    ...                 trafaret=config_traf)
    >>> options = ap.parse_args(['-D', 'port=8000',
    ...                          '-D', 'redis.host=locahlost'])
    >>> options.overrides
    {'port': 8000, 'redis.port': 'localhost'}
    """

    def __init__(self, *args, trafaret, **kw):
        super().__init__(*args, **kw)
        self._folded = unfold_keys(trafaret)

    def __call__(self, parser, namespace, values, option_strings):
        try:
            field, value = values.split('=')
        except ValueError:
            raise argparse.ArgumentError(
                self, "Option must be in form of VARNAME=VALUE")
        if field in self._folded:
            dest = getattr(namespace, self.dest, None)
            if dest is None:
                dest = {}
                setattr(namespace, self.dest, dest)
            traf = self._folded[field]
            if isinstance(traf, (t.List, t.Tuple)):
                dest.setdefault(field, [])
            if isinstance(traf, t.Bool):
                value = value.lower() in {'1', 'true', 'yes', 'on'}
            if field in dest:
                if isinstance(dest[field], list):
                    value = dest[field] + [value]
                else:
                    value = [dest[field], value]
            dest.update({field: value})
        else:
            # Try not to show whole big list of options
            match = list(self._folded)
            for i in range(len(field)):
                tmp = [k for k in match if k.startswith(field[:i+1])]
                if tmp:
                    match = tmp
                    continue
                break
            raise argparse.ArgumentError(
                self,
                ("{!r} is not a valid option,\n"
                 "valid config variables are:\n\t {!s}\n"
                 .format(field, '\n\t '.join(sorted(match)))))


def get_config():
    return _CONFIG


def _to_celery_schedule(d):
    d = d.copy()
    never = d.pop('never')
    if never:
        return timedelta(days=365 * 10)
    return celery_crontab(**d)


postgres_trafaret = t.Dict({
    t.Key('dsn'): t.String,
    t.Key('dsn_slave', default=None): t.String | t.Null,
    t.Key('echo', default=False): t.Bool,
    })


redis_sentinel_trafaret = t.Dict({
    t.Key('sentinels'): t.List(t.Tuple(t.String, t.Int)),
    t.Key('service_name'): t.String,
    t.Key('socket_timeout', default=5): t.Float,
})


redis_trafaret = t.Dict({
    t.Key('host', default='localhost'): t.String,
    t.Key('port', default=6379): t.Int,
    t.Key('db', default=0): t.Int[0:],
    t.Key('sentinel', optional=True): redis_sentinel_trafaret,
    })


cache_trafaret = t.Dict({
    'redis': redis_trafaret,
})


flask_trafaret = MyDict({
    t.Key('secret_key'): t.String,
    t.Key('server_name'): t.String,
    t.Key('wtf_csrf_enabled', default=True): t.Bool,

    # See https://github.com/lepture/flask-wtf/issues/285
    # to learn why `False`.
    t.Key('wtf_csrf_ssl_strict', default=False): t.Bool,

    t.Key('max_content_length', default=52428800): t.Int,   # 50MB
    t.Key('preferred_url_scheme', default='http'): t.String,
    t.Key('debug_tb_enabled', default=False): t.Bool,
    t.Key('debug_tb_intercept_redirects', default=False): t.Bool,
    t.Key('debug_tb_profiler_enabled', default=False): t.Bool,
}).uppercase()


CeleryCronTraf = t.Dict({
    t.Key('never', default=False): t.Bool,

    t.Key('minute', default='*'): t.String | t.Int,
    t.Key('hour', default='*'): t.String | t.Int,
    t.Key('day_of_week', default='*'): t.String | t.Int,
    t.Key('day_of_month', default='*'): t.String | t.Int,
    t.Key('month_of_year', default='*'): t.String | t.Int,
}) >> _to_celery_schedule


celery_trafaret = MyDict({
    t.Key('broker_url'): t.String,
    t.Key('task_always_eager', default=False): t.Bool,
    t.Key('enable_ping_sitemap', default=True): t.Bool,
    # drop unused messages from celeryev queues
    t.Key('event_queue_ttl', default=5): t.Int,
    t.Key('event_queue_expires', default=60): t.Int,
})


auth_trafaret = t.Dict({
    t.Key('redis_client_session_prefix'): t.String,
    t.Key('redis_user_session_prefix'): t.String,
    t.Key('cookie_name'): t.String,
    t.Key('cookie_httponly'): t.Bool,
    t.Key('cookie_secure'): t.Bool,
})


def propagate_duplicates(conf):
    """Propagates config values into some inner dicts."""
    # XXX: get rid of this method eventually
    debug = conf['debug']
    conf['flask']['DEBUG'] = debug
    conf['celery']['timezone'] = conf['timezone']
    return conf


config_trafaret = t.Dict({
    t.Key('debug', default=False): t.Bool,  # propagate into flask.DEBUG
    t.Key('production', default=False): t.Bool,
    t.Key('local', default=False): t.Bool,
    t.Key('enable_geoip', default=True): t.Bool,
    t.Key('country', default='UA'): t.String,
    t.Key('timezone', default='Europe/Kiev'): t.String,
    t.Key('postgres'): postgres_trafaret,
    t.Key('redis'): redis_trafaret,
    t.Key('cache'): cache_trafaret,
    t.Key('flask'): flask_trafaret,
    t.Key('celery'): celery_trafaret,
    t.Key('user_auth'): auth_trafaret,
}) >> propagate_duplicates
