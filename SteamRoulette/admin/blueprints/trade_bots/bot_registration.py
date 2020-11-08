from dependency_injector.wiring import Provide
from flask import Blueprint
from redis import Redis

from SteamRoulette.admin.containers import Container

bp = Blueprint('trade_bots', __name__, url_prefix='/api/trade-bots')


@bp.route('/list', defaults={'page': 'index'})
def bot_list(page):
    return bot_list_(page)


def bot_list_(page, redis: Redis = Provide[Container.redis]):
    redis.set('1', '200')
    return redis.get('1')
