import asyncio
import json
import logging.handlers

from aiohttp import web, WSMsgType
from prometheus_async.aio import time

from SteamBotManager.SteamBotManager.prometheus_setup import RESPONSE_TIME
from SteamBotManager.SteamBotManager.services.bot_register import SteamBotRegistrationService, LoginErrors, WebAuthError


log = logging.getLogger(__name__)


async def save_bot_and_notify(ws, bot_service: SteamBotRegistrationService, msg):
    bot_id = await asyncio.shield(bot_service.save_bot())
    msg['bot_id'] = bot_id
    await ws.send_str(json.dumps(msg))


def registration_process_msg(pg_engine):
    ws = yield
    msg = yield
    bot_register_service = None
    if msg['type'] == 'init':
        bot_register_service = SteamBotRegistrationService(
            password=msg['password'],
            username=msg['username'],
            pg_engine=pg_engine
        )
    register_process = bot_register_service.add_authenticator()
    for error, error_data in register_process:
        if error == LoginErrors.success:
            break
        resp_data = {
            "error": error.value,
            "error_data": error_data,
            "message_type": 'bot_registration',
        }
        msg = yield ws.send_str(json.dumps(resp_data))
        register_process.send(msg['code'])
        
    resp_data = {}
    try:
        bot_register_service.check_web_client()
    except WebAuthError as e:
        resp_data = {
            "error": LoginErrors.web_auth_session.value,
            "error_data": {"status_code": e.status_code},
            "message_type": 'bot_registration',
        }
    else:
        resp_data = {
            "error": LoginErrors.success.value,
            "error_data": {"msg": "Success registered"},
            "message_type": 'bot_registration',
        }
    finally:
        yield save_bot_and_notify(ws, bot_register_service, resp_data)


message_types_processors = {
    "bot_registration": registration_process_msg,
}


async def ws_ping_task(ws):
    while True:
        await ws.ping()
        await asyncio.sleep(5)


@time(RESPONSE_TIME.labels('bot_registration'))
async def bot_register(request):
    ws = web.WebSocketResponse()
    can_prepare = ws.can_prepare(request)

    if not can_prepare.ok:
        rs = web.Response(status=400)
        rs.force_close()
        return rs
    await ws.prepare(request)
    asyncio.create_task(ws_ping_task(ws))
    message_processors = {}
    try:
        async for ws_msg in ws:
            if ws_msg.type == WSMsgType.text:
                msg = json.loads(ws_msg.data)
                message_type = msg['message_type']
                if message_type not in message_processors:
                    processor = message_types_processors.get(message_type)
                    if processor is None:
                        await ws.send_str(json.dumps({"error_type": message_type}))
                        continue
                    else:
                        message_processors[message_type] = processor(request.app['pg_engine'])
                        next(message_processors[message_type])
                        message_processors[message_type].send(ws)
                message_process = message_processors[message_type]
                callback = message_process.send(msg)
                if callback:
                    await callback
            elif ws_msg.type == WSMsgType.error:
                log.info('websocket closed with error')
            elif ws_msg.type == WSMsgType.close:
                log.info('websocket closed normally')
    finally:
        return ws
