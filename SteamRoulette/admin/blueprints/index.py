from flask import Blueprint, url_for

bp = Blueprint('index', __name__, url_prefix='/')


@bp.route('/')
def index():
    return url_for('trade_bots.bot_list')
