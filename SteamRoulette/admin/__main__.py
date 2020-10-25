import argparse

from SteamRoulette import admin
from SteamRoulette.application import create_app
from SteamRoulette.config import get_config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--host", default='0.0.0.0')
    ap.add_argument("--config", default='./SteamRoulette/config/app.yaml')
    ap.add_argument("--secrets", default=None)
    ap.add_argument("--debug", default=False)
    args = ap.parse_args()
    config = get_config(args.config, args.secrets)
    app = create_app(
        config=config,
        app_name='admin',
    )
    for bp in admin.BLUEPRINTS:
        url_prefix = '/admin' + (bp.url_prefix or '')
        app.register_blueprint(bp, url_prefix=url_prefix)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
