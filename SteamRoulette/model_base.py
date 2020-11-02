from typing import TypeVar, Type, List

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import joinedload
from sqlalchemy.util import immutabledict

from SteamRoulette.service.db import session


def _with_joinedloads(query, load, innerjoin=False):
    if not load:
        return query
    joins = []
    for rel in load:
        if isinstance(rel, str):
            first, *tail = rel.split('.')
            join = joinedload(first, innerjoin=innerjoin)
            for child in tail:
                join = join.joinedload(child, innerjoin=innerjoin)
        else:
            join = joinedload(rel)
        joins.append(join)
    return query.options(*joins)


naming_convention = immutabledict({
    'uq': '%(table_name)s_%(column_0_N_name)s_key',    # unique constraint
    'ix': '%(table_name)s_%(column_0_N_name)s_idx',    # index
    'pk': '%(table_name)s_pkey',                       # primary key
    'fk': '%(table_name)s_%(column_0_N_name)s_fkey',   # foreign key
    'ck': '%(table_name)s_%(column_0_N_name)s_check',  # check constraint
})
metadata = MetaData(naming_convention=naming_convention)

T = TypeVar('T')


class Base(declarative_base(metadata=metadata)):
    __abstract__ = True

    @classmethod
    def get(cls: Type[T], id_, *, load=(), session=session) -> T:
        """Fetch one record.

        >>> User.get(1, load=['performer'])

        Arguments:
            id_ (int): id of a record to fetch.
            load (iterable[str]): Iterable of strings which describe related
                records that should be eagerly joined. Strings should follow
                `joinedload_all` format.

        Returns:
            Fetched record or `None`
        """
        if id_ is None:
            return None
        if not load:
            return session.query(cls).get(id_)
        q = session.query(cls).filter_by(id=id_)
        return _with_joinedloads(q, load).first()

    @classmethod
    def get_for_update(cls: Type[T], id_, load=(), session=session) -> T:
        assert session.is_active,  \
            '`FOR UPDATE` outside an active transaction is useless'
        session.flush()

        q = session.query(cls).filter_by(id=id_)
        # `populate_existing()` is needed to ensure that
        # instances are consistent with the state of DB.
        return (_with_joinedloads(q, load, innerjoin=True)
                .with_for_update()
                .populate_existing()
                .first())

    @classmethod
    def get_many(cls: Type[T], ids, session=session) -> List[T]:
        """Fetch many records filtered by IDs."""
        return session.query(cls).filter(cls.id.in_(ids)).all()

    @classmethod
    def get_all(cls):
        """Fetch all records."""
        return session.query(cls)

    def update_from_dict(self, dict_, exclude_fields=None):
        colnames = set(c.name for c in self.__table__.c)
        if exclude_fields is not None:
            exclude = set(exclude_fields)
        else:
            exclude = set()
        names = set(dict_) - exclude
        for name in names & colnames:
            setattr(self, name, dict_[name])
        for name in names - colnames:
            if not hasattr(self, name):
                continue
            if callable(getattr(self, name)):
                continue
            setattr(self, name, dict_[name])

    def __repr__(self):
        if hasattr(self, 'id'):
            class_name = self.__class__.__name__
            return f'<{self.__module__}.{class_name}(id={self.id})>'
        return super().__repr__()
