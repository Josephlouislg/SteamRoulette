from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import flag_modified

from SteamRoulette.libs.orm.types import EnumInt
from SteamRoulette.model_base import Base


class SteamBot(Base):
    __tablename__ = 'steam_bot'

    class STATUS(Enum):
        active = 0
        deleted = 1

    id = Column(Integer, primary_key=True)
    status = Column(EnumInt(STATUS), nullable=False, default=STATUS.active)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_modified = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_name = Column(String(500), nullable=False)
    password = Column(String(500), nullable=False)
    data = Column(JSONB, nullable=False)

    __table_args__ = (
    )

    @hybrid_property
    def sa_secrets(self):
        return self.data['sa_secrets']

    @sa_secrets.setter
    def sa_secrets(self, value):
        self.data['sa_secrets'] = value
        flag_modified(self, self.data.key)