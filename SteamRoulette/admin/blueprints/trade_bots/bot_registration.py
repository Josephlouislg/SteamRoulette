from dependency_injector.wiring import Provide
from flask import Blueprint
from redis import Redis

from SteamRoulette.containers import AppContainer
from SteamRoulette.service.taskqueue import Queues
from SteamRoulette.tasks.trade_bot import test

bp = Blueprint('trade_bots', __name__, url_prefix='/api/trade-bots')


@bp.route('/list', defaults={'page': 'index'})
def bot_list(page):
    return bot_list_(page)


def bot_list_(page, redis: Redis = Provide[AppContainer.redis]):
    redis.set('1', '200')
    test.delay()
    test.apply_async(args=[], queue=Queues.DEFAULT.value.name)
    return redis.get('1')
