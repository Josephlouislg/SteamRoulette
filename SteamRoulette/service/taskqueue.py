import threading
from datetime import datetime
from enum import Enum
from functools import partial

import celery
import pytz
from celery import Celery
from celery.beat import Scheduler
from celery.loaders.base import BaseLoader
from celery.schedules import crontab
from kombu import Queue, Exchange

from SteamRoulette.libs.contextmanagers import nested
from SteamRoulette.service.db import session
from SteamRoulette.tasks import register_tasks

_local = threading.local()


class CeleryLoader(BaseLoader):

    def on_worker_init(self):
        self.import_default_modules()
        # adopt_celery_logging(self.app)

    def on_task_init(self, task_id, task):
        ctx_managers = [
            # appstats_ctx(task.name, self.app.appstats, None)
        ]
        _local.ctx = nested(*ctx_managers)
        _local.ctx.__enter__()

    def on_process_cleanup(self):
        if hasattr(_local, 'ctx'):
            _local.ctx.__exit__(None, None, None)
            del _local.ctx


def configure_schedule(app, config):
    local_timezone = pytz.timezone(config['timezone'])
    celery_config = config['celery']

    def local_timezone_nowfun():
        return datetime.now(local_timezone).replace(tzinfo=None)

    local_crontab = partial(crontab, nowfun=local_timezone_nowfun)

    CELERYBEAT_SCHEDULE = {
        'SteamRoulette.tasks.trade_bot.test': {
            'task': 'SteamRoulette.tasks.trade_bot.test',
            'schedule': crontab(minute='*/5'),
        },
    }
    app.conf.beat_schedule = CELERYBEAT_SCHEDULE


class DummyScheduler(Scheduler):

    def __init__(self, *args, **kwargs):
        self._store = {'entries': {}}
        super().__init__(*args, **kwargs)

    def setup_schedule(self):
        self.merge_inplace(self.app.conf.CELERYBEAT_SCHEDULE)
        self.install_default_entries(self.schedule)
        self.sync()

    @property
    def schedule(self):
        return self._store['entries']

    @schedule.setter
    def schedule(self, schedule):
        self._store['entries'] = schedule

    def sync(self):
        pass

    @property
    def info(self):
        return 'dummy scheduler'


def init_celery(config):
    app = Celery('task', loader='SteamRoulette.service.taskqueue.CeleryLoader')
    app.conf.update(config['celery'])
    init_queues(app)
    configure_schedule(app, config)

    # Remove scoped sqlalchemy session when task finished.
    @celery.signals.task_postrun.connect(weak=False)
    def shutdown_session(*args, **kw):
        session.remove()

    register_tasks(app)
    setup_task_routes(app)
    app.finalize()
    return app


def init_queues(app):
    app.conf.update(
        task_queues=Queues.get_queues(),
        task_default_queue=Queues.DEFAULT.value.name,
        task_default_exchange=Queues.DEFAULT.value.exchange,
        task_default_routing_key=Queues.DEFAULT.value.routing_key,
    )


class Queues(Enum):
    DEFAULT = Queue(name='celery', exchange=Exchange('celery'), routing_key='celery')
    HIGH = Queue(name='high', exchange=Exchange('high'), routing_key='high')

    @classmethod
    def is_queue_exist(cls, queue_name):
        return queue_name in {queue.value.name for queue in cls}

    @classmethod
    def get_queues(cls):
        return tuple(
            (queue.value for queue in cls)
        )


class TaskRouter:

    def __init__(self, app: Celery):
        self._app = app

    def route_for_task(self, task_name: str, *args, **kwargs):
        task = self._app.tasks[task_name]
        if hasattr(task, 'queue_name') and Queues.is_queue_exist(task.queue_name):
            return {'queue': task.queue_name}
        route_key = next(
            (key for key in self.ROUTES.keys() if task_name.startswith(key.split('*')[0])),
            None
        )
        if route_key:
            return self.ROUTES[route_key]['queue']

    ROUTES = {
        'SteamRoulette.tasks.trade_bot.*': {
            'queue': Queues.HIGH.value.name
        },

    }


def setup_task_routes(app):
    return
    app.conf.update(
        task_routes={
            'SteamRoulette.tasks.trade_bot.*': {
                'queue': Queues.HIGH.value.name,
                # 'routing_key': Queues.HIGH.value.routing_key,
                # 'exchange': Queues.HIGH.value.exchange,
            },
        }
    )
