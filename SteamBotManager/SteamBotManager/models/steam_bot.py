from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from SteamBotManager.SteamBotManager.models import metadata, EnumInt


class STATUS(Enum):
    active = 0
    deleted = 1


steam_bot = sa.Table(
    'steam_bot', metadata,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('status', EnumInt(STATUS), default=STATUS.active),
    sa.Column('date_created', sa.DateTime, nullable=False, default=datetime.utcnow),
    sa.Column('date_modified', sa.DateTime, nullable=False, default=datetime.utcnow),
    sa.Column('username', sa.DateTime, nullable=False,),
    sa.Column('password', sa.DateTime, nullable=False),
    sa.Column('data', JSONB, nullable=False)  # {"sa_secrets" {...}}
)
