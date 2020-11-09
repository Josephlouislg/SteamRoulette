from SteamRoulette.libs.auth.service import AuthService
from SteamRoulette.models.admin_user import UserAdmin


class AdminProvider:
    def __init__(self, admin_auth: AuthService):
        self._auth = admin_auth

    def get(self, request: 'AdminRequest') -> UserAdmin:
        user_ident = self._auth.user_session.session_key
        if user_ident:
            user = UserAdmin.get(UserAdmin.id_from_ident(user_ident))
            return user
