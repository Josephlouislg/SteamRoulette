from enum import Enum

from sqlalchemy import Column, Integer

from SteamRoulette.libs.orm import EnumInt
from SteamRoulette.model_base import Base


class User(Base):
    __tablename__ = 'user'

    class STATUS(Enum):
        active = 0
        deleted = 1
        draft = 2

    id = Column(Integer, primary_key=True, nullable=False)
    status = Column(EnumInt(STATUS), default=STATUS.active)
