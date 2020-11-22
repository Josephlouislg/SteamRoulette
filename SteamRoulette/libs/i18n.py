def gettext(val, **kw):
    return val % kw if kw else val


_ = gettext
