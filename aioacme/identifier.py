from . import validation


class Identifier:
    pass


class DnsName(Identifier):
    __slots__ = ('domain_name',)

    def __init__(self, domain_name: str) -> None:
        self.domain_name = domain_name

    def __repr__(self):
        return f'{__name__}.{type(self).__name__}({self.domain_name!r})'

    def __hash__(self):
        return hash(self.domain_name)

    def __eq__(self, other):
        if not isinstance(other, DnsName):
            return NotImplemented
        return self.dns_name == other.dns_name

    def __ne__(self, other):
        return not (self == other)

    def to_json(self):
        return {'type': 'dns', 'value': self.domain_name}


class UnknownIdentifier(Identifier):
    def __init__(self, type_: str, value):
        self.type = type_
        self.value = value


def identifier_from_json(json_):
    validation.type_check(json_, dict)
    validation.require_key(json_, 'type', 'Identifier')
    identifier_type = json_['type']
    try:
        validation.type_check(identifier_type, str)
    except validation.ValidationError as err:
        raise validation.ValidationError(
            'Failed to deserialize field "type" while parsing Identifier'
            ' object.'
        ) from err

    if identifier_type == 'dns':
        validation.require_key(json_, 'value', 'Identifier')
        value = json_['value']
        try:
            validation.type_check(value, str)
        except validation.ValidationError as err:
            raise validation.ValidationError(
                'Failed to deserialize field "value" while parsing Identifier'
                ' object.'
            ) from err
        return DnsName(value)
    else:
        validation.require_key(json_, 'value', 'Identifier')
        value = json_['value']
        return UnknownIdentifier(identifier_type, value)
