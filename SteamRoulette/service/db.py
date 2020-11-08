import logging
import typing
from types import SimpleNamespace

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlalchemy.ext.baked import bake_lazy_loaders
from sqlalchemy.orm import (
    sessionmaker,
    Query as SAQuery
)

from SteamRoulette.libs.rxid import get_current_rxid
from SteamRoulette.service.scoping import MasterSlaveScopedSession


log = logging.getLogger(__name__)
db = SQLAlchemy()


class Query(SAQuery):

    # def paginate(self, page, per_page=20) -> Pagination:
    #     if page < 1:
    #         raise ValueError("`page` param must be greater than 0")
    #
    #     items = self.limit(per_page).offset((page - 1) * per_page).all()
    #
    #     if page == 1 and len(items) < per_page:
    #         total = len(items)
    #     else:
    #         #  remove order clause and count
    #         total = self.order_by(None).count()
    #
    #     return Pagination(
    #         query=self,
    #         page=page,
    #         per_page=per_page,
    #         items=items,
    #         total=total,
    #     )

    def flat_all(self) -> typing.List[typing.Any]:
        """A convenience method for result sets with single column.

        Returns:
            flat list where elements is the first column.
        """
        return [x for (x, ) in self.all()]


master_session_factory = sessionmaker(autocommit=True, autoflush=False, query_cls=Query)
slave_session_factory = sessionmaker(autocommit=True, autoflush=False, query_cls=Query)
session = MasterSlaveScopedSession(master_session_factory, slave_session_factory)


def inject_request_id(conn, cursor, statement, parameters,
                      context, executemany):
    new = "{} /* {} */".format(statement, get_current_rxid())
    return new, parameters


def create_engine_slave(config, debug):
    db_engine = db.create_engine(
        config['dsn_slave'],
        {'echo': config['echo'], 'empty_in_strategy': 'static'}
    )

    # if debug:
    #     _EngineDebuggingSignalEvents(db_engine,
    #                                  'slave').register()

    # Inject Request ID into each DB query
    listen(db_engine, 'before_cursor_execute',
           inject_request_id, retval=True)
    return db_engine


def create_engine(config, debug):
    db_engine = db.create_engine(
        config['dsn'],
        {'echo': config['echo'], 'empty_in_strategy': 'static'}
    )
    # if debug:
    #     _EngineDebuggingSignalEvents(db_engine,
    #                                  'master').register()


    # Inject Request ID into each DB query
    listen(db_engine, 'before_cursor_execute',
           inject_request_id, retval=True)
    return db_engine


def init_session_master(db_engine, sessionmaker_opts):
    session.configure_master(bind=db_engine, **sessionmaker_opts)
    # listen(session, 'before_flush', _disallow_saving_models)
    # changes_listener = ObjectChangesTracker()
    # ModificationsTracker(changes_listener).install(master_session_factory)


def init_session_slave(db_engine, sessionmaker_opts):
    session.configure_slave(bind=db_engine, **sessionmaker_opts)


class DBEngines(SimpleNamespace):
    master: Engine
    slave: Engine


def init_db(
        config, sessionmaker_opts=None, slave_sessionmaker_opts=None,
        debug=False,
):
    bake_lazy_loaders()
    db_engine = create_engine(config, debug)
    if config.get('dsn_slave'):
        slave_db_engine = create_engine_slave(config, debug)
    else:
        slave_db_engine = db_engine
    session.remove()
    init_session_master(db_engine, sessionmaker_opts or {})
    init_session_slave(slave_db_engine, slave_sessionmaker_opts or {})
    log.debug('DB configured: url %s' % config)
    return DBEngines(master=db_engine, slave=slave_db_engine)
