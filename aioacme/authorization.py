from datetime import datetime
import enum
from typing import Any, List, Optional

import attr

from .identifier import Identifier
from .validation import OptionalKey
from . import challenge
from . import identifier
from . import validation


class AuthorizationStatus(enum.Enum):
    PENDING = object()
    VALID = object()
    INVALID = object()
    DEACTIVATED = object()
    EXPIRED = object()
    REVOKED = object()

    def __repr__(self):
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def from_json(json_) -> 'AuthorizationStatus':
        validation.type_check(json_, str)
        if json_ == 'pending':
            return AuthorizationStatus.PENDING
        elif json_ == 'valid':
            return AuthorizationStatus.VALID
        elif json_ == 'invalid':
            return AuthorizationStatus.INVALID
        elif json_ == 'deactivated':
            return AuthorizationStatus.DEACTIVATED
        elif json_ == 'expired':
            return AuthorizationStatus.EXPIRED
        elif json_ == 'revoked':
            return AuthorizationStatus.REVOKED
        else:
            raise validation.ValidationError(
                f'Got unknown value {json_!r} for an AuthorizationStatus.'
            )


@attr.s
class Authorization:
    identifier: Identifier = attr.ib()
    status: AuthorizationStatus = attr.ib()
    expires: Optional[datetime] = attr.ib()
    challenges: List[Any] = attr.ib()
    wildcard: bool = attr.ib()


def wildcard_from_json(value):
    validation.type_check(value, bool)
    if value != True:
        raise validation.ValidationError('wildcard field set to false')
    return True


def challenges_from_json(json_):
    return validation.deserialize_list(
        json_,
        challenge.challenge_from_json,
        'challenge',
    )


_AUTHORIZATION_SCHEMA = {
    'identifier': identifier.identifier_from_json,
    'status': AuthorizationStatus.from_json,
    OptionalKey('expires'): validation.datetime_from_json,
    'challenges': challenges_from_json,
    OptionalKey('wildcard'): wildcard_from_json,
}


def authorization_from_json(json_):

    def _make_authorization(**validated_json):
        if validated_json['wildcard'] is None:
            validated_json['wildcard'] = False
        return Authorization(**validated_json)

    return validation.deserialize_dict(
        json_,
        _AUTHORIZATION_SCHEMA,
        _make_authorization,
        'Authorization',
    )
