from flask import Blueprint

bp = Blueprint('trade_bots', __name__, url_prefix='/trade-bots')


@bp.route('/list', defaults={'page': 'index'})
def bot_list(page):
    return "200"
