import hashlib

KEY = 'dev-123'


def hash_id(ids):
    string = ':'.join(ids)
    return hashlib.sha256(f'{string}:{KEY}'.encode()).hexdigest()
