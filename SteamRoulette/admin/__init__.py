from SteamRoulette.admin.blueprints.trade_bots import *
from SteamRoulette.admin.blueprints import trade_bots
from SteamRoulette.admin.blueprints import index
BLUEPRINTS = [
    *trade_bots.BLUEPRINTS,
    index.bp,   # must be last
]
