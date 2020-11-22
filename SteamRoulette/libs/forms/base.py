from collections import Mapping

from werkzeug.datastructures import MultiDict
from flask import request
from wtforms import Form as _Form
from wtforms.fields import FileField


_Auto = ...


class Form(_Form):
    def __init__(self, formdata=_Auto, obj=None, prefix='', **kwargs):
        if formdata is _Auto:
            if request and request.method in ("PUT", "POST", "PATCH"):
                formdata = request.form
                if request.files:
                    formdata = formdata.copy()
                    formdata.update(request.files)
                elif request.json:
                    formdata = MultiDict(request.json)
            else:
                formdata = None
        super(Form, self).__init__(
            formdata, obj, prefix,
            **kwargs
        )

    def get_file_fields(self):
        return {name: field for name, field in self._fields.items() if isinstance(field, FileField)}

    def error_response(self, skip_file_fields=False, skip_status=False):
        errors = self.errors
        if self._prefix:
            errors = {(self._prefix + k): v for k, v in errors.items()}
        if skip_file_fields:
            errors = {k: v for k, v in errors.items() if k not in self.get_file_fields().keys()}

        if skip_status:
            return {'errors': errors}

        return {'status': 'error', 'errors': errors}

    @property
    def errors_as_str(self, sep='\n'):
        return sep.join(str(msg) for field in self for msg in field.errors)

    @classmethod
    def from_json(cls, formdata=_Auto, obj=None, prefix='', *args, **kwargs):
        if formdata is _Auto:
            formdata = request.get_json()

        return cls(
            formdata=MultiDict(
                flatten_dict(formdata)
            ) if formdata else None,
            obj=obj,
            prefix=prefix,
            *args, **kwargs
        )

    @classmethod
    def from_kw(cls, **kwargs):
        return cls(formdata=MultiDict(kwargs))


def flatten_dict(mapping, separator='-'):
    """
    >>> flatten_dict({'a': {'b': 0}, 'c': [1, 2]})
    {'a-b': 0, 'c-0': 1, 'c-1': 2}
    """
    if not isinstance(mapping, Mapping):
        raise TypeError("Not a mapping")

    flat_dict = {}
    stack = [None, mapping]
    while stack:
        current, key = stack.pop(), stack.pop()
        if isinstance(current, Mapping):
            for k, element in current.items():
                new_key = key + separator + k if key else k
                stack.append(new_key)
                stack.append(element)
        elif isinstance(current, list):
            for i, element in enumerate(current):
                new_key = key + separator + str(i)
                stack.append(new_key)
                stack.append(element)
        else:
            if current is None:  # WTForms cant handle Nones
                current = ''
            elif current is False:
                current = 'false'
            flat_dict[key] = current

    return flat_dict


def list_to_choices(items):
    return tuple((value, title) for value, title in enumerate(items))
