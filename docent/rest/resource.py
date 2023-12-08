__all__ = (
    'Resource',
    )

import functools
import re
import traceback
import typing
import uuid

import docent.core

from . import constants
from . import enums
from . import exceptions
from . import objects


class Constants(constants.FrameworkConstants):  # noqa

    pass


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
    authorizers: list[objects.security.Authorizer] = None,
    integrations: list[objects.base.Component] = None,
    response_headers: objects.response.Headers = None,
    request_headers: objects.parameter.Parameters = None,
    errors: list[Exception] = None,
    ):

    if 'return' not in event_handler_function.__annotations__:
        raise exceptions.InvalidReturnSignatureError(
            ' '.join(
                (
                    f'Function {event_handler_function!s} missing',
                    'return signature. Docent requires all functions',
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

    path_obj = cls.PATHS[
        '.'.join((cls.__module__, cls.__name__))
        ][
        'ID'
        if id_in_path
        else 'NO_ID'
        ]

    parameters = path_obj._path_parameters

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
        cls.PATHS['.'.join((cls.__module__, cls.__name__))]['NO_ID']._name,
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
                in (errors or [])
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

    resource_id = '_'.join(
        (
            docent.core.utils.camel_case_to_snake_case(
                cls.resource.__name__.removesuffix('s')
                ),
            'id'
            )
        )
    path_ids = [
        path_parameter.name
        for path_parameter
        in path_obj._path_parameters
        if (
            (
                path_parameter.name == resource_id
                and id_in_path
                )
            or path_parameter.name != resource_id
            )
        ]

    body_validator = objects.validator.SchemaValidator.from_object(
        cls.resource,
        request_attribute='body',
        method_name=method_name,
        many=not id_in_path,
        resource_id=(
            resource_id
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
            resource_id
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
                in (authorizers or [])
                ],
            tags=cls.tags or [],
            description=event_handler_function.__doc__,
            _name=method_name,
            _many=not id_in_path,
            _extensions=integrations or [],
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
                    headers=response_headers or objects.response.Headers.from_list(
                        [
                            objects.response.Header(
                                header.value,
                                description=(
                                    enums.header.DefaultHeaderValues[
                                        header.name
                                        ].value
                                    )
                                )
                            for header
                            in enums.header.DefaultHeaders
                            ]
                        ),
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


class ResourceMeta(objects.base.ComponentMeta):  # noqa

    def __getitem__(
        cls,
        request: 'objects.request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:
        return cls.process_request(request)

    @classmethod
    def process_request(
        cls,
        request: 'objects.request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa
        ...


class Resource(metaclass=ResourceMeta):  # noqa
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


    @docent.rest.Route
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


    @docent.rest.Route
    class Campaigns(docent.rest.Resource):
        ...


    @docent.rest.Route
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


    @docent.rest.Route
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


    @docent.rest.Route
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

    * Additionally, Docent is built to convert builtin python exceptions \
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

    * Do not forget to decorate your resources with the Route class.

    ```py
    import docent.rest


    @docent.rest.Route
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

    @docent.rest.Route
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


    @docent.rest.Route
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
            (l := cls.__name__.lower()) == 'docs'
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

        cls.PATHS.setdefault('.'.join((cls.__module__, cls.__name__)), {})
        cls.PATHS[
            '.'.join((cls.__module__, cls.__name__))
            ]['NO_ID'] = objects.path.Path(
                _name=cls.path_schema,
                )
        resource_id = '_'.join(
            (
                docent.core.utils.camel_case_to_snake_case(
                    cls.resource.__name__.removesuffix('s')
                    ),
                'id'
                )
            )
        path_schema_id = '/'.join(
            (
                cls.path_schema,
                '{' + resource_id + '}'
                )
            )
        cls.PATHS['.'.join((cls.__module__, cls.__name__))]['ID'] = (
            objects.path.Path(_name=path_schema_id)
            )

        return super().__init_subclass__()

    def __getitem__(
        self,
        request: 'objects.request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa
        return self.__class__[request]

    @classmethod
    def DELETE_MANY(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                None
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'delete',
                event_handler_function,
                id_in_path=False,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def DELETE_ONE(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                None
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'delete',
                event_handler_function,
                id_in_path=True,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def GET_MANY(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                list[docent.core.objects.DocObject]
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'get',
                event_handler_function,
                id_in_path=False,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def GET_ONE(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                docent.core.objects.DocObject
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'get',
                event_handler_function,
                id_in_path=True,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def PATCH_ONE(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                docent.core.objects.DocObject
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'patch',
                event_handler_function,
                id_in_path=True,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def POST_MANY(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                list[docent.core.objects.DocObject]
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'post',
                event_handler_function,
                id_in_path=False,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def PUT_MANY(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                list[docent.core.objects.DocObject]
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'put',
                event_handler_function,
                id_in_path=False,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def PUT_ONE(
        cls,
        authorizers: list[objects.security.Authorizer] = None,
        integrations: list[objects.base.Component] = None,
        response_headers: objects.response.Headers = None,
        request_headers: objects.parameter.Parameters = None,
        errors: list[Exception] = None,
        ) -> typing.Callable:  # noqa

        def _wrapper(
            event_handler_function: typing.Callable[
                ['objects.request.Request'],
                docent.core.objects.DocObject
                ],
            ) -> 'Resource':

            _prepare_method(
                cls,
                'put',
                event_handler_function,
                id_in_path=True,
                authorizers=authorizers,
                integrations=integrations,
                response_headers=response_headers,
                request_headers=request_headers,
                errors=errors,
                )

            return event_handler_function

        return _wrapper

    @classmethod
    def process_request(
        cls,
        request: 'objects.request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa
        try:
            request_id = uuid.uuid4().hex
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': cls.__name__,
                    'message': 'validating request',
                    'request': request,
                    }
                )

            if request.method.lower() == 'post':
                path_key = 'NO_ID'
            else:
                path_key = cls.validate_path(request.path_as_list)

            path_obj = cls.PATHS[
                '.'.join((cls.__module__, cls.__name__))
                ][path_key]
            path_obj.validate_method(request.method, request.path)

            method_obj: objects.method.Method = getattr(
                path_obj,
                request.method.lower()
                )

            parameters = {}

            if request.headers:
                parameters.update(request.headers)
            if request.params:
                parameters.update(request.params)

            if parameters:
                method_obj.validate_against_schema('parameters', parameters)
            if request.body:
                method_obj.validate_against_schema('body', request.body)

            (
                request_body,
                request_params
                ) = method_obj.parse_request_dtypes(
                    request.body,
                    request.params
                    )
            request.body = request_body
            request.params = request_params
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': cls.__name__,
                    'message': 'processing validated request',
                    'request': request
                    }
                )
            response_obj = method_obj(request)
            status_code = Constants.METHOD_SUCCESS_CODES.get(
                request.method.lower(),
                200
                )
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': cls.__name__,
                    'message': 'request processed successfully',
                    'status_code': str(status_code),
                    'response': response_obj,
                    },
                )
        except Exception as exception:
            api_module = cls.__module__.split('.')[0]
            most_recent_trace = traceback.format_tb(
                exception.__traceback__
                )[-1]
            if len(spl := most_recent_trace.strip().split(', ')) != 3:
                is_error_raised = False
            else:
                file_name, _, trace = spl
                is_error_raised = ' raise ' in trace
                is_error_from_api = api_module in file_name
            if is_error_raised or is_error_from_api:
                response_obj = objects.response.Error.from_exception(exception)
            else:
                response_obj = objects.response.Error.from_exception(
                    exceptions.UnexpectedError
                    )
            status_code = response_obj.errorCode
            docent.core.log.error(
                {
                    'request_id': request_id,
                    'resource': cls.__name__,
                    'message': 'error processing request',
                    'status_code': str(status_code),
                    'response': response_obj,
                    },
                )
        return response_obj, status_code

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
    def resource_id(cls) -> str:
        """
        Unique ID field name for the resource.

        Default is to_snake_case(Resource.lower().removesuffix('s'))
        if this field is available on the object (ex. 'pet_id'),
        otherwise will use the shortest available field ending
        in 'id' or 'id_' (case insensitive).
        """

        if (
            cls.resource.reference
            == 'docent-rest-healthz-resource-heartBeat'
            ):
            return 'healthz_id'
        elif (
            (
                k := '_'.join(
                    (
                        singular.removesuffix('ie') + 'y' if (
                            singular := docent.core.utils.camel_case_to_snake_case(
                                cls.__name__.removesuffix('s')
                                )
                            ).endswith('ie') else singular,
                        'id'
                        )
                    )
                )
            and (
                (_k := k.strip('_')) in cls.resource.fields
                or ('_' + _k) in cls.resource.fields
                or (_k + '_') in cls.resource.fields
                or ('_' + _k + '_') in cls.resource.fields
                )
            ):
            return k
        else:
            return sorted(
                (
                    f
                    for f
                    in cls.resource.fields
                    if f.strip('_').lower().endswith('id')
                    ),
                key=lambda k: len(k)
                )[0]

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
        split_string = re.sub(
            Constants.PATH_ID_PARSE_EXPR,
            '',
            cls.path_schema
            ).strip('/').split('/')
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
