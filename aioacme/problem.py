from typing import Optional

import attr

from .errors import UnknownAcmeError
from .validation import OptionalKey
from . import validation


class ProblemBase(Exception):
    pass


@attr.s
class Problem(ProblemBase):
    type: str = attr.ib()
    title: Optional[str] = attr.ib()
    status: Optional[int] = attr.ib()
    detail: Optional[str] = attr.ib()
    instance: Optional[str] = attr.ib()


# TODO: I feel like we should derive subclasses for the ACME specific errors,
# to allow easy `try: ... except <error>:`.
class AcmeProblem(ProblemBase):
    pass


_PROBLEM_BASE_SCHEMA = {
    OptionalKey('type'): str,
    OptionalKey('title'): str,
    OptionalKey('status'): int,
    OptionalKey('detail'): str,
    OptionalKey('instance'): str,
}


def from_json(json_):
    validated_base = validation.deserialize_dict(
        json_,
        _PROBLEM_BASE_SCHEMA,
        lambda **dct: dct,
        'Problem',
    )

    if validated_base['type'] is None:
        validated_base['type'] = 'about:blank'
    return Problem(**validated_base)
