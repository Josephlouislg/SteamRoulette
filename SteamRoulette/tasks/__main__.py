import argparse
import logging
import pathlib
import random
import socket
import sys
from time import time

from celery.concurrency import ALIASES as CELERY_POOL_ALIASES
from celery.signals import task_prerun, task_postrun
from dependency_injector.wiring import Provide
from prometheus_client import start_http_server

from SteamRoulette.admin.app import create_admin_app
from SteamRoulette.application import create_raw_app
from SteamRoulette.config import TrafaretValueAction, config_trafaret, load_config
from SteamRoulette.containers import AppContainer
from SteamRoulette.service.celery_task_manager import CeleryTaskManager
from SteamRoulette.service.taskqueue import Queues, init_celery, DummyScheduler
from SteamRoulette.tasks.containers import CeleryContainer
from SteamRoulette.tasks.prometheus_setup import attach_prometheus_metrics_to_celery, start_queues_size_collector

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


def log_execution_time():
    times = {}

    @task_prerun.connect(weak=False)
    def task_prerun_handler(signal, sender, task_id, task, *args, **kwargs):
        times[task_id] = time()

    @task_postrun.connect(weak=False)
    def task_postrun_handler(signal, sender, task_id, task, *args, **kwargs):
        start = times.pop(task_id, None)
        if start is not None:
            # Task name is logged implicitly.
            log.info('celery_postrun',
                     extra=dict(celery_duration=int((time() - start) * 1000)))


def _drop_task(signal, sender, task_id, task, celery_task_manage: CeleryTaskManager = Provide[AppContainer.celery_task_manager], *args, **kwargs):
    if celery_task_manage.need_drop_task(task_name=task.name):
        raise Exception(f"TASK: {task.name} in stop list")


def set_celery_task_manage():
    _drop_task_ = None

    @task_prerun.connect(weak=False)
    def maybe_drop_task(signal, sender, task_id, task, *args, **kwargs):
        nonlocal _drop_task_
        if _drop_task_ is None:
            from SteamRoulette.tasks.__main__ import _drop_task
            _drop_task_ = _drop_task

        _drop_task_(signal, sender, task_id, task, *args, **kwargs)


def main(args=None, *, run=True):
    ap = make_parser()
    options, _ = ap.parse_known_args()

    log_execution_time()

    log.debug('Using config: %s', options.config.resolve())
    config = load_config(
        options.config,
        options.secrets,
        options.config_defaults
    )

    try:
        start_http_server(9100)
    except Exception as e:
        log.error(f'Prometheus client celery error, {e}')

    attach_prometheus_metrics_to_celery()


    # XXX: celery depends on flask
    # app = create_raw_app(config)
    app = create_admin_app(config)
    hostname = '{type}{id}@{host}'.format(
        type=(options.beat and 'beat' or 'worker'),
        id=random.randint(1, 1000),
        host=socket.gethostname())
    celery_app = init_celery(config)

    container = AppContainer()
    celery_container = CeleryContainer()
    container.config.from_dict(config)
    celery_container.config.from_dict(config)
    modules = [m for m in sys.modules.values() if 'SteamRoulette' in m.__name__ and hasattr(m, '__path__')]
    container.wire(packages=modules)
    celery_container.wire(packages=modules)
    container.init_resources()
    celery_container.init_resources()

    set_celery_task_manage()

    if options.beat:
        beat = celery_app.Beat(
            scheduler_cls=DummyScheduler,
        )
        start_queues_size_collector(queues=Queues.get_queues(), celery_app=celery_app)
        beat.run()
    else:
        worker = celery_app.Worker(
            queues=options.queues,
            pool_cls=options.pool,
            concurrency=options.concurrency,
            purge=options.purge,
            optimization='fair',
            hostname=hostname,
        )
        with app.app_context():
            worker.start()


if __name__ == '__main__':
    main()
