from sqlalchemy import func
from steam.guard import SteamAuthenticator
from steam.webauth import MobileWebAuth, TwoFactorCodeRequired

from SteamRoulette.models.steam_bot import SteamBot
from SteamRoulette.service.db import session


@session.readonly
def get_bot_list_c(page=1, per_page=20):
    rows = (
        session.query(SteamBot)
        .order_by(SteamBot.id)
        .offset(per_page * (page - 1))
        .limit(per_page)
        .all()
    )
    items_count = (
        session.query(func.count(SteamBot.id))
        .scalar()
    )
    result = []
    if not rows:
        return result

    for sb in rows:
        sb: SteamBot
        result.append({
            "username": sb.username,
            "date_created": sb.date_created,
            "date_modified": sb.date_modified,
            "status": sb.status.value,
            "id": sb.id,
        })
    return {
        "items_count": items_count,
        "bots": result
    }


@session.readonly
def get_steam_bot_details(bot_id):
    if not bot_id:
        return
    bot: SteamBot = (
        session.query(SteamBot)
        .filter(SteamBot.id == bot_id)
        .first()
    )
    if not bot:
        return
    data = {
        "bot_id": bot.id,
        "status": bot.status.value,
        "username": bot.username,
        "steam_id": bot.steam_id,
        "date_created": bot.date_created,
        "date_modified": bot.date_modified
    }
    return data


def remove_sb_guard(bot_id):
    if not bot_id:
        return
    with session.begin():
        bot = SteamBot.get_for_update(bot_id)
        if not bot or bot.status != SteamBot.STATUS.active:
            return
        wa = MobileWebAuth(bot.username, password=bot.password)
        revocation_code = bot.revocation_code
        steam_auth = SteamAuthenticator(secrets=bot.sa_secrets)
        try:
            wa.login(password=bot.password)
        except TwoFactorCodeRequired:
            wa.login(password=bot.password, twofactor_code=steam_auth.get_code())
        steam_auth.backend = wa
        steam_auth.remove(revocation_code=revocation_code)
        bot.status = SteamBot.STATUS.need_guard
        bot.sa_secrets = None
