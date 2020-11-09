from itsdangerous import URLSafeTimedSerializer

from SteamRoulette.config import get_config

DEFAULT_SALT = 'SteamRoulette.libs.signer'


def signer_dumps(data, *, salt=DEFAULT_SALT):
    key = get_config('flask.SECRET_KEY')
    return URLSafeTimedSerializer(key, salt=salt).dumps(data)


def signer_loads(data, *, salt=DEFAULT_SALT, max_age=None):
    key = get_config('flask.SECRET_KEY')
    return URLSafeTimedSerializer(key, salt=salt).loads(data, max_age=max_age)
