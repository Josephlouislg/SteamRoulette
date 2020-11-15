import pytest
from SteamRoulette.config import init_config as _init_config, _CONFIG


pytest_plugins = [
    'SteamRoulette.tests.fixtures.db_fixtures',
    # 'tests.fixtures.util_fixtures'
]


def pytest_configure(config):
    # More obvious option here would be to use
    # pytest.fixture(autouse=True, scope='session')
    # but all fixtures run after tests are discovered,
    # and some modules that we are testing (esp. forms)
    # require that config is initialized on import time
    _init_config({
        'country': 'UA',
        'timezone': 'Europe/Kiev',
        'testing': {
            'unsafe_superlogin': False
        }
    })


@pytest.yield_fixture
def set_config():
    current = _CONFIG.copy()

    def setter(key, value):
        c = _CONFIG
        *heads, tail = key.split('.')
        for head in heads:
            c = c.setdefault(head, {})
        c[tail] = value

    yield setter

    _CONFIG.clear()
    _CONFIG.update(current)


def pytest_collection_modifyitems(items, config):
    """Skips tests that use fixtures provided in the `--skip-fixture` commandline arguments"""
    selected_items = []
    deselected_items = []

    # if config.option.skipped_fixtures:
    #     for item in items:
    #         fixtures = getattr(item, 'fixturenames', ())
    #         if any(f in fixtures for f in config.option.skipped_fixtures):
    #             deselected_items.append(item)
    #         else:
    #             selected_items.append(item)
    #     config.hook.pytest_deselected(items=deselected_items)
    #     items[:] = selected_items
