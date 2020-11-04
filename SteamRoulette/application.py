from flask import Flask, url_for

from SteamRoulette.config import get_static_filename
from SteamRoulette.service.db import db


def create_app(config, app_name=__name__):
    app = Flask(app_name)
    db.init_app(app)
    return app


def setup_common_jinja_env(env, debug=False):
    """Setups common stuff for flask's and celery's jinja2 envs"""
    env.autoescape = True
    # env.add_extension('jinja2.ext.do')
    # env.add_extension('jinja2.ext.i18n')
    env.globals.update({
        'url_for_static': lambda filename: url_for('static', filename=get_static_filename(filename)),
    })
