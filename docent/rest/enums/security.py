__all__ = (
    'HttpScheme',
    'SecuritySchemes',
    )

import enum


class SecurityScheme(enum.Enum):  # noqa

    http          = 'http'
    apiKey        = 'apiKey'
    oauth2        = 'oauth2'
    openIdConnect = 'openIdConnect'


class HttpScheme(enum.Enum):  # noqa

    basic  = 'basic'
    bearer = 'bearer'
