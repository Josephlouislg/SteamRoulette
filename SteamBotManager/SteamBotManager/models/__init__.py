import sqlalchemy as sa
from sqlalchemy import TypeDecorator, SmallInteger

metadata = sa.MetaData()


class EnumInt(TypeDecorator):

    impl = SmallInteger

    def __init__(self, enum, *args, **kwargs):
        self._enum = enum
        super().__init__(*args, **kwargs)

    def process_bind_param(self, enum, dialect):
        if enum is None:
            return None
        return enum.value

    def process_result_value(self, value, dialect):
        if value is not None:
            return self._enum(value)
        return value

    def copy(self, **kw):
        return EnumInt(self._enum)
