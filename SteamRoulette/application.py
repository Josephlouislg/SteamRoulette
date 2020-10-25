from flask import Flask


def create_app(config, app_name=__name__):
    app = Flask(app_name)
    return app
