from dependency_injector import containers, providers

from SteamRoulette.service.celery_task_manager import CeleryTaskManager
from SteamRoulette.service.db import init_db
from SteamRoulette.service.redis import init_redis


class AppContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    redis = providers.Resource(
        init_redis,
        config=config.redis
    )
    db_engines = providers.Resource(
        init_db,
        config=config.postgres,
        debug=config.debug
    )
    celery_task_manager = providers.Resource(
        CeleryTaskManager,
        redis=redis
    )
