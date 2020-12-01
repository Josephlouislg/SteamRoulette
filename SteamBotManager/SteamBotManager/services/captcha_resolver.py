import logging
from io import BytesIO

from anticaptchaofficial.imagecaptcha import imagecaptcha


from anticaptchaofficial.antinetworking import *
from base64 import b64encode

log = logging.getLogger(__name__)


class ImageCaptcha(antiNetworking):

    def solve_and_return_solution(self, img: BytesIO, **kwargs):  # TODO: make async
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
        if self.create_task({
            "clientKey": self.client_key,
            "task": task_data
        }) == 1:
            self.log("created task with id "+str(self.task_id))
        else:
            self.log("could not create task")
            self.log(self.err_string)
            return 0

        task_result = self.wait_for_result(60)  # TODO: make await
        if task_result == 0:
            return 0
        else:
            return task_result["solution"]["text"]


class CaptchaService(object):
    def __init__(self, api_key):
        self._solver = ImageCaptcha()
        self._solver.set_verbose(1)
        self._solver.set_key(api_key)

    def solve(self, image: BytesIO):
        captcha_text = self._solver.solve_and_return_solution(image)
        if captcha_text != 0:
            log.info("captcha text " + captcha_text)
            return captcha_text
        else:
            log.info("task finished with error " + self._solver.error_code)
