import logging
import re
import string
from urllib import parse

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    normalized_name = ""
    for c in name:
        # if c is uppercase or digit, add a space before it
        if c in string.ascii_uppercase + string.digits:
            normalized_name += " " + c
        # if c is not a letter or digit, replace it with a space
        elif c not in string.ascii_letters + string.digits:
            normalized_name += " "
        else:
            normalized_name += c

    # remove leading and trailing spaces
    normalized_name = re.sub(r"\s+", " ", normalized_name).strip()

    return normalized_name


def validate_name(name: str) -> bool:
    if name != normalize_name(name):
        return False
    return True


def normalize_path(path: str) -> str:
    normalized_path = path.lower()
    normalized_path = normalized_path.replace(" ", "-")
    normalized_path = parse.quote(normalized_path)
    if not normalized_path.startswith('/'):
        normalized_path = '/' + normalized_path

    return normalized_path


def validate_path(path: str) -> bool:
    if path != normalize_path(path):
        return False
    return True
