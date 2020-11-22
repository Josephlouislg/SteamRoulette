import logging
from functools import partial

from redis import Redis
from sqlalchemy import select

from SteamRoulette.libs.auth.service import AuthService
from SteamRoulette.libs.auth.session import RedisSessionStorage
from SteamRoulette.models.admin_user import UserAdmin
from SteamRoulette.models.user import User
from SteamRoulette.service.db import DBEngines


log = logging.getLogger(__name__)


def get_user_info(user_ident, is_admin, db_engine):
    user_table = UserAdmin if is_admin else User
    user = db_engine.execute(
        select([user_table.first_name, user_table.last_name, user_table.email])
        .where(user_table.id == user_table.id_from_ident(user_ident))
    ).first()
    if user:
        full_name = user.first_name
        return full_name, user['email']


def init_auth(config, redis, db_engine):
    client_session_storage = RedisSessionStorage(
        redis, prefix=config['redis_client_session_prefix'])
    user_session_storage = RedisSessionStorage(
        redis, prefix=config['redis_user_session_prefix'])

    user_info = partial(get_user_info, is_admin=False, db_engine=db_engine)

    auth = AuthService(
        user_info, db_engine, client_session_storage, user_session_storage
    )
    log.debug("Auth configured")
    return auth


def init_admin_auth(
        config,
        redis: Redis,
        db_engines: DBEngines,
):
    client_session_storage = RedisSessionStorage(
        redis, prefix=config['redis_client_session_prefix'])
    user_session_storage = RedisSessionStorage(
        redis, prefix=config['redis_user_session_prefix'])

    user_admin_info = partial(get_user_info, is_admin=True, db_engine=db_engines.master)

    admin_auth = AuthService(
        user_admin_info, db_engines.master,
        client_session_storage, user_session_storage
    )
    log.debug("Auth admin configured")
    return admin_auth
