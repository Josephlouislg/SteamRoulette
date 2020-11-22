from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB

from SteamRoulette.libs.orm.types import EnumInt, Dict
from SteamRoulette.model_base import Base


class DeviceTypes(object):
    DESKTOP = 1
    IOS = 2
    ANDROID = 3


class UserSession(Base):
    __tablename__ = 'auth_user_session'

    class STATUS(Enum):
        active = 0
        deleted = 1

    session_key = Column(String(255), primary_key=True, nullable=False)
    status = Column(EnumInt(STATUS), nullable=False, default=STATUS.active)
    user_ident = Column(String(255),)
    creation_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    expiration_time = Column(DateTime, nullable=False)
    device_type = Column(Integer, nullable=False)
    client_name = Column(String(500))
    remote_addr = Column(String(255))
    data = Column(Dict.as_mutable(JSONB))
    # when device_type in (MOBILE, IOS, ANDROID), hid is stored here

    __table_args__ = (
        Index('%s_user_ident_creation_time' % __tablename__,
              user_ident, creation_time),
        Index('%s_expiration_time' % __tablename__,
              expiration_time),
    )

    def set_expire(self, seconds):
        self.expiration_time = datetime.utcnow() + timedelta(seconds=seconds)

    def to_dict(self):
        return dict(
            session_key=self.session_key,
            status=self.status,
            user_ident=self.user_ident,
            creation_time=self.creation_time,
            expiration_time=self.expiration_time,
            device_type=self.device_type,
            client_name=self.client_name,
            remote_addr=self.remote_addr,
            data=self.data,
        )
