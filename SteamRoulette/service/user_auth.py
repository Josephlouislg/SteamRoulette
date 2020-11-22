import logging

from flask import request
from redis import Redis

from SteamRoulette.libs.auth.service import AuthService
from SteamRoulette.libs.utils.signer import signer_loads
from SteamRoulette.libs.utils.tools import get_remote_address
from SteamRoulette.models.base_user import BaseUser

log = logging.getLogger(__name__)


class UserDeletedError(Exception):
    pass


class InvalidDeviceError(Exception):
    pass


class UserAuthService:
    DEFAULT_LOGIN_TIME = 3600 * 24 * 180  # sec in hour * hours in day * days

    def __init__(self, auth: AuthService, redis: Redis):
        self._auth = auth
        self._redis = redis

    def login(self, user: BaseUser, request, *, device=None, hid=None, mode=None,
              device_type=None, max_age=DEFAULT_LOGIN_TIME):
        if user.is_deleted:
            raise UserDeletedError(user.id)
        # TODO: check if already logged in
        remote_addr = get_remote_address(request)[:255]
        if device:
            client_name = device[:500]
            if client_name.lower() == 'ios':
                device_type = self._auth.DeviceTypes.IOS
            elif client_name.lower() == 'android':
                device_type = self._auth.DeviceTypes.ANDROID
            else:
                raise InvalidDeviceError(client_name)
            data = {'hid': hid, 'mode': mode}
        else:
            client_name = request.user_agent.string[:500]
            if device_type is None:
                device_type = self._auth.DeviceTypes.DESKTOP
            data = None
        self._auth.sign_in(
            user.user_ident,
            max_age,
            device_type,
            client_name=client_name,
            remote_addr=remote_addr,
            data=data
        )
        return self._auth.client_session.session_key

    def logout(self):
        self._auth.sign_out()
