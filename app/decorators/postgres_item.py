from functools import wraps


def postgres_items_to_json(wrapped):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            items = f(*args, **kwargs)
            return items_to_json(items)

        return decorated_function

    return decorator(wrapped)


def items_to_json(items):
    data = []
    for item in items:
        data.append(item_to_json(item))
    return data


def item_to_json(item):
    data = {}
    for key in item.keys():
        data[key] = item[key]
    return data
