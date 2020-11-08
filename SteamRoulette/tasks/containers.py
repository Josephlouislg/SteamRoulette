from dependency_injector import containers, providers

from SteamRoulette.service.redis import init_redis


class CeleryContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    redis = providers.Resource(
        init_redis,
        config=config.redis
    )
