import glob
import json
import logging
import os

import yaml


logger = logging.getLogger(__name__)
_STATIC_CONFIG = {}
_STATIC_PREFIX = '/static/'


def _deep_replace(target: dict, source: dict):
    for key in source:
        if key not in target:
            continue
        if isinstance(source[key], dict) and isinstance(target[key], dict):
            _deep_replace(target[key], source[key])
        else:
            target[key] = source[key]


def get_config(config_path, secrets_path=None):
    with open(config_path, 'rt', encoding='UTF-8') as config_file:
        config = yaml.safe_load(config_file)
        if secrets_path:
            with open(secrets_path, 'rt', encoding='UTF-8') as secrets_file:
                secrets = yaml.safe_load(secrets_file)
                _deep_replace(config, secrets)
        return config


def get_static_filename(filename):
    filename = _STATIC_CONFIG.get(filename) or filename
    if filename.startswith(_STATIC_PREFIX):
        return filename[len(_STATIC_PREFIX):]
    return filename


def load_static_config(config_path: str):
    if not config_path:
        return logger.error('No static-config argument')

    for filename in glob.glob(os.path.join(config_path, '*.json')):
        try:
            with open(filename, 'r') as f:
                static_manifest = json.load(f)
            for key, value in static_manifest.items():
                file_key = key[len(_STATIC_PREFIX):] if key.startswith(_STATIC_PREFIX) else key
                file_value = value if value.startswith(_STATIC_PREFIX) else _STATIC_PREFIX + value
                _STATIC_CONFIG[file_key] = file_value
        except (TypeError, FileNotFoundError):
            logger.error(f'Static config {filename} not found or error occurred')