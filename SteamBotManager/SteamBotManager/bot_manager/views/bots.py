import json
import logging.handlers

from aiohttp import web, WSMsgType
from prometheus_async.aio import time

from SteamBotManager.SteamBotManager.prometheus_setup import RESPONSE_TIME

from SteamBotManager.SteamBotManager.services.bot_register import SteamBotRegistrationService, LoginErrors, WebAuthError


log = logging.getLogger(__name__)


async def process_msg():
    ws = yield
    msg = yield
    bot_register_service = None
    if msg['type'] == 'init':
        bot_register_service = SteamBotRegistrationService(password=msg['password'], username=msg['username'])
    register_process = bot_register_service.add_authenticator()
    for error, error_data in register_process:
        if error == LoginErrors.success:
            break
        resp_data = {
            "error": error.value,
            "error_data": error_data
        }
        await ws.send_str(json.dumps(resp_data))
        msg = yield
        register_process.send(msg['code'])
    try:
        bot_register_service.check_web_client()
    except WebAuthError as e:
        resp_data = {
            "error": LoginErrors.web_auth_session.value,
            "error_data": {"status_code": e.status_code}
        }
        await ws.send_str(json.dumps(resp_data))
    bot_register_service.save_bot()


@time(RESPONSE_TIME.labels('bot_registration'))
async def bot_register(request):
    ws = web.WebSocketResponse()
    can_prepare = ws.can_prepare(request)
    if not can_prepare.ok:
        rs = web.Response(status=400)
        rs.force_close()
        return rs
    await ws.prepare(request)

    message_process = process_msg()
    message_process.send(ws)
    try:
        async for ws_msg in ws:
            if ws_msg.type == WSMsgType.text:
                msg = json.loads(ws_msg.data)
                message_process.send(msg)
            elif ws_msg.type == WSMsgType.error:
                log.info('websocket closed with error')
            elif ws_msg.type == WSMsgType.close:
                log.info('websocket closed normally')
    finally:
        return ws
