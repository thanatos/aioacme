from datetime import datetime
import enum
from typing import Optional

import attr
from yarl import URL

from .validation import OptionalKey
from . import problem
from . import util
from . import validation


class ChallengeStatus(enum.Enum):
    PENDING = object()
    PROCESSING = object()
    VALID = object()
    INVALID = object()

    def __repr__(self):
        return f'{__name__}.{type(self).__name__}.{self.name}'

    @staticmethod
    def from_json(json_) -> 'ChallengeStatus':
        validation.type_check(json_, str)
        if json_ == 'pending':
            return ChallengeStatus.PENDING
        elif json_ == 'processing':
            return ChallengeStatus.PROCESSING
        elif json_ == 'valid':
            return ChallengeStatus.VALID
        elif json_ == 'invalid':
            return ChallengeStatus.INVALID
        else:
            raise validation.ValidationError(
                f'Got unknown value {json_!r} for a ChallengeStatus.'
            )


@attr.s
class Challenge:
    type: str = attr.ib()
    url: URL = attr.ib()
    status: ChallengeStatus = attr.ib()
    validated: Optional[datetime] = attr.ib()
    error: Optional[problem.Problem] = attr.ib()


@attr.s
class Http01Challenge(Challenge):
    token: str = attr.ib()

    def sign(self, private_key):
        thumbprint = private_key.thumbprint()
        return f'{self.token}.{util.acme_b64encode(thumbprint)}'


@attr.s
class Dns01Challenge(Challenge):
    token = attr.ib()


@attr.s
class TlsAlpn01Challenge(Challenge):
    token = attr.ib()


@attr.s
class UnknownChallenge(Challenge):
    extra_json = attr.ib()


def token_from_json(json_) -> str:
    return validation.type_check(json_, str)


_CHALLENGE_BASE_SCHEMA = {
    'type': validation.is_string,
    'url': validation.url_from_json,
    'status': ChallengeStatus.from_json,
    OptionalKey('validated'): validation.datetime_from_json,
    OptionalKey('error'): problem.from_json,
}
_HTTP_01_SCHEMA = {
    'token': validation.is_string,
}
_DNS_01_SCHEMA = {
    'token': validation.is_string,
}
_TLS_ALPN_01_SCHEMA = {
    'token': validation.is_string,
}


def challenge_from_json(json_) -> Challenge:
    validated_base = validation.deserialize_dict(
        json_,
        _CHALLENGE_BASE_SCHEMA,
        lambda **dct: dct,
        'Challenge',
    )

    challenge_type: str = validated_base['type']
    if challenge_type == 'http-01':
        return validation.deserialize_dict(
            json_,
            _HTTP_01_SCHEMA,
            lambda **dct: Http01Challenge(**validated_base, **dct),
            'Http01Challenge',
        )
    elif challenge_type == 'dns-01':
        return validation.deserialize_dict(
            json_,
            _DNS_01_SCHEMA,
            lambda **dct: Dns01Challenge(**validated_base, **dct),
            'Dns01Challenge',
        )
    elif challenge_type == 'tls-alpn-01':
        return validation.deserialize_dict(
            json_,
            _TLS_ALPN_01_SCHEMA,
            lambda **dct: TlsAlpn01Challenge(**validated_base, **dct),
            'TlsAlpn01Challenge',
        )
    else:
        for key in _CHALLENGE_BASE_SCHEMA:
            field_name = \
                key.field_name if isinstance(key, OptionalKey) else key
            delete_if_exists(json_, field_name)
        return UnknownChallenge(extra_json=json_, **validated_base)


def delete_if_exists(dct, key):
    if key in dct:
        del dct[key]
