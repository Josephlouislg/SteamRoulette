import logging
import threading
import time
from typing import List

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_success, task_failure, task_retry
from kombu import Queue
from prometheus_client import Counter, Gauge


log = logging.getLogger(__name__)


celery_processing = Gauge(
    'celery_processing', "Number of celery tasks in progress", ['queue']
)

celery_queue = Gauge(
    'celery_queue', "Count of celery tasks in queue", ['queue']
)

celery_consumers_online = Gauge(
    'celery_consumers_online', "Count of celery consumers in queue", ['queue']
)


celery_success = Counter(
    'celery_success_total', "Count of success celery tasks", ['queue'],
)


celery_failure = Counter(
    'celery_failure_total', "Count of failed celery tasks", ['queue'],
)


celery_retry = Counter(
    'celery_retry_total', "Count of retried celery tasks", ['queue'],
)


class _QueuesMetricsCollector(threading.Thread):
    """
        use only as daemon, and only with rabbit as a broker
    """
    DELAY = 10

    def __init__(self, queues: List[Queue], celery_app: Celery):
        super().__init__()
        self._queues = queues
        self._init_metrics()
        self._celery_app = celery_app

    def run(self):
        while True:
            self._collect_tasks_in_queues()
            time.sleep(self.DELAY)

    def _init_metrics(self):
        # for proper prometheus Gauge metrics expose
        for queue in self._queues:
            celery_queue.labels(queue=queue.name).set(0)
            celery_consumers_online.labels(queue=queue.name).set(0)

    def _collect_tasks_in_queues(self):
        try:
            with self._celery_app.connection_or_acquire() as conn:
                for queue in self._queues:
                    rabbit_queue = self._get_queue(conn, queue.name)
                    celery_queue.labels(queue=rabbit_queue.queue).set(rabbit_queue.message_count)
                    celery_consumers_online.labels(queue=rabbit_queue.queue).set(rabbit_queue.consumer_count)
        except Exception as err:
            log.warning(
                '[CELERY_METRICS] can not update queues size, err: %r',
                err
            )

    @staticmethod
    def _get_queue(conn, queue: str):
        return conn.default_channel.queue_declare(
            queue=queue,
            passive=True,
        )


def start_queues_size_collector(queues: List[Queue], celery_app: Celery):
    collector = _QueuesMetricsCollector(queues, celery_app)
    collector.daemon = True
    collector.start()


def attach_prometheus_metrics_to_celery(worker_signal=False):
    task_prerun.connect(_on_task_prerun)
    task_postrun.connect(_on_task_postrun)
    task_success.connect(_on_success)
    task_failure.connect(_on_failure)
    task_retry.connect(_on_retry)


def _on_task_prerun(*args, sender, **kw):
    routing_key = sender.request.delivery_info['routing_key']
    celery_processing.labels(routing_key).inc()


def _on_task_postrun(*args, sender, **kw):
    routing_key = sender.request.delivery_info['routing_key']
    celery_processing.labels(routing_key).dec()


def _on_success(*args, sender, **kw):
    routing_key = sender.request.delivery_info['routing_key']
    celery_success.labels(routing_key).inc()


def _on_failure(*args, sender, **kw):
    routing_key = sender.request.delivery_info['routing_key']
    celery_failure.labels(routing_key).inc()


def _on_retry(*args, sender, **kw):
    routing_key = sender.request.delivery_info['routing_key']
    celery_retry.labels(routing_key).inc()
