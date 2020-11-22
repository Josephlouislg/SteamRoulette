import logging

from dependency_injector.wiring import Provide
from flask import Blueprint, request
from werkzeug.datastructures import MultiDict

from SteamRoulette.admin.form.auth import AdminLoginForm
from SteamRoulette.containers import AppContainer
from SteamRoulette.libs.utils.tools import ok
from SteamRoulette.models.admin_user import UserAdmin
from SteamRoulette.service.db import session
from SteamRoulette.service.user_auth import UserAuthService

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


log = logging.getLogger(__name__)


def _serialize_admin(admin):
    if not admin:
        return None
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
    form = AdminLoginForm(formdata=MultiDict(request.get_json()))
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
def info():
    admin = request.admin
    return ok(data=_serialize_admin(admin))


@bp.route('/create_admin')
def create_admin():
    with session.begin():
        admin = UserAdmin(
            roles=(UserAdmin.ROLE.super_admin,),
            first_name='root',
            last_name='root',
            email='root@gmail.com',
        )
        admin.password = 'root'
        session.add(admin)
    return ok()
