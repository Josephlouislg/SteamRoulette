import os
import random
import time
from contextlib import closing, contextmanager
from datetime import datetime, timedelta
from hashlib import sha1, md5

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from werkzeug.local import LocalStack
from werkzeug.utils import cached_property

from SteamRoulette.libs.auth.session import DummySessionStorage
from SteamRoulette.libs.auth.users import AuthenticatedUser, AnonymousUser
from SteamRoulette.models.user_session import UserSession, DeviceTypes
from SteamRoulette.service.db import DBEngines


class _RemoteUser:

    def __init__(self, user_id):
        self.user_id = user_id

    @classmethod
    def loads(cls, string):
        return cls(string)

    def dumps(self):
        return '{user_id}'.format(user_id=self.user_id)


class _Context:

    def __init__(self, auth_service, secure_session_key):
        self._auth_service = auth_service
        self._secure_session_key = secure_session_key

    @cached_property
    def client_session(self):
        if self._secure_session_key:
            return (
                self._auth_service.client_session_storage
                .get_session(self._secure_session_key)
            )
        else:
            return DummySessionStorage().get_session(None)

    @cached_property
    def _remote_user(self):
        remote_user_data = self.client_session.get('remote_user')
        if remote_user_data:
            return _RemoteUser.loads(remote_user_data)

    @cached_property
    def user_session(self):
        if self._remote_user:
            return (
                self._auth_service.user_session_storage
                .get_session(self._remote_user.user_id)
            )
        else:
            return DummySessionStorage().get_session(None)

    @cached_property
    def user(self):
        if self._remote_user:
            user_info = self._auth_service._get_user_info(
                self._remote_user.user_id)
            if user_info:
                user_name, user_email = user_info
                return AuthenticatedUser(self._remote_user.user_id,
                                         user_name,
                                         self._remote_user.scopes,
                                         _email=user_email)
        return AnonymousUser()


class AuthService:
    DeviceTypes = DeviceTypes

    def __init__(
        self, user_info_loader, db_engine,
        client_session_storage, user_session_storage
    ):
        self._ctx_var = LocalStack()
        self._user_info_loader = user_info_loader
        self._session_maker = sessionmaker(db_engine, autoflush=False,
                                           autocommit=True)
        self.client_session_storage = client_session_storage
        self.user_session_storage = user_session_storage

    @property
    def client_session(self):
        return self._ctx_var.top.client_session

    @property
    def user_session(self):
        return self._ctx_var.top.user_session

    @property
    def user(self):
        return self._ctx_var.top.user

    @classmethod
    def gen_session_key(cls):
        vars_ = (time.time(), id({}), random.random(), os.getpid())
        return sha1(md5((''.join(map(str, vars_))).encode()).hexdigest().encode()).hexdigest()

    @contextmanager
    def using(self, secure_session_key):
        self._ctx_var.push(_Context(self, secure_session_key))
        try:
            yield
        finally:
            self._ctx_var.pop()

    def sign_in(self, user_ident, max_age, device_type,
                client_name=None, remote_addr=None, data=None):
        assert isinstance(user_ident, str)
        session_key = self.client_session.session_key
        if not session_key:
            return
        with closing(self._session_maker()) as db_session, db_session.begin():
            session_table = UserSession.__table__
            session_data = dict(
                user_ident=user_ident,
                device_type=device_type,
                client_name=client_name,
                remote_addr=remote_addr,
                data=data,
                expiration_time=datetime.utcnow() + timedelta(seconds=max_age)
            )
            stmt = (
                insert(session_table)
                .values(session_key=session_key, **session_data)
                .on_conflict_do_update(
                    index_elements=[session_table.c.session_key],
                    set_=dict(**session_data),
                )
            )
            db_session.connection().execute(stmt)

        remote_user = _RemoteUser(user_ident)
        self.client_session.set('remote_user', remote_user.dumps(), max_age)
        self.client_session.flush()

    def sign_out(self):
        remote_user = self.client_session.get('remote_user')
        if remote_user:
            admin_id = self.client_session.get('admin_id')
            if admin_id:
                user = request.user
                user.add_activity(Activity(
                    verb=VERB.sudo_logout,
                    admin_id=admin_id,
                ))
                session.flush()
                self.client_session.delete('admin_id')

            self.client_session.delete('remote_user')
            self.client_session.flush()
            with closing(self._session_maker()) as db_session:
                with db_session.begin():
                    (db_session.query(UserSession)
                     .filter(UserSession.session_key == self.client_session.session_key)
                     .update({'status': UserSession.STATUS.deleted})
                     )

    def _get_user_info(self, user_ident):
        return self._user_info_loader(user_ident)

    def get_last_sessions(self, user_ident):
        now = datetime.utcnow()
        with closing(self._session_maker()) as db_session:
            user_sessions = (
                db_session.query(UserSession)
                .filter(UserSession.user_ident == user_ident)
                .filter(UserSession.expiration_time > now)
                .order_by(UserSession.creation_time.desc())
            )
        return user_sessions

    def get_session_device(self, session_key) -> UserSession:
        with closing(self._session_maker()) as db_session:
            return (
                db_session.query(UserSession.device_type)
                .filter(UserSession.session_key == session_key)
                .scalar()
            )

    def clean_expired_sessions(self, limit):
        now = datetime.utcnow()
        with closing(self._session_maker()) as db_session:
            with db_session.begin():
                sessions_to_delete = (
                    db_session.query(UserSession.session_key)
                    .filter(
                        UserSession.expiration_time < now,
                        UserSession.is_active()
                    )
                    .order_by(UserSession.creation_time)
                    .limit(limit)
                    .all()
                )
                if not sessions_to_delete:
                    return 0
                keys = [sess.session_key for sess in sessions_to_delete]
                updated_count = (
                    db_session.query(UserSession)
                    .filter(UserSession.session_key.in_(keys))
                    .update(synchronize_session=False, values={'status': UserSession.STATUS.deleted})
                )
                self.drop_sessions_from_storage(keys)
        return updated_count

    def delete_sessions(self, user_ident, exclude=()):
        with closing(self._session_maker()) as db_session:
            query = (
                UserSession.__table__.update().values({"status": UserSession.STATUS.deleted})
                .where(UserSession.user_ident == user_ident)
            )
            if exclude:
                query = query.where(UserSession.session_key.notin_(exclude))
            query = query.returning(UserSession.session_key)

            res = db_session.execute(query).fetchall()
            if self._ctx_var.top:
                self.sign_out()
            for session_key, in res:
                self.client_session_storage.delete_key(session_key, 'remote_user')

    def drop_sessions_from_storage(self, session_keys):
        return self.client_session_storage.delete_bulk(session_keys, 'remote_user')

    def get_user_sessions(self, user_ident):
        with closing(self._session_maker()) as db_session:
            user_sessions = (
                db_session.query(UserSession)
                .filter(UserSession.user_ident == user_ident)
                .all()
            )
        return user_sessions
