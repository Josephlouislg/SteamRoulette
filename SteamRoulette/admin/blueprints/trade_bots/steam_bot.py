from flask import Blueprint, abort, request

from SteamRoulette.admin.controllers.steam_bot_c import get_bot_list_c
from SteamRoulette.libs.utils.tools import ok

bp = Blueprint('trade_bots', __name__, url_prefix='/api/trade-bots')


@bp.route('/list')
@bp.route('/list/<int:page>')
def bot_list(page=1):
    if page < 1:
        abort(404)
    per_page = request.args.get('per_page', type=int, default=20)
    bots = get_bot_list_c(page, per_page=per_page)
    return ok(data=bots)
