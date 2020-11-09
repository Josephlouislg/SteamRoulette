from enum import Enum

from sqlalchemy import Integer, Column
from sqlalchemy.dialects.postgresql import ARRAY

from SteamRoulette.libs.orm.types import EnumInt
from SteamRoulette.models.base_user import BaseUser


class UserAdmin(BaseUser):
    __tablename__ = 'user_admin'

    class ROLE(Enum):
        super_admin = 0
        moderator = 1

    id = Column(Integer, primary_key=True, nullable=False)
    roles = Column(ARRAY(EnumInt(ROLE)), nullable=False, default=[ROLE.moderator])
