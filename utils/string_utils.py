import random
import string

_ALPHABET = string.ascii_letters + string.digits
_SYSTEM_RANDOM = random.SystemRandom()


def random_string(slen: int = 5) -> str:
    """Generates a random string for a room name"""
    return "".join(_SYSTEM_RANDOM.choices(_ALPHABET, k=slen))
