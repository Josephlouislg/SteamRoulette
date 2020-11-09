from sqlalchemy import TypeDecorator, SmallInteger
from sqlalchemy.ext.mutable import Mutable


class Dict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, Dict):
            if isinstance(value, dict):
                return Dict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()


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
