from enum import Enum

from aiopg import sa
from sqlalchemy.dialects.postgresql import insert
from steam.guard import SteamAuthenticator
from steam.webauth import MobileWebAuth, CaptchaRequired, LoginIncorrect, EmailCodeRequired, TwoFactorCodeRequired
import steam.webauth as web_auth

from SteamBotManager.SteamBotManager.models.steam_bot import steam_bot


class LoginErrors(Enum):
    invalid_password = 0
    captcha = 1
    email_code = 2
    two_factor_code = 3
    guard_setup_code = 4
    success = 5
    web_auth_session = 6


class WebAuthError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


class SteamBotRegistrationService(object):
    def __init__(self, password, username, pg_engine: sa.Engine):
        self._pg_engine = pg_engine
        self._password = password
        self._username = username
        self._guard_secrets = None

    def add_authenticator(self):
        # TODO: USE PROXY
        # There have been too many login failures from your network in a short time period.
        # Please wait and try again later.

        wa = MobileWebAuth(self._username, password=self._password)
        captcha, email_code, twofactor_code = '', '', ''
        while True:
            try:
                wa.login(self._password, captcha, email_code, twofactor_code, 'english')
            except (LoginIncorrect, CaptchaRequired) as exp:
                email_code = twofactor_code = ''

                if isinstance(exp, LoginIncorrect):
                    error_data = {"msg": "Invalid password"}
                    self._password = yield LoginErrors.invalid_password, error_data
                    yield
                if isinstance(exp, CaptchaRequired):
                    captcha = yield LoginErrors.captcha, {"captcha_url": wa.captcha_url, "msg": "Enter captcha"}
                    yield
                else:
                    captcha = ''
            except EmailCodeRequired:
                twofactor_code = ''
                error_data = {"msg": "Enter email_code" if not email_code else "Incorrect code. Enter email code"}
                email_code = yield LoginErrors.email_code, error_data
                yield
            except TwoFactorCodeRequired:
                error_data = {"msg": "Enter 2FA code" if not twofactor_code else "Incorrect code. Enter 2FA code"}
                email_code = ''
                twofactor_code = yield LoginErrors.two_factor_code, error_data
                yield
            else:
                break

        steam_auth = SteamAuthenticator(backend=wa)
        steam_auth.add()
        code = yield LoginErrors.guard_setup_code, {"msg": "Enter SMS code for steam guard"}
        yield
        steam_auth.finalize(code)
        self._guard_secrets = steam_auth.secrets
        return LoginErrors.success, None

    def get_guard(self):
        steam_auth = SteamAuthenticator(secrets=self._guard_secrets)
        return steam_auth

    def check_web_client(self):
        user = web_auth.WebAuth(self._username)
        try:
            user.login(self._password)
        except web_auth.TwoFactorCodeRequired:
            guard = self.get_guard()
            user.login(twofactor_code=guard.get_code())
            resp = user.session.get('https://store.steampowered.com/account/history/')
            if not resp.status_code == 200:
                raise WebAuthError(resp.status_code)

    async def save_bot(self):
        async with self._pg_engine.acquire() as conn:
            result = await conn.execute(
                insert(steam_bot)
                .values([
                    {
                        "username": self._username,
                        "password": self._password,
                        "data": {"sa_secrets": {self._guard_secrets}}
                    }
                ])
                .returning(steam_bot.c.id)
            )
            ids = [row.id for row in (await result.fetchall())][0]
            return ids
