from sqlalchemy import func

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
