import datetime
import decimal
import re

import docent.core

from . import exceptions


class FrameworkConstants(docent.core.Constants):  # noqa

    BASE_ERROR_CODES: dict[exceptions.BaseRequestError, int] = {
        exceptions.RequestError: 400,
        exceptions.UnexpectedError: 500,
        }
    COMPONENT_TYPE_MAP: dict[str, str]                       = {
        'authorizer': 'securityScheme',
        'requestBody': 'requestBodies',
        }
    DEFAULT_ERROR_CODES: dict[Exception, int]                = {
        ConnectionRefusedError: 401,
        Exception: 500,
        FileExistsError: 400,
        FileNotFoundError: 404,
        ModuleNotFoundError: 405,
        NotImplementedError: 501,
        PermissionError: 403,
        SyntaxError: 400,
        }
    ERROR_CODES: dict[Exception, int]                        = {
        exceptions.MethodNotAllowedError: 405,
        exceptions.MethodNotImplementedError: 501,
        exceptions.NotAuthenticatedError: 401,
        exceptions.NotAuthorizedError: 403,
        exceptions.RequestError: 400,
        exceptions.ResourceLockedError: 429,
        exceptions.ResourceNotFoundError: 404,
        exceptions.UnexpectedError: 500,
        **DEFAULT_ERROR_CODES,
        }
    DEFAULT_ERROR_MAP: dict[Exception, str]                  = {
        ConnectionRefusedError: exceptions.NotAuthenticatedError.__doc__,
        Exception: exceptions.UnexpectedError.__doc__,
        FileExistsError: exceptions.RequestError.__doc__,
        FileNotFoundError: exceptions.ResourceNotFoundError.__doc__,
        ModuleNotFoundError: exceptions.MethodNotAllowedError.__doc__,
        NotImplementedError: exceptions.MethodNotImplementedError.__doc__,
        PermissionError: exceptions.NotAuthorizedError.__doc__,
        SyntaxError: exceptions.RequestError.__doc__,
        }
    EXTENSIONS: set[str]                                     = {
        'AUTHORIZERS',
        'INTEGRATIONS',
        'RESPONSE_HEADERS',
        'REQUEST_HEADERS',
        'ERRORS',
        }
    FIELD_DELIM                                              = '.'
    TAG_DELIM                                                = ':'
    METHOD_SUCCESS_CODES: dict[str, int]                     = {
        'delete': 204,
        'get': 200,
        'get_one': 200,
        'get_many': 200,
        'patch': 200,
        'post': 201,
        'put': 200,
        'put_one': 200,
        'put_many': 200,
        }
    NAMED_COMPONENTS: set[str]                               = {
        'parameter',
        }
    PATH_ID_PARSE_EXPR                                       = re.compile(r'({)\w+(})')
    PATH_ID_GROUP_EXPR                                       = re.compile(r'{(\w+)}')
    REST_TYPES: dict[object, dict[str, str]]                 = {
        bool: {
            'type': 'boolean',
            },
        bytes: {
            'type': 'string',
            'format': 'byte'
            },
        datetime.date: {
            'type':  'string',
            'format': 'date'
            },
        datetime.datetime: {
            'type':  'string',
            'format': 'date-time'
            },
        decimal.Decimal: {
            'type':  'number',
            'format': 'double'
            },
        dict: {
            'type': 'object',
            },
        float: {
            'type': 'number',
            'format': 'float'
            },
        int: {
            'type': 'integer',
            'format': 'int32'
            },
        list: {
            'type': 'array',
            },
        set: {
            'type': 'array',
            },
        str: {
            'type': 'string',
            },
        tuple: {
            'type': 'array',
            },
        }
