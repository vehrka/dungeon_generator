import random
import string


def random_string(self, lenght=5):
    """Generates a random string for a room name"""
    return "".join(
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(lenght)
    )
