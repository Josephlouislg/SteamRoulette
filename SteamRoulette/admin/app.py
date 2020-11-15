from SteamRoulette import admin
from SteamRoulette.application import create_raw_app, setup_common_jinja_env


def create_admin_app(config):
    app = create_raw_app(config)
    app.config_from_dict(config['flask'])
    for bp in admin.BLUEPRINTS:
        url_prefix = '/admin' + (bp.url_prefix or '')
        app.register_blueprint(bp, url_prefix=url_prefix)
    setup_common_jinja_env(app.jinja_env, debug=config['debug'])
    app.jinja_env.globals.update({})
    return app
