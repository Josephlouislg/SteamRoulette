from celery import current_app
from dependency_injector.wiring import Provide
from redis import Redis

from SteamRoulette.containers import AppContainer
from SteamRoulette.service.taskqueue import Queues
from SteamRoulette.tasks.containers import CeleryContainer


@current_app.task(bind=False, queue=Queues.HIGH.value.name)
def test(self=False):
    test_(self)


def test_(self, redis1: Redis = Provide[AppContainer.redis],
    redis2: Redis = Provide[CeleryContainer.redis]):
    assert redis1 != redis2
