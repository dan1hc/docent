__all__ = (
    'ComponentType',
    'ContentType',
    'DataType',
    'TypeFormat',
    )

import enum


class DataType(enum.Enum):  # noqa

    array   = 'array'
    boolean = 'boolean'
    integer = 'integer'
    number  = 'number'
    object  = 'object'
    string  = 'string'


class TypeFormat(enum.Enum):  # noqa

    binary    = 'binary'
    byte      = 'byte'
    double    = 'double'
    date      = 'date'
    date_time = 'date-time'
    float     = 'float'
    int32     = 'int32'
    int64     = 'int64'
    password  = 'password'


class ContentType(enum.Enum):  # noqa

    html = 'text/html'
    icon = 'image/x-icon'
    json = 'application/json'
    text = 'text/plain'
    yaml = 'text/yaml'


class ComponentType(enum.Enum):  # noqa

    schemas         = 'schemas'
    parameters      = 'parameters'
    securitySchemes = 'securitySchemes'
    requestBodies   = 'requestBodies'
    responses       = 'responses'
    headers         = 'headers'
    examples        = 'examples'
    links           = 'links'
    callbacks       = 'callbacks'
