import json
import pathlib

import pytest
from flask import Response
from flask.testing import FlaskClient
from werkzeug.utils import cached_property

from SteamRoulette.admin.__main__ import main as admin_main


@pytest.fixture(scope='session')
def admin_app():
    root_dir = pathlib.Path(__file__)
    root_dir = root_dir.parent.parent.parent.parent
    config = root_dir / 'SteamRoulette/config' / 'tests/app.yaml'
    return admin_main(
        args=[
            '-c',
            str(config.absolute()),
        ],
    )


class TestClientResponse(Response):
    @cached_property
    def json(self):
        return json.loads(self.data.decode('utf8'))


class AppFlaskTestClient(FlaskClient):

    def post_json(self, url, *args, data, **kwargs) -> TestClientResponse:
        return self.post(url, *args, data=json.dumps(data), content_type='application/json', **kwargs)

    def post(self, *args, **kwargs) -> TestClientResponse:
        kwargs.setdefault('headers', {}).setdefault('X-REQUESTED-WITH', 'xmlhttprequest')
        return super().post(*args, **kwargs)


@pytest.fixture
def test_admin_client(
        admin_app,
        # db_session
):
    return AppFlaskTestClient(
        admin_app,
        use_cookies=True,
        response_wrapper=TestClientResponse
    )


@pytest.fixture
def admin_ctx(admin_app):
    with admin_app.app_context():
        yield
