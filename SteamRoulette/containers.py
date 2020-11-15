from dependency_injector import containers, providers

from SteamRoulette.admin.admin_provider import AdminProvider
from SteamRoulette.libs.auth.auth import init_admin_auth
from SteamRoulette.service.celery_task_manager import CeleryTaskManager
from SteamRoulette.service.db import init_db
from SteamRoulette.service.redis import init_redis
from SteamRoulette.service.user_auth import UserAuthService


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
    admin_auth = providers.Factory(
        init_admin_auth,
        redis=redis,
        db_engines=db_engines,
        config=config.admin_auth,
    )
    admin_auth_s = providers.Singleton(
        init_admin_auth,
        redis=redis,
        db_engines=db_engines,
        config=config.admin_auth,
    )
    admin_provider = providers.Factory(AdminProvider, admin_auth=admin_auth)
    admin_auth_service = providers.Factory(
        UserAuthService,
        auth=admin_auth,
        redis=redis
    )
