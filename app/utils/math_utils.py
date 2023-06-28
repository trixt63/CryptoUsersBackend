def divide(a, b, default=None):
    if b:
        if a == 0:
            return 0
        elif not a:
            return default
        else:
            return a / b
    else:
        return None
