import re


def short_address(address: str, n_start=3, n_end=4):
    if not address:
        return ''
    return address[:n_start + 2] + '...' + address[-n_end:]


def pretty_tx_method(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1 \2', name)
    return name[:1].upper() + name[1:]


def about(value, _min=0, _max=1000):
    if value < _min:
        value = _min
    elif value > _max:
        value = _max
    return value
