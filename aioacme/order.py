from datetime import datetime
import enum
from typing import List, Optional

from .util import rename_key
from .identifier import Identifier
from .validation import OptionalKey
from . import identifier
from . import problem
from . import validation

import attr
from yarl import URL


class OrderStatus(enum.Enum):
    INVALID = object()
    PENDING = object()
    READY = object()
    PROCESSING = object()
    VALID = object()

    def __repr__(self):
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def from_json(json_) -> 'OrderStatus':
        validation.type_check(json_, str)
        if json_ == 'invalid':
            return OrderStatus.INVALID
        elif json_ == 'pending':
            return OrderStatus.PENDING
        elif json_ == 'ready':
            return OrderStatus.READY
        elif json_ == 'processing':
            return OrderStatus.PROCESSING
        elif json_ == 'valid':
            return OrderStatus.VALID
        else:
            raise validation.ValidationError(
                f'Got unknown value {json_!r} for an OrderStatus.'
            )


def authorizations_from_json(json_) -> List[URL]:

    def authorization_from_json(json_):
        validation.type_check(json_, str)
        return URL(json_)

    return validation.deserialize_list(
        json_,
        authorization_from_json,
        'authorization',
    )


def identifiers_from_json(json_) -> List[Identifier]:
    return validation.deserialize_list(
        json_,
        identifier.identifier_from_json,
        'identifier',
    )


_ORDER_SCHEMA = {
    'status': OrderStatus.from_json,
    OptionalKey('expires'): validation.datetime_from_json,
    'identifiers': identifiers_from_json,
    OptionalKey('not_before'): validation.datetime_from_json,
    OptionalKey('not_after'): validation.datetime_from_json,
    OptionalKey('error'): problem.from_json,
    'authorizations': authorizations_from_json,
    'finalize': validation.url_from_json,
    OptionalKey('certificate'): validation.url_from_json,
}


@attr.s
class Order:
    status: OrderStatus = attr.ib()
    expires: Optional[datetime] = attr.ib()
    identifiers: List[Identifier] = attr.ib()
    not_before: Optional[datetime] = attr.ib()
    not_after: Optional[datetime] = attr.ib()
    error: Optional[problem.Problem] = attr.ib()
    authorization_urls: List[URL] = attr.ib()
    finalize_url: URL = attr.ib()
    certificate_url: Optional[URL] = attr.ib()

    async def finalize(self):
        pass

    @staticmethod
    def from_json(json_) -> 'Order':

        def _make_order(**validated_json) -> Order:
            rename_key(validated_json, 'finalize', 'finalize_url')
            rename_key(validated_json, 'certificate', 'certificate_url')
            rename_key(validated_json, 'authorizations', 'authorization_urls')
            return Order(**validated_json)

        return validation.deserialize_dict(
            json_,
            _ORDER_SCHEMA,
            _make_order,
            'Order',
        )
