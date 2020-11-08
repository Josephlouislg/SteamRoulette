from redis import Redis


class CeleryTaskManager(object):
    TASKS_FOR_DROP_KEY = "TASKS_FOR_DROP_KEY"

    def __init__(self, redis: Redis):
        self._redis = redis

    def need_drop_task(self, task_name: str) -> bool:
        return bool(self._redis.sismember(self.TASKS_FOR_DROP_KEY, task_name))

    def drop_task(self, task_name: str):
        self._redis.sadd(self.TASKS_FOR_DROP_KEY, task_name)

    def remove_task_from_drop_set(self, task_name: str):
        self._redis.srem(self.TASKS_FOR_DROP_KEY, task_name)

    def get_stopped_tasks(self):
        return [task_name.decode() for task_name in self._redis.smembers(self.TASKS_FOR_DROP_KEY)]
