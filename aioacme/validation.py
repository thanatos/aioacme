from datetime import datetime

import iso8601
from yarl import URL


class OptionalKey:
    def __init__(self, field_name: str) -> None:
        self.field_name = field_name


def deserialize_dict(
        dct,
        schema,
        deserializer,
        obj_type_name: str,
):
    """
    Validate dct according to schema, convert to an object by calling
    ``ctor(**<validated args>)`` if validation succeeds.

    ``obj_type_name`` is used for debugging purposes.
    """
    validated = {}
    extra = {}

    type_check(dct, dict)

    for key, value_deserializer in schema.items():
        if isinstance(key, OptionalKey):
            field_name = key.field_name
            if key.field_name in dct:
                value = dct[key.field_name]
            else:
                validated[key.field_name] = None
                continue
        else:
            field_name = key
            require_key(dct, key, obj_type_name)
            value = dct[key]

        try:
            value = value_deserializer(value)
        except Exception as err:
            raise ValidationError(
                f'Failed to deserialize field "{field_name}" while parsing'
                f' {obj_type_name} object.'
            ) from err
        validated[field_name] = value

    return deserializer(**validated)


class ValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def type_check(value, type_) -> None:
    if not isinstance(value, type_):
        raise ValidationError(f'Expected a {type_}, but got {value!r}')


def deserialize_list(lst, item_deserializer, item_name: str):
    type_check(lst, list)
    items = []
    for idx, item in enumerate(lst):
        try:
            items.append(item_deserializer(item))
        except ValidationError as err:
            raise ValidationError(
                f'Error parsing {item_name} in list at index {idx}.'
            ) from err

    return items


def require_key(dct, key, obj_type_name: str) -> None:
    if key not in dct:
        raise ValidationError(
            f'Failed to find required field "{key}" while parsing'
            f' {obj_type_name} object.'
        )


def datetime_from_json(json_) -> datetime:
    type_check(json_, str)
    return iso8601.parse_date(json_)


def url_from_json(json_) -> URL:
    type_check(json_, str)
    return URL(json_)


def is_string(json_) -> str:
    type_check(json_, str)
    return json_
