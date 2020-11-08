import logging

from redis import Redis
from redis.sentinel import Sentinel


log = logging.getLogger(__name__)


def init_redis(config):
    log.info('init redis')
    if 'sentinel' in config:
        sentinel_conf = config['sentinel']
        socket_timeout = sentinel_conf['socket_timeout']
        sentinel = Sentinel(sentinel_conf['sentinels'],
                            socket_timeout=socket_timeout)
        redis = sentinel.master_for(sentinel_conf['service_name'],
                                    redis_class=Redis,
                                    socket_timeout=socket_timeout,
                                    db=config['db'])
    else:
        redis = Redis(**config)
    log.debug('Redis configured, %r' % config)
    yield redis
