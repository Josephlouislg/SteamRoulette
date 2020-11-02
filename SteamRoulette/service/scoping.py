from contextlib import contextmanager

import sqlalchemy
from sqlalchemy.util import ScopedRegistry, ThreadLocalRegistry

from SteamRoulette.libs.decorators import decorator_with_params


class MasterSlaveScopedSession(sqlalchemy.orm.scoping.scoped_session):

    def __init__(self, master_session_factory, slave_session_factory,
                 scopefunc=None):
        super(MasterSlaveScopedSession, self).__init__(master_session_factory,
                                                       scopefunc=scopefunc)
        self.slave_session_factory = slave_session_factory
        self.slave_session_cls = self.slave_session_factory.class_

        if scopefunc:
            self.slave_registry = ScopedRegistry(slave_session_factory,
                                                 scopefunc)
        else:
            self.slave_registry = ThreadLocalRegistry(slave_session_factory)

    def configure(self, **kwargs):
        self.configure_master(**kwargs)
        self.configure_slave(**kwargs)

    def configure_master(self, **kwargs):
        self.session_factory.configure(**kwargs)

    def configure_slave(self, **kwargs):
        self.slave_session_factory.configure(**kwargs)

    def readonly(self, func=None):
        @contextmanager
        def ctx():
            current = self.registry() if self.registry.has() else None
            if isinstance(current, self.slave_session_cls):
                yield
                return

            slave_session = self.slave_registry()
            self.registry.set(slave_session)
            try:
                yield
            finally:
                if current is not None:
                    self.registry.set(current)
                else:
                    self.registry.clear()

        if func is None:
            return ctx()
        else:
            @decorator_with_params
            def decorated(fn, *args, **kwargs):
                with ctx():
                    return fn(*args, **kwargs)
            return decorated(func)

    def remove(self):
        current = self.registry() if self.registry.has() else None
        assert not isinstance(current, self.slave_session_cls), current
        super(MasterSlaveScopedSession, self).remove()
        if self.slave_registry.has():
            self.slave_registry().close()
        self.slave_registry.clear()
