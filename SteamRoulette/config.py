import yaml


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
