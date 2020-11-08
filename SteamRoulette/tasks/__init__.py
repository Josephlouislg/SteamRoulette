import importlib

from celery.app.task import Task


def register_tasks(real_app):
    module_names = (
        'trade_bot',
    )
    for module_name in module_names:
        mod = importlib.import_module(__name__ + '.' + module_name)
        for name in dir(mod):
            attr = getattr(mod, name)
            if isinstance(attr, Task):
                attr.app = real_app
            elif isinstance(attr, type(Task)) and attr != Task:
                # attr.bind(real_app)
                pass