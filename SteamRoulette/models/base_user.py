from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, Unicode, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash

from SteamRoulette.libs.orm.types import EnumInt
from SteamRoulette.model_base import Base


class BaseUser(Base):

    __abstract__ = True

    class STATUS(Enum):
        active = 0
        blocked = 1
        deleted = 2

    id = Column(Integer, primary_key=True, nullable=False)
    status = Column(EnumInt(STATUS), default=STATUS.active)
    email = Column(Unicode(255), nullable=False, unique=True)
    first_name = Column(Unicode(100))
    middle_name = Column(Unicode(100))
    last_name = Column(Unicode(100))
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    _password = Column(Unicode(255), nullable=False, name='password')

    def __init__(self, **kwargs):
        if 'password' in kwargs:
            self.password = kwargs.pop('password')
        super().__init__(**kwargs)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, pwd):
        self._password = generate_password_hash(pwd, method='pbkdf2:sha512')

    def check_password(self, pwd):
        pwhash = self._password
        return check_password_hash(pwhash, pwd)
