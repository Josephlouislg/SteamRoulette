from enum import Enum

from sqlalchemy import Integer, Column
from sqlalchemy.dialects.postgresql import ARRAY

from SteamRoulette.libs.orm.types import EnumInt
from SteamRoulette.models.base_user import BaseUser
from SteamRoulette.service.db import session


class UserAdmin(BaseUser):
    __tablename__ = 'user_admin'

    class ROLE(Enum):
        super_admin = 0
        moderator = 1

    id = Column(Integer, primary_key=True, nullable=False)
    roles = Column(ARRAY(EnumInt(ROLE)), nullable=False, default=[ROLE.moderator])

    @classmethod
    def get_by_email(cls, email):
        return session.query(cls).filter_by(email=email).first()

    @property
    def user_ident(self) -> str:
        if self.id is None:
            raise RuntimeError('user must be persisted')
        return f'admin-{self.id}'
