class AnonymousUser(object):
    is_authenticated = False
    ident = None
    name = 'Anonymous'
    scopes = ()


class SystemUser(object):
    is_authenticated = True
    ident = None

    def __init__(self, name):
        self.name = name


class AuthenticatedUser(object):
    is_authenticated = True

    def __init__(self, ident, name, scopes, _email):
        self.ident = ident
        self.name = name
        self.scopes = scopes
        self._email = _email
