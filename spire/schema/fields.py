import re

from sqlalchemy import Column, ForeignKey as _ForeignKey, types
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator

from spire.util import uniqid

__all__ = ('Boolean', 'Date', 'DateTime', 'Decimal', 'Email', 'Enumeration', 'Float',
    'ForeignKey', 'Identifier', 'Integer', 'Text', 'Time', 'UUID')

class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, MutableDict):
            return value
        elif isinstance(value, dict):
            return MutableDict(value)
        else:
            return Mutable.coerce(key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()

class ValidatesMinMax(object):
    def validate(self, instance, column, value):
        minimum = self.minimum
        if minimum is not None and value < minimum:
            raise ValueError()

        maximum = self.maximum
        if maximum is not None and value > maximum:
            raise ValueError()

class DateType(TypeDecorator, ValidatesMinMax):
    impl = types.Date

    def __init__(self, minimum=None, maximum=None):
        super(DateType, self).__init__()
        self.minimum = minimum
        self.maximum = maximum

class DateTimeType(TypeDecorator, ValidatesMinMax):
    impl = types.DateTime

    def __init__(self, minimum=None, maximum=None, timezone=None):
        super(DateTimeType, self).__init__(timezone=timezone)
        self.minimum = minimum
        self.maximum = maximum

class DecimalType(TypeDecorator, ValidatesMinMax):
    impl = types.Numeric

    def __init__(self, minimum=None, maximum=None, precision=None, scale=None):
        super(DecimalType, self).__init__(precision=precision, scale=scale)
        self.minimum = minimum
        self.maximum = maximum

class EnumerationType(TypeDecorator):
    impl = types.Text

    def __init__(self, enumeration):
        super(EnumerationType, self).__init__()
        if isinstance(enumeration, basestring):
            enumeration = enumeration.split(' ')
        self.enumeration = enumeration

    def validate(self, instance, column, value):
        if value in self.enumeration:
            return value
        else:
            raise ValueError()

class FloatType(TypeDecorator, ValidatesMinMax):
    impl = types.Float

    def __init__(self, minimum=None, maximum=None):
        super(FloatType, self).__init__()
        self.minimum = minimum
        self.maximum = maximum

class IntegerType(TypeDecorator, ValidatesMinMax):
    impl = types.Integer

    def __init__(self, minimum=None, maximum=None):
        super(IntegerType, self).__init__()
        self.minimum = minimum
        self.maximum = maximum

class TextType(TypeDecorator):
    impl = types.Text
    pattern = None

    def __init__(self, pattern=None, min_length=None, max_length=None):
        super(TextType, self).__init__()
        self.min_length = min_length
        self.max_length = max_length
        if pattern:
            self.pattern = pattern

    def validate(self, instance, column, value):
        if self.pattern and not self.pattern.match(value):
            raise ValueError()

        min_length = self.min_length
        if min_length is not None and len(value) < min_length:
            raise ValueError()

        max_length = self.max_length
        if max_length is not None and len(value) > max_length:
            raise ValueError()

class TimeType(TypeDecorator, ValidatesMinMax):
    impl = types.Time

    def __init__(self, minimum=None, maximum=None):
        super(TimeType, self).__init__()
        self.minimum = minimum
        self.maximum = maximum

class EmailType(TextType):
    pattern = re.compile(
        r"(?i)^([-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        r'|"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"'
        r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}')

class IPAddressType(TextType):
    pattern = re.compile(r'^\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}$')

class TokenType(TextType):
    pattern = re.compile(r'^[_a-z0-9][-_.a-z0-9]*(?<=[_a-z0-9])$')

class UUIDType(TextType):
    pattern = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')

def Boolean(nullable=False, **params):
    return Column(types.Boolean(), nullable=nullable, **params)

def Date(minimum=None, maximum=None, **params):
    return Column(DateType(minimum, maximum), **params)

def DateTime(minimum=None, maximum=None, timezone=None, **params):
    return Column(DateTimeType(minimum, maximum, timezone), **params)

def Decimal(minimum=None, maximum=None, precision=None, scale=None, **params):
    return Column(DecimalType(minimum, maximum, precision, scale), **params)

def Email(**params):
    return Column(EmailType(), **params)

def Enumeration(enumeration, **params):
    return Column(EnumerationType(enumeration), **params)

def Float(minimum=None, maximum=None, **params):
    return Column(FloatType(minimum, maximum), **params)

def ForeignKey(column, **params):
    column_params = {}
    for name in ('default', 'doc', 'index', 'info', 'nullable', 'unique'):
        if name in params:
            column_params[name] = params.pop(name)

    return Column(_ForeignKey(column, **params), **column_params)

def Identifier(**params):
    return Column(UUIDType(), nullable=False, primary_key=True, default=uniqid, **params)

def Integer(minimum=None, maximum=None, **params):
    return Column(IntegerType(minimum, maximum), **params)

def Text(pattern=None, min_length=None, max_length=None, **params):
    return Column(TextType(pattern, min_length, max_length), **params)

def Time(minimum=None, maximum=None, **params):
    return Column(TimeType(minimum, maximum), **params)

def UUID(**params):
    return Column(UUIDType(), **params)