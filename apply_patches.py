import argparse
import os
import pathlib
import re
from datetime import date, datetime, timedelta

import psycopg2

from SteamRoulette.config import load_config, _existing_file, TrafaretValueAction, config_trafaret


app_dir = os.path.join(os.path.dirname(__file__), 'SteamRoulette')


PATCH_PATTERN = re.compile(
    r'^r(?P<year>20[1-9][0-9])_(?P<month>[0-1][0-9])_(?P<day>[0-3][0-9])(?:v(?P<version>[1-9]))?\.sql$'
)

RELEASE_BRANCH_PATTERN = re.compile('^r(?P<year>20[1-9][0-9])_(?P<month>[0-1][0-9])_(?P<day>[0-3][0-9])$')


def get_list_of_patches(last_applied_patch_date, scripts_folder, last_version=0, max_date=None):
    folder = os.path.join(app_dir, scripts_folder)
    res = dict()
    for patch_name in os.listdir(folder):
        match = PATCH_PATTERN.match(patch_name)
        if match:
            groups = match.groupdict()
            date = datetime(int(groups['year']), int(groups['month']), int(groups['day'])).date()
            version = int(groups['version']) if groups['version'] else 0
            if date > last_applied_patch_date or date == last_applied_patch_date and version > last_version:
                if not max_date or date <= max_date:
                    res[(date, version)] = patch_name

    return [
        value
        for key, value in sorted(
            res.items(),
            key=lambda item: datetime.combine(item[0][0], datetime.min.time()) + timedelta(minutes=item[0][1])
        )
    ]


def _get_last_applied_patch(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_patch
        (
          id serial NOT NULL,
          date date NOT NULL,
          version smallint not null,
          CONSTRAINT db_patch_pkey PRIMARY KEY (id)
        );

        CREATE  UNIQUE INDEX IF NOT EXISTS ux__db_patch__date_version
          ON db_patch
          USING btree (date, version);
    """)
    cursor.execute('select date, version from db_patch ORDER BY date desc, version desc limit 1')
    return (cursor.fetchall() or [(date(1970, 1, 1), 0)])[0]


def _apply_patches(patch_names, cursor, scripts_folder):
    for patch_name in patch_names:
        with open(os.path.join(app_dir, scripts_folder, patch_name), 'r') as patch:
            sqls = patch.read().split('--//--')
            for sql in sqls:
                if ';' in sql:
                    try:
                        cursor.execute(sql)
                        cursor.execute("commit;")
                    except Exception:
                        print(sql)
                        raise


def apply_patch(branch_name, cursor, scripts_folder):
    last_patch = _get_last_applied_patch(cursor)
    assert last_patch

    match = RELEASE_BRANCH_PATTERN.match(branch_name)
    max_date = None
    if match:
        groups = match.groupdict()
        max_date = datetime(int(groups['year']), int(groups['month']), int(groups['day'])).date()

    _apply_patches(
        get_list_of_patches(last_patch[0], scripts_folder, last_patch[1], max_date),
        cursor,
        scripts_folder
    )


def make_parser(config_trafaret, default_config='config.yaml', root_dir=None):
    if not root_dir:
        root_dir = pathlib.Path(__file__)
        root_dir = root_dir.parent.parent

    ap = argparse.ArgumentParser(fromfile_prefix_chars='@')
    ap.add_argument('-c', '--config', type=_existing_file, metavar='PATH',
                    default=root_dir / 'config' / default_config,
                    help="Path to config file (default: `%(default)s`)")
    ap.add_argument('-s', '--secrets', type=pathlib.Path, metavar='PATH',
                    default=None, help="Path to file with secrets")
    ap.add_argument('-D', dest="config_defaults", metavar="VARNAME=VALUE",
                    action=TrafaretValueAction, trafaret=config_trafaret,
                    help="Config overrides")
    ap.add_argument('-b', '--branch', default='master',
                    help="Logger level")
    ap.add_argument('-l', '--log', default='INFO',
                    help="Logger level")
    return ap


if __name__ == "__main__":
    ap = make_parser(config_trafaret)
    options = ap.parse_args()
    config = load_config(
        options.config,
        options.secrets,
        options.config_defaults
    )

    from urllib.parse import urlparse

    dsn = config['postgres']['dsn']
    result = urlparse(dsn)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    connection = psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=hostname,
        port=port,
    )
    apply_patch(
        options.branch,
        cursor=connection.cursor(),
        scripts_folder='db_patch/postgres',
    )
