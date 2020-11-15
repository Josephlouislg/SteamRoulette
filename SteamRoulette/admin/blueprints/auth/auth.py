import logging

from dependency_injector.wiring import Provide
from flask import Blueprint, request

from SteamRoulette.admin.form.auth import AdminLoginForm
from SteamRoulette.containers import AppContainer
from SteamRoulette.libs.utils.tools import ok
from SteamRoulette.service.user_auth import UserAuthService

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


log = logging.getLogger(__name__)


def _serialize_admin(admin):
    return {
        'admin': {
            'name': admin.first_last_name,
            'roles': [role.value for role in admin.roles],
        }
    }


@bp.route('/login', methods=('POST', ))
def login_view():
    return login_view_c()


def login_view_c(admin_auth_service: UserAuthService = Provide[AppContainer.admin_auth_service]):
    form = AdminLoginForm()
    is_valid = form.validate()
    user = form.user

    if not is_valid:
        return form.error_response()
    admin_auth_service.login(user, request)
    return ok(data=_serialize_admin(user))


@bp.route('/logout', methods=('POST', ))
def logout():
    return logout_c()


def logout_c(admin_auth_service: UserAuthService = Provide[AppContainer.admin_auth_service]):
    admin_auth_service.logout()
    return ok()


@bp.route('/info')
def show():
    admin = request.admin
    return ok(data=_serialize_admin(admin))
