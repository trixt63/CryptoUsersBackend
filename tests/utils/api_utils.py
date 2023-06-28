import time

from prettytable import PrettyTable
import requests
from urllib.parse import urlencode

from app import log
from app.utils.logger_utils import get_logger
from app.utils.time_utils import human_readable_time
from tests.parameters import config
from tests.utils.common_utils import param_with_config

logger = get_logger('API Utils')


def call_api(base_url, path, method, test_cases):
    latency = []
    for test_case in test_cases:
        params = handler_params(test_case)

        url_path = path
        if params.get('path'):
            url_path = url_path.format(**params['path'])

        if params.get('query'):
            url_path += f'?{urlencode(params["query"])}'

        url = f'{base_url}{url_path}'
        kwargs = {}
        if params.get('body'):
            kwargs['json'] = params['body']

        try:
            response = requests.request(method=method, url=url, **kwargs)
            if 200 <= response.status_code < 300:
                latency_ = float(response.headers['latency'])
                latency.append(latency_)
                log(f'Success with {url_path} - {latency_}s', keyword='INFO')
            else:
                log(f'Fail with {url_path}', keyword='ERROR')
        except Exception as ex:
            logger.warning(ex)

    avg_latency = round(sum(latency) / len(latency), 3) if latency else None
    number_of_success = len(latency)
    return avg_latency, number_of_success


def create_report(data):
    cases = data['cases']
    cols = ['path', 'latency', 'success', 'fail']
    tables = [cols]
    for case in cases:
        try:
            row = []
            for col in cols:
                row.append(case[col])
        except KeyError:
            logger.exception(f'Missing value of column in path {case.get("path")}')
            continue

        tables.append(row)

    timestamp = int(time.time())

    report = ''
    report += 'API Performance Report \n'
    report += '-- \n'
    report += f'Base URL: {data["base_url"]} \n'
    report += f'Time: {human_readable_time(timestamp)} \n'
    report += '-' * 100 + '\n'
    report += f'Number of SUCCESS: {data["success"]} \n'
    report += f'Number of FAIL: {data["fail"]} \n'
    report += '-' * 100 + '\n'
    report += f'Blocked: {data["blocked"]} \n'
    report += f'Slow: {data["slow"]} \n'

    tab = PrettyTable(tables[0])
    tab.add_rows(tables[1:])
    report += str(tab)
    print(report)

    with open(f'tests/logs/api_performance_report_{timestamp}.txt', 'w') as f:
        f.write(report)


def handler_params(params):
    allowable_key = ['query', 'path', 'body']
    url_params = {}
    for url_param_location in allowable_key:
        params_ = params.get(url_param_location, {})
        url_params[url_param_location] = handler_params_(params_)

    return url_params


def handler_params_(value):
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if k.startswith('_'):
                continue
            result[k] = handler_params_(v)
    elif isinstance(value, list):
        result = []
        for v in value:
            result.append(handler_params_(v))
    else:
        result = param_with_config(config, value)

    return result
