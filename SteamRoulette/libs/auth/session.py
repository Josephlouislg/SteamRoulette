import json
from abc import abstractmethod, ABCMeta

from redis import Redis


DEFAULT_MAX_AGE = 3600 * 24


class Session(object):

    def __init__(self, session_storage, session_key):
        self._session_storage = session_storage
        self.session_key = session_key

    def get(self, key, default=None):
        return self._session_storage.get_key(self.session_key, key, default)

    def set(self, key, value, max_age=None):
        return self._session_storage.set_key(self.session_key, key, value,
                                             max_age)

    def delete(self, key):
        return self._session_storage.delete_key(self.session_key, key)

    def begin(self):
        pass  # TODO

    def flush(self):
        pass  # TODO


class SessionStorageBase(metaclass=ABCMeta):

    def get_session(self, session_key):
        return Session(self, session_key)

    @abstractmethod
    def get_key(self, session_key, key, default=None):
        pass

    @abstractmethod
    def set_key(self, session_key, key, value, max_age=None):
        pass

    @abstractmethod
    def delete_key(self, session_key, key, default=None):
        pass

    @abstractmethod
    def delete_bulk(self, session_keys, key):
        pass


class DummySessionStorage(SessionStorageBase):

    def delete_bulk(self, session_keys, key):
        pass

    def get_key(self, session_key, key, default=None):
        return default

    def set_key(self, session_key, key, value, max_age=None):
        pass

    def delete_key(self, session_key, key, default=None):
        return default


class RedisSessionStorage(SessionStorageBase):

    def __init__(self, redis_connection: Redis, prefix='auth.session',
                 serializer=json, default_max_age=DEFAULT_MAX_AGE):
        self._default_max_age = default_max_age
        self._redis_connection = redis_connection
        self._prefix = prefix
        self._serializer = serializer

    def get_key(self, session_key, key, default=None):
        key_ = '{}:{}:{}'.format(self._prefix, session_key, key)
        value = self._redis_connection.get(key_)
        if value is None:
            return default
        return self._serializer.loads(value.decode())

    def set_key(self, session_key, key, value, max_age=None):
        key_ = '{}:{}:{}'.format(self._prefix, session_key, key)
        value_ = self._serializer.dumps(value)
        max_age_ = max_age if max_age is not None else self._default_max_age
        self._redis_connection.setex(key_, max_age_, value_)

    def delete_key(self, session_key, key, default=None):
        key_ = '{}:{}:{}'.format(self._prefix, session_key, key)
        self._redis_connection.delete(key_)

    def delete_bulk(self, session_keys, key):
        keys = [f'{self._prefix}:{session_key}:{key}' for session_key in session_keys]
        return self._redis_connection.delete(*keys)
