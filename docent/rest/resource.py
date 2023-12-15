__all__ = (
    'Resource',
    )

import dataclasses
import functools
import re
import typing

import docent.core

from . import constants
from . import enums
from . import exceptions
from . import objects
from . import utils


class Constants(constants.FrameworkConstants):  # noqa

    AUTHORIZERS: list[objects.security.Authorizer] = list
    ERRORS: list[Exception]                        = list
    INTEGRATIONS: list[objects.base.Component]     = list
    REQUEST_HEADERS: objects.parameter.Parameters  = objects.parameter.Parameters  # noqa
    RESPONSE_HEADERS: objects.response.Headers     = objects.response.Headers  # noqa


def _prepare_method(
    cls: 'Resource',
    method_name: str,
    event_handler_function: typing.Callable[
        ['objects.request.Request'],
        typing.Union[
            docent.core.objects.DocObject,
            list[docent.core.objects.DocObject],
            None
            ]
        ],
    id_in_path: bool = True,
    **kwargs,
    ):

    extensions: dict[
        str,
        typing.Union[
            list,
            objects.response.Headers,
            objects.parameter.Parameters
            ]
        ] = {
            ext_lower: (
                method_ext + rsc_extension
                if (rsc_extension := getattr(cls, ext))
                else method_ext
                )
            for ext
            in Constants.EXTENSIONS
            if (
                method_ext := (
                    kwargs[(ext_lower := ext.lower())]
                    or getattr(Constants, ext)()
                    )
                ) is not None
            }

    authorizers: list[objects.security.Authorizer] = extensions['authorizers']
    integrations: list[objects.base.Component] = extensions['integrations']
    response_headers: objects.response.Headers = extensions['response_headers']  # noqa
    request_headers: objects.parameter.Parameters = extensions['request_headers']  # noqa
    errors: list[Exception] = extensions['errors']

    if 'return' not in event_handler_function.__annotations__:
        raise exceptions.InvalidReturnSignatureError(
            ' '.join(
                (
                    f'Function {event_handler_function!s} missing',
                    'return signature. docent requires all functions',
                    'decorated with a REST method to be annotated with a',
                    'return signature.'
                    )
                )
            )
    elif not (
        isinstance(
            (return_type := event_handler_function.__annotations__['return']),
            (
                docent.core.DocMeta,
                docent.core.DocObject,
                )
            )
        or hasattr(return_type, '__args__')
        or return_type is None
        ):
        raise exceptions.InvalidReturnSignatureError(
            ' '.join(
                (
                    f'Function {event_handler_function!s}',
                    'return signature must be an DocObject,',
                    'list[DocObject], typing.Union[DocObject],',
                    '`None`, or variation thereof.',
                    )
                ) + f'\nCurrent value: {return_type!s}'
            )

    path_obj = cls.PATHS[cls.resource_key]['ID' if id_in_path else 'NO_ID']
    parameters = objects.parameter.Parameters.from_list(
        path_obj._path_parameters._extensions
        )

    if (
        method_name in {
            'delete',
            'get',
            }
        and not id_in_path
        ) or method_name == 'patch':
        parameters += objects.parameter.Parameters.from_object(
            cls.resource,
            method_name=method_name
            )
    if request_headers:
        parameters += request_headers

    success_response = objects.response.ResponseSpec.from_annotation(
        return_type,
        method_name,
        cls.PATHS[cls.resource_key]['NO_ID']._name,
        response_headers,
        )
    responses = objects.response.Responses(
        _extensions=[
            success_response,
            *[
                objects.response.ResponseSpec.from_exception(
                    exception,
                    method_name,
                    path_obj._name,
                    many=not id_in_path,
                    )
                for exception
                in errors
                ],
            *[
                objects.response.ResponseSpec.from_exception(
                    exception,
                    method_name,
                    path_obj._name,
                    many=not id_in_path,
                    )
                for exception
                in Constants.BASE_ERROR_CODES
                ]
            ]
        )

    body = objects.request.RequestBody.from_object(
        cls.resource if id_in_path else list[cls.resource],
        method_name=method_name,
        ) if method_name in {'post', 'put'} else None

    path_ids = [
        path_parameter.name
        for path_parameter
        in path_obj._path_parameters
        if (
            (
                path_parameter.name == cls._resource_id
                and id_in_path
                )
            or path_parameter.name != cls._resource_id
            )
        ]

    body_validator = objects.validator.SchemaValidator.from_object(
        cls.resource,
        request_attribute='body',
        method_name=method_name,
        many=not id_in_path,
        resource_id=(
            cls._resource_id
            if id_in_path
            else cls.resource_id
            ),
        ) if body else None

    parameters_validator = objects.validator.SchemaValidator.from_object(
        cls.resource,
        path_ids=path_ids,
        request_attribute='parameters',
        method_name=method_name,
        many=not id_in_path,
        resource_id=(
            cls._resource_id
            if id_in_path
            else cls.resource_id
            ),
        ) if parameters else None

    setattr(
        path_obj,
        method_name,
        objects.method.Method(
            parameters=parameters.as_reference if parameters else None,
            requestBody=body.as_reference if body is not None else None,
            responses=responses.as_reference if responses else None,
            security_=[
                {auth._name: []}
                for auth
                in authorizers
                ],
            tags=cls.tags or [],
            description=event_handler_function.__doc__,
            _name=method_name,
            _many=not id_in_path,
            _extensions=integrations,
            _callable=event_handler_function,
            _response_headers=response_headers,
            _body_validator=body_validator,
            _parameters_validator=parameters_validator,
            )
        )

    if not path_obj.options:
        options_responses = objects.response.Responses(
            _extensions=[
                objects.response.ResponseSpec(
                    _name=Constants.DOC_DELIM.join(
                        (
                            path_obj._name,
                            '200'
                            )
                        ),
                    description='Resource options response.',
                    headers=response_headers,
                    )
                ]
            )

        def _handle_options_request(_: objects.request.Request) -> None:
            return None

        path_obj.options = objects.method.Method(
            _name='options',
            description='Resource options.',
            responses=options_responses.as_reference,
            tags=cls.tags,
            _many=not id_in_path,
            _callable=_handle_options_request,
            _response_headers=response_headers,
            )


class Resource(metaclass=objects.base.ComponentMeta):  # noqa
    """
    A RESTful Resource.

    ---

    Usage
    -----

    * Subclass this to create a new resource.

    * A RESTful path is automatically generated from subclass name, \
    hierarchy, and any included path prefices or suffices.


    #### Usage Example 1

    ##### Route Table 1

    ```
    | METHOD        | PATH                      |
    | ------------- | ------------------------- |
    | DELETE (MANY) | /campaigns/               |
    | DELETE (ONE)  | /campaigns/${campaign_id} |
    | GET (MANY)    | /campaigns                |
    | GET (ONE)     | /campaigns/${campaign_id} |
    | PATCH (ONE)   | /campaigns/${campaign_id} |
    | POST (MANY)   | /campaigns                |
    | PUT (MANY)    | /campaigns                |
    | PUT (ONE)     | /campaigns/${campaign_id} |
    ```

    ##### Generated from:

    ```py
    import docent.rest


    @docent.rest.API
    class Campaigns(docent.rest.Resource):
        ...

    ```


    #### Usage Example 2

    ##### Route Table 2

    ```
    | METHOD        | PATH                                                 |
    | ------------- | ---------------------------------------------------- |
    | DELETE (MANY) | /campaigns/${campaign_id}/placements/                |
    | DELETE (ONE)  | /campaigns/${campaign_id}/placements/${placement_id} |
    | GET (MANY)    | /campaigns/${campaign_id}/placements                 |
    | GET (ONE)     | /campaigns/${campaign_id}/placements/${placement_id} |
    | PATCH (ONE)   | /campaigns/${campaign_id}/placements/${placement_id} |
    | POST (MANY)   | /campaigns/${campaign_id}/placements                 |
    | PUT (MANY)    | /campaigns/${campaign_id}/placements                 |
    | PUT (ONE)     | /campaigns/${campaign_id}/placements/${placement_id} |
    ```

    ##### Generated from:

    ```py
    import docent.rest


    @docent.rest.API
    class Campaigns(docent.rest.Resource):
        ...


    @docent.rest.API
    class Placements(Campaigns):
        ...

    ```


    ---

    Routing Requests
    ----------------

    * Register methods by decorating a function that takes a Request \
    and returns an DocObject, a list of DocObjects, or a \
    union of DocObjects.

    #### Request Routing Example 1:

    ```py
    import docent.core
    import docent.rest


    @docent.rest.API
    class Campaigns(docent.rest.Resource):
        ...


    @Campaigns.PATCH_ONE
    def update_campaign(Request) -> docent.core.DocObject:
        ...

    ```

    #### Request Routing Example 2:

    ```py
    import dataclasses
    import typing

    import docent.core
    import docent.rest


    @dataclasses.dataclass
    class Campaign(docent.core.DocObject):
        ...


    @dataclasses.dataclass
    class DigitalCampaign(docent.core.DocObject):
        ...


    @docent.rest.API
    class Campaigns(docent.rest.Resource):
        ...


    @Campaigns.GET_MANY
    def get_campaigns(Request) -> list[typing.Union[Campaign, DigitalCampaign]]:
        ...

    ```

    ---

    Error Handling
    --------------

    * The `docent.rest.exceptions` module comes pre-loaded with common \
    HTTP exceptions that can be raised within a decorated method \
    to automatically generate an error response with the correcr error \
    code and message for the situation.

    * Additionally, docent is built to convert builtin python exceptions \
    into sensible HTTP counterparts.
        \
        * For example, `SyntaxError` can be raised to return a 400 error \
        response to a user when an invalid request is received.
        \
        * Similarly, `FileNotFoundError` can be raised to return a 404 \
        error response.

    Python Exceptions are mapped to HTTP Errors as follows:

    ```py
    ConnectionRefusedError : NotAuthenticatedError(401)
    Exception              : UnexpectedError(500)
    FileExistsError        : RequestError(400)
    FileNotFoundError      : ResourceNotFoundError(404)
    ModuleNotFoundError    : MethodNotAllowedError(405)
    NotImplementedError    : MethodNotImplementedError(501)
    PermissionError        : NotAuthorizedError(403)
    SyntaxError            : RequestError(400)
    ```

    ---

    Special Rules
    -------------

    * All resource names must end with the letter: 's'.

    * Do not forget to decorate your resources with the API class.

    ```py
    import docent.rest


    @docent.rest.API
    class Pets(docent.rest.Resource):
        ...

    ```

    * Type annotations must be included on decorated functions' \
    return signatures. `None` is allowed to indicate an empty response.

    ```py
    import dataclasses

    import docent.core
    import docent.rest


    @dataclasses.dataclass
    class Campaign(docent.core.DocObject):
        ...

    @docent.rest.API
    class Campaigns(docent.rest.Resource):
        ...

    @Campaigns.GET_ONE
    def get_campaign(Request) -> Campaign:  # Correct annotation
        ...

    ```

    * You must implement a classmethod 'resource' property \
    on any derived class. The classmethod must return the DocObject \
    derivative to be controlled by the resource. Example below.

    ```py
    import dataclasses

    import docent.core
    import docent.rest


    @dataclasses.dataclass
    class Campaign(docent.core.DocObject):
        ...


    @docent.rest.API
    class Campaigns(docent.rest.Resource):
    
        @classmethod
        @property
        def resource(cls) -> Campaign:
            return Campaign

    ```

    """

    PATHS: dict[str, dict[str, objects.path.Path]] = {}

    PATH_PREFICES: list[str] = []
    PATH_SUFFICES: list[str] = []

    AUTHORIZERS: list[objects.security.Authorizer] = []
    INTEGRATIONS: list[objects.base.Component] = []
    RESPONSE_HEADERS: objects.response.Headers = objects.response.Headers()  # noqa
    REQUEST_HEADERS: objects.parameter.Parameters = objects.parameter.Parameters()  # noqa
    ERRORS: list[Exception] = []

    def __init_subclass__(cls):  # noqa
        if cls.__name__ == 'Healthz':
            pass
        elif not cls.__name__.endswith('s'):
            raise exceptions.NotRESTfulError(
                ' '.join(
                    (
                        'REST Violation -',
                        f'Resource: {cls.__name__}',
                        "must end with the letter 's'."
                        )
                    )
                )

        if (
            'docs' in (l := cls.__name__.lower())
            or 'favicon' in l
            ):
            raise exceptions.ReservedKeywordError(
                ' '.join(
                    (
                        f'Resource: {cls.__name__}',
                        'cannot contain any of the following',
                        'words in its name:',
                        "['docs', 'favicon']",
                        '(case insensitive).'
                        )
                    )
                )

        cls.PATHS.setdefault(cls.resource_key, {})
        cls.PATHS[cls.resource_key]['NO_ID'] = objects.path.Path(
            _name=cls.path_schema,
            )

        path_schema_id = '/'.join(
            (
                cls.path_schema,
                '{' + cls._resource_id + '}'
                )
            )

        cls.PATHS[cls.resource_key]['ID'] = (
            objects.
            path.
            Path(_name=path_schema_id)
            )

        return super().__init_subclass__()

    @classmethod
    def _register_method(
        cls,
        event_handler_function: typing.Callable[
            ['objects.request.Request'],
            None
            ],
        method_name: str,
        id_in_path: bool,
        *args,
        **kwargs
        ) -> typing.Callable:

        _prepare_method(
            cls,
            method_name,
            event_handler_function,
            id_in_path=id_in_path,
            authorizers=kwargs.get('authorizers'),
            integrations=kwargs.get('integrations'),
            response_headers=kwargs.get('response_headers'),
            request_headers=kwargs.get('request_headers'),
            errors=kwargs.get('errors'),
            )

        return event_handler_function

    @classmethod
    def DELETE_MANY(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'delete'
        id_in_path: bool = False

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def DELETE_ONE(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'delete'
        id_in_path: bool = True

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def GET_MANY(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'get'
        id_in_path: bool = False

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def GET_ONE(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'get'
        id_in_path: bool = True

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def PATCH_ONE(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'patch'
        id_in_path: bool = True

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def POST_MANY(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'post'
        id_in_path: bool = False

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def PUT_MANY(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'put'
        id_in_path: bool = False

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def PUT_ONE(
        cls,
        *args,
        **kwargs,
        ) -> typing.Callable:  # noqa

        method_name: str = 'put'
        id_in_path: bool = True

        if args:
            event_handler_function, *args = args
            return cls._register_method(
                event_handler_function,
                method_name,
                id_in_path,
                *args,
                **kwargs
                )
        else:
            def _wrapper(
                event_handler_function: typing.Callable[
                    ['objects.request.Request'],
                    None
                    ],
                *args,
                **kwargs
                ) -> typing.Callable:
                return cls._register_method(
                    event_handler_function,
                    method_name,
                    id_in_path,
                    *args,
                    **kwargs
                    )
            return _wrapper

    @classmethod
    def validate_path(
        cls,
        request_path_as_list: list[str]
        ) -> str:  # noqa
        if not request_path_as_list:
            return 'NO_ID'
        for idx, k in enumerate(cls.path_schema.split('/')):
            if request_path_as_list[idx] != k and not (
                k.startswith('{')
                and k.endswith('}')
                ):
                raise FileNotFoundError(
                    ' '.join(
                        (
                            'Invalid request path structure.',
                            'No resource could be found at path:',
                            '/'.join(request_path_as_list)
                            )
                        )
                    )
        if len(request_path_as_list) < len(cls.path_schema.split('/')) - 1:
            raise FileNotFoundError(
                ' '.join(
                    (
                        'Invalid request path length.',
                        'No resource could be found at path:',
                        '/'.join(request_path_as_list)
                        )
                    )
                )
        elif len(request_path_as_list) <= len(cls.path_schema.split('/')):
            return 'NO_ID'
        else:
            return 'ID'

    @classmethod
    @property
    def resource(cls) -> docent.core.objects.DocObject:  # noqa
        raise NotImplementedError(
            ' '.join(
                (
                    'Must implement a classmethod property returning',
                    'an uninstantiated class object of the resource',
                    'to be managed.'
                    )
                )
            )

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def _resource_id(cls) -> str:
        return '_'.join(
            (
                singular.removesuffix('ie') + 'y' if (
                    singular := docent.core.utils.camel_case_to_snake_case(
                        cls.__name__.removesuffix('s')
                        )
                    ).endswith('ie') else singular,
                'id'
                )
            )

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def resource_id(cls) -> str:
        """
        Unique ID field name for the resource.

        Default is to_snake_case(Resource.lower().removesuffix('s'))
        if this field is available on the object (ex. 'pet_id'),
        otherwise will use the shortest available field ending
        in 'id' or 'id_' (case insensitive).
        """

        cls.resource: docent.core.objects.DocObject
        if (
            cls.resource.reference
            == 'docent-rest-healthz-resource-heartBeat'
            ):
            return 'healthz_id'
        elif (
            (k := cls._resource_id)
            and k in cls.resource
            ):
            return k
        elif (
            ordering := sorted(
                (
                    f
                    for f
                    in cls.resource.fields
                    if f.strip('_').lower().endswith('id')
                    ),
                key=lambda k: len(k)
                )
            ):
            return ordering[0]
        else:
            return k

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def resource_key(cls) -> str:  # noqa
        # return '.'.join((cls.__module__, cls.__name__))
        return '.'.join(
            (
                cls.__module__,
                *[prefix.lower() for prefix in cls.PATH_PREFICES],
                cls.__name__
                )
            )

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def path_schema(cls) -> str:  # noqa
        cls.__bases__: tuple['Resource']
        parent_schema_elements = [
            '/'.join(
                (
                    parent.path_schema,
                    '{' + '_'.join(
                        (
                            docent.core.utils.camel_case_to_snake_case(
                                parent.__name__.removesuffix('s')
                                ),
                            'id'
                            )
                        ) + '}'
                    )
                )
            for parent
            in cls.__bases__
            if parent.__name__ != 'Resource'
            ]
        if parent_schema_elements:
            path = '/'.join(
                (
                    *parent_schema_elements,
                    docent.core.utils.camel_case_to_snake_case(cls.__name__)
                    )
                )
        elif (prefix := '/'.join(cls.PATH_PREFICES)):
            path = '/'.join(
                (
                    prefix,
                    docent.core.utils.camel_case_to_snake_case(cls.__name__)
                    )
                )
        else:
            path = docent.core.utils.camel_case_to_snake_case(cls.__name__)
        if (suffix := '/'.join(cls.PATH_SUFFICES)):
            suffix = '/' + suffix
        return path + suffix

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def tags(cls) -> list[str]:  # noqa
        split_string = Constants.PATH_ID_PARSE_EXPR.sub(
            '',
            cls.path_schema
            ).replace('//', '/').strip('/').split('/')
        return [
            Constants.TAG_DELIM.join(
                [
                    docent.core.utils.to_camel_case(s)
                    for s
                    in split_string
                    if s and s != 'api'
                    ]
                )
            ]

    @classmethod
    @property
    def methods(cls) -> typing.Iterator[objects.method.Method]:
        """Yield all methods for resource."""

        for path_obj in cls.PATHS[cls.resource_key].values():
            for method_name in {'delete', 'get', 'patch', 'post', 'put'}:
                if (method_obj := getattr(path_obj, method_name)) is not None:
                    yield method_obj

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def as_enum(cls) -> 'Resource':
        """Return an Enumeration resource for the managed object."""

        @dataclasses.dataclass
        class Enumeration(docent.core.objects.DocObject):
            """Contains documented object enums."""

            name: str = dataclasses.field(
                default=None,
                metadata={
                    'ignore': True,
                    }
                )
            values: list = dataclasses.field(
                default_factory=list,
                metadata={
                    'ignore': True,
                    }
                )

        Enumeration.__name__ = cls.resource.__name__ + 'Enumeration'

        class Enums(Resource):  # noqa

            PATH_PREFICES = [
                prefix
                for prefix
                in cls.path_schema.strip('/').split('/')
                if Constants.PATH_ID_PARSE_EXPR.search(prefix) is None
                ]

            @classmethod
            @property
            def resource(cls) -> Enumeration:  # noqa
                return Enumeration

        for ext in Constants.EXTENSIONS:
            extension = getattr(Enums, ext)
            extension += getattr(cls, ext)
            setattr(Enums, ext, extension)

        @Enums.GET_MANY
        def get_enums(
            request: objects.Request
            ) -> list[Enumeration]:
            """Retrieve all enumerated field values for the object."""

            return [
                Enumeration(name=k, values=v)
                for k, v
                in cls.resource.enumerations.items()
                ]

        return Enums
