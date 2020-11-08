import datetime
from decimal import Decimal
from enum import Enum
from types import SimpleNamespace

from flask.json import JSONEncoder


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.time, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return str(obj.value)
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, SimpleNamespace):
            return vars(obj)
        return super().default(obj)
