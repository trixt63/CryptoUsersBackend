from app.utils.logger_utils import get_logger

logger = get_logger('Parser')


def get_connection_elements(string):
    """
    example output for exporter_type: exporter_type@username:password@connection_url

    :param string:
    :return: username, password, connection_url
    """
    try:
        elements = string.split("@")
        auth = elements[1].split(":")
        username = auth[0]
        password = auth[1]
        connection_url = elements[2]
        return username, password, connection_url
    except Exception as e:
        logger.warning(f"get_connection_elements err {e}")
        return None, None, None


def get_redis_connection_elements(string: str):
    try:
        connection = string.split('://')[-1]
        elements = connection.split('@')
        if len(elements) > 1:
            username, password = elements[0].split(':')
            url = elements[1]
        else:
            username, password = None, None
            url = elements[0]

        url_elements = url.split('/')
        db = url_elements[1] if len(url_elements) > 1 else 0
        host, port = url_elements[0].split(':')
        return {
            'username': username,
            'password': password,
            'host': host,
            'port': int(port),
            'db': int(db)
        }
    except Exception as ex:
        logger.warning(f'Parse REDIS_URL {string} error: {ex}')
        return {
            'username': None,
            'password': None,
            'host': 'localhost',
            'port': 6379,
            'db': 0
        }


def parse_pagination(page_index: int, page_size: int):
    skip = (page_index - 1) * page_size
    limit = page_size
    return skip, limit
