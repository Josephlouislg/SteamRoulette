import argparse
import logging
import pathlib

from celery.concurrency import ALIASES as CELERY_POOL_ALIASES

from SteamRoulette.config import TrafaretValueAction, config_trafaret

log = logging.getLogger(__name__)


def make_parser(root_dir=None, default_config='config.yaml'):
    if not root_dir:
        root_dir = pathlib.Path(__file__)
        root_dir = root_dir.parent.parent.parent

    ap = argparse.ArgumentParser(fromfile_prefix_chars='@')
    ap.add_argument('-c', '--config', type=pathlib.Path, metavar='PATH',
                    default=root_dir / 'config' / default_config,
                    help="Path to config file (default: `%(default)s`)")
    ap.add_argument('-s', '--secrets', type=pathlib.Path, metavar='PATH',
                    default=None, help="Path to file with secrets")
    ap.add_argument('-D', dest="config_defaults", metavar="VARNAME=VALUE",
                    action=TrafaretValueAction, trafaret=config_trafaret,
                    help="Config overrides")

    ap.add_argument('--queues',
                    default='celery',
                    help="Celery queues to process (default: `%(default)s`)")
    ap.add_argument('--pool',
                    default='solo',
                    choices=CELERY_POOL_ALIASES,
                    help="Celery pool class (default: `%(default)s`)")
    ap.add_argument('--concurrency', default=None, type=int,
                    help="Concurrency level")
    ap.add_argument('--purge', default=False, action='store_true',
                    help="???")
    ap.add_argument('--schedule-last-run', type=pathlib.Path, metavar='PATH',
                    default=root_dir / 'celerybeat-schedule',
                    help="Path to celerybeat schedule database"
                         " (default: `%(default)s`)")
    ap.add_argument('--beat', default=False, action='store_true',
                    help="Enable Celery Beat (default: `%(default)s`)")
    return ap
