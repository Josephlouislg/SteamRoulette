from functools import wraps


def decorator_with_params(decorator):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            return decorator(func, *args, **kwargs)
        return decorated
    return wrapper
