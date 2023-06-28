import re

from sanic_testing.testing import TestingResponse

from app.utils.logger_utils import get_logger

logger = get_logger('Common Utils')


def assert_success_response(response: TestingResponse):
    assert response.status == 200
    assert response.content_type == "application/json"
    assert response.json

    return response.json


def split_config(params: dict):
    names = list(params.keys())
    values = list(params.values())
    return names, values


def param_with_config(config, key):
    if key.startswith('$'):
        try:
            name = re.search('\$\{(.*)}', key)
            config_key = name.group(1)
            if config_key:
                key = config_key.split('.')
                return config.get(*key)
        except Exception as ex:
            logger.exception(ex)

    return key
