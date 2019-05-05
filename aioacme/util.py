import base64
from typing import Dict, Union


def rename_key(
        dct: Dict[object, object],
        key_src: object,
        key_dst: object
) -> None:

    dct[key_dst] = dct[key_src]
    del dct[key_src]


def acme_b64encode(data: bytes) -> str:
    """URL-safe base64 encode, without padding chars."""
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def acme_b64decode(data: str) -> bytes:
    len_mod = len(data) % 4
    if len_mod == 2:
        data += '=='
    elif len_mod == 3:
        data += '='

    return base64.urlsafe_b64decode(data)
