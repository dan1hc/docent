__all__ = (
    'DefaultHeaders',
    'DefaultHeaderValues',
    )

import enum

from . import component


class DefaultHeaders(enum.Enum):  # noqa

    accessControlAllowCredentials = 'Access-Control-Allow-Credentials'
    accessControlAllowHeaders     = 'Access-Control-Allow-Headers'
    accessControlMaxAge           = 'Access-Control-Max-Age'
    accessControlAllowMethods     = 'Access-Control-Allow-Methods'
    accessControlAllowOrigin      = 'Access-Control-Allow-Origin'
    connection                    = 'Connection'
    contentLength                 = 'Content-Length'
    contentType                   = 'Content-Type'
    date                          = 'Date'


class DefaultHeaderValues(enum.Enum):  # noqa

    accessControlAllowCredentials = True
    accessControlAllowHeaders     = '*'
    accessControlMaxAge           = 86400
    accessControlAllowMethods     = '*'
    accessControlAllowOrigin      = '*'
    connection                    = 'close'
    contentLength                 = '*'
    contentType                   = component.ContentType.json.value
    date                          = "'%Y-%m-%dT%H:%M:%S.%f%z'"
