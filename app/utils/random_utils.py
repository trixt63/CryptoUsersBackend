import random
import string


def generate_random_string(length):
    letters = string.ascii_letters + string.digits  # Include both letters and digits
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string


def generate_random_number(lower, upper):
    return random.randint(lower, upper)
