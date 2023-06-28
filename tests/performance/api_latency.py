import json

from app import log
from app.utils.logger_utils import get_logger
from tests.utils.api_utils import call_api, create_report

logger = get_logger('Test API latency')


def api_latency(base_url):
    logger.info(f'Testing with {base_url}')
    with open('tests/.config/parameters.json') as f:
        cases = json.load(f)
    logger.info(f'There are {len(cases)} path')

    print('-' * 100)

    result = []
    number_of_blocked = 0
    number_of_slow = 0
    for case in cases:
        method = case.get('method', 'GET')
        path = case['path']

        test_cases = case['testcases']
        avg_latency, number_of_success = call_api(base_url, path, method, test_cases)
        number_of_fails = len(test_cases) - number_of_success

        result.append({'path': path, 'latency': avg_latency, 'success': number_of_success, 'fail': number_of_fails})

        if (avg_latency is None) or (avg_latency > 5) or number_of_fails:
            log_level = 'ERROR'
            number_of_blocked += 1
        elif avg_latency > 1:
            log_level = 'WARN'
            number_of_slow += 1
        else:
            log_level = 'INFO'
        log(f'Path {path} - avg {round(avg_latency or 0, 3)}s - SUCCESS {number_of_success} - FAIL {number_of_fails}', keyword=log_level)
        print('-' * 100)

    total_number_of_success = sum([x['success'] for x in result])
    total_number_of_fails = sum([x['fail'] for x in result])
    data = {
        'base_url': base_url,
        'success': total_number_of_success,
        'fail': total_number_of_fails,
        'blocked': number_of_blocked,
        'slow': number_of_slow,
        'cases': result
    }
    create_report(data)
