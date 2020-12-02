import asyncio
import json
import logging
from io import BytesIO

import aiohttp


from anticaptchaofficial.antinetworking import antiNetworking
from base64 import b64encode

log = logging.getLogger(__name__)


# TODO: Remove anticaptchaofficial package


class ImageCaptcha(antiNetworking):
    def __init__(self, client_session: aiohttp.ClientSession, captcha_resolve_timeout: int):
        self._session = client_session
        self._captcha_resolve_timeout = captcha_resolve_timeout

    async def get_balance(self):
        result = await self.make_request("getBalance", {"clientKey": self.client_key})
        if result != 0:
            return result["balance"]
        else:
            return -1

    async def solve_and_return_solution(self, img: BytesIO, **kwargs):
        img_str = b64encode(img.read()).decode('ascii')
        task_data = {
            "type": "ImageToTextTask",
            "body": img_str,
            "phrase": self.phrase,
            "case": self.case,
            "numeric": self.numeric,
            "math": self.math,
            "minLength": self.minLength,
            "maxLength": self.maxLength,
        }
        task_data.update(kwargs)
        task_create_result = await self.create_task({
            "clientKey": self.client_key,
            "task": task_data
        })
        if task_create_result == 1:
            self.log("created task with id "+str(self.task_id))
        else:
            self.log("could not create task")
            self.log(self.err_string)
            return 0
        try:
            task_result = await asyncio.wait_for(
                self.wait_for_result(),
                timeout=self._captcha_resolve_timeout
            )
        except asyncio.TimeoutError:
            self.err_string = "task solution expired"
            return 0
        if task_result == 0:
            return 0
        else:
            return task_result["solution"]["text"]

    async def create_task(self, post_data):
        new_task = await self.make_request("createTask", post_data)
        if new_task == 0:
            return 0
        else:
            if new_task["errorId"] == 0:
                self.task_id = new_task["taskId"]
                return 1
            else:
                self.error_code = new_task["errorCode"]
                self.err_string = "API error " + new_task["errorCode"] + ": " + new_task["errorDescription"]
                return 0

    async def wait_for_result(self):
        while True:
            task_check = await self.make_request("getTaskResult", {
                "clientKey": self.client_key,
                "taskId": self.task_id
            })
            if task_check == 0:
                return 0
            else:
                if task_check["errorId"] == 0:
                    if task_check["status"] == "processing":
                        log.info("task is still processing")
                        await asyncio.sleep(1)
                    if task_check["status"] == "ready":
                        log.info("task solved")
                        return task_check
                else:
                    self.error_code = task_check["errorCode"]
                    self.err_string = "API error "+task_check["errorCode"] + ": " + task_check["errorDescription"]
                    log.info(self.err_string)
                    return 0

    async def make_request(self, method, data):
        log.info("making request to "+method)
        try:
            async with self._session.post("https://api.anti-captcha.com/"+method, json=json.dumps(data)) as resp:
                if resp.status_code != 200:
                    log.info("https://api.anti-captcha.com - {}".format(resp.status_code))
                    return 0
                return await resp.json()
        except aiohttp.ClientTimeout:
            self.err_string = "Client timeout"
            return 0
        except aiohttp.ServerTimeoutError:
            self.err_string = "Read timeout"
            return 0
        except aiohttp.ServerConnectionError:
            self.err_string = "Connection refused"
            return 0


class CaptchaService(object):
    def __init__(self, api_key: str, client_session: aiohttp.ClientSession, captcha_resolve_timeout=60):
        self._session = client_session
        self.captcha_resolve_timeout = captcha_resolve_timeout
        self._api_key = api_key
        self._closed = False

    def make_captcha_solver(self):
        solver = ImageCaptcha(self._session, self.captcha_resolve_timeout)
        solver.set_verbose(1)
        solver.set_key(self._api_key)
        return solver

    async def solve(self, image: BytesIO):
        if self._closed:
            raise Exception("Captcha service session is closed")
        solver = self.make_captcha_solver()
        captcha_text = await solver.solve_and_return_solution(image)
        if captcha_text != 0:
            log.info("captcha text " + captcha_text)
            return captcha_text
        else:
            log.info("task finished with error " + solver.error_code)

    async def close(self):
        self._closed = True
        return await self._session.close()
