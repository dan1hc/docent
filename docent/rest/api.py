__all__ = (
    'API',
    'APIMeta',
    )

import traceback
import typing
import uuid

import docent.core

from . import commands
from . import constants
from . import enums
from . import exceptions
from . import resource
from . import objects
from . import static
from . import utils


class Constants(constants.FrameworkConstants):  # noqa

    DEFAULT_RESPONSE_HEADERS: objects.response.Headers = (
        objects.response.Headers.from_list(
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
            )
        )


class APIMeta(type):  # noqa

    APPLICATION: str = None
    APPLICATION_RESOURCES: list[tuple[str, set[int], resource.Resource]] = []

    AUTHORIZERS: list[objects.security.Authorizer] = []
    INTEGRATIONS: list[objects.base.Component] = []
    RESPONSE_HEADERS: objects.response.Headers = Constants.DEFAULT_RESPONSE_HEADERS  # noqa
    REQUEST_HEADERS: objects.parameter.Parameters = objects.parameter.Parameters()  # noqa
    ERRORS: list[Exception] = []

    def __wrapped_call__(
        cls,
        rsc: resource.Resource,
        *args,
        **kwargs
        ) -> resource.Resource:

        for ext in Constants.EXTENSIONS:
            app_extension = getattr(cls, ext)
            rsc_extension = getattr(rsc, ext)
            if (extension := kwargs.get(ext.lower())):
                extension += app_extension
                extension += rsc_extension
                setattr(rsc, ext, extension)
            else:
                setattr(rsc, ext, app_extension + rsc_extension)

        cls.APPLICATION_RESOURCES: list[tuple[str, set[int], resource.Resource]]  # noqa
        cls.APPLICATION_RESOURCES.append(
            (
                rsc.path_schema,
                {
                    i
                    for i, v
                    in enumerate(rsc.path_schema.split('/'))
                    if Constants.PATH_ID_PARSE_EXPR.search(v) is not None
                    },
                rsc
                )
            )
        cls.APPLICATION_RESOURCES.append(
            (
                (
                    id_schema := '/'.join(
                        (
                            rsc.path_schema,
                            '{' + rsc._resource_id + '}'
                            )
                        )
                    ),
                {
                    i
                    for i, v
                    in enumerate(id_schema.split('/'))
                    if Constants.PATH_ID_PARSE_EXPR.search(v) is not None
                    },
                rsc
                )
            )

        if kwargs.get('include_enums_endpoint'):

            path_schema = Constants.PATH_ID_PARSE_EXPR.sub(
                '',
                rsc.as_enum.path_schema
                ).replace('//', '/').strip('/')

            cls.APPLICATION_RESOURCES.append(
                (
                    path_schema,
                    set(),
                    rsc.as_enum
                    )
                )

        if not cls.APPLICATION:
            cls.APPLICATION = rsc.__module__.split('.')[0]

        return rsc

    def __call__(
        cls,
        *args,
        **kwargs,
        ) -> resource.Resource:
        """Register a resource object for central request processing."""  # noqa

        if args:
            rsc, *args = args
            return cls.__wrapped_call__(rsc, *args, **kwargs)
        else:
            def _wrapper(rsc: resource.Resource) -> resource.Resource:
                return cls.__wrapped_call__(rsc, *args, **kwargs)
            return _wrapper

    def __getitem__(
        cls,
        request: objects.Request
        ) -> tuple[docent.core.objects.DocObject, int]:

        cls.route_request: typing.Callable[[list[str]], resource.Resource]
        cls.process_request: typing.Callable[
            [resource.Resource, objects.Request],
            tuple[docent.core.objects.DocObject, int]
            ]

        requested_resource = cls.route_request(request.path_as_list)

        if requested_resource is None:
            response_msg = ' '.join(
                (
                    'Invalid request path.',
                    'No resource could be found at path:',
                    f'{request.path!s}'
                    )
                )
            response = objects.response.Error.from_exception(
                FileNotFoundError(response_msg)
                )
            status_code = response.errorCode
            docent.core.log.error(
                {
                    'request_id': uuid.uuid4().hex,
                    'resource': (
                        requested_resource.__name__
                        if hasattr(requested_resource, '__name__')
                        else None
                        ),
                    'message': 'error processing request',
                    'status_code': str(status_code),
                    'response': response
                    },
                )
        else:
            response, status_code = cls.process_request(
                requested_resource,
                request
                )

        return response, status_code


class API(metaclass=APIMeta):
    """
    Primary resource registry for docent APIs.

    ---

    Usage
    -----


    #### Step 1
    Decorate a Resource object to wire it to handle requests.

    ```py
    import docent.rest

    @docent.rest.API(
        include_enums_endpoint=True,
        )
    class Pets(docent.rest.Resource):  # noqa
        ...

    ```

    #### Step 2
    Then, use the API object as follows when a request arrives \
    to actually process it:

    ```py
    import docent.rest

    request = docent.rest.Request(
        body={'name': 'Sophie', 'type': 'dog'},
        headers={'x-docent-example-header': '*'},
        method='POST',
        path='/api/v1/pets',
        params={}
        )

    response_obj, status_code = docent.rest.API[request]

    ```
 
    """

    CONFIG: list[str] = []

    @classmethod
    def route_request(
        cls,
        request_path_as_list: list[str]
        ) -> resource.Resource:  # noqa

        if request_path_as_list and any(
            (
                'favicon' in request_path_as_list[-1],
                'docs' in request_path_as_list[-1],
                )
            ):
            return objects.documentation.Swagger

        affixes: list[str] = []
        for (_, _, rsc) in cls.APPLICATION_RESOURCES:
            affixes.extend(rsc.PATH_PREFICES)
            affixes.extend(rsc.PATH_SUFFICES)
            affixes.append(rsc.__name__.lower())

        for resource_meta in cls.APPLICATION_RESOURCES:
            if (
                resource_meta[0] == 'healthz'
                and not request_path_as_list
                ):
                return resource_meta[2]

            path_trimmed = '/'.join(
                [
                    (
                        resource_meta[0].split('/')[i]
                        if (
                            i in resource_meta[1]
                            and v not in affixes
                            )
                        else v
                        )
                    for i, v
                    in enumerate(request_path_as_list)
                    ]
                )

            if resource_meta[0] == path_trimmed:
                return resource_meta[2]

    @classmethod
    def process_request(
        cls,
        rsc: resource.Resource,
        request: 'objects.request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa

        try:
            request_id = uuid.uuid4().hex
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': rsc.__name__,
                    'message': 'validating request',
                    'request': request,
                    }
                )
            if rsc is not objects.documentation.Swagger:
                method_obj, request = cls._validate_resource_request(
                    rsc,
                    request
                    )
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': rsc.__name__,
                    'message': 'processing validated request',
                    'request': request
                    }
                )
            if rsc is objects.documentation.Swagger:
                response_obj, status_code = cls._handle_docs_request(
                    rsc,
                    request
                    )
            else:
                response_obj, status_code = cls._handle_resource_request(
                    method_obj,
                    request
                    )
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': rsc.__name__,
                    'message': 'request processed successfully',
                    'status_code': str(status_code),
                    'response': response_obj,
                    },
                )
        except Exception as exception:
            api_module = rsc.__module__.split('.')[0]
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
                    'resource': rsc.__name__,
                    'message': 'error processing request',
                    'status_code': str(status_code),
                    'response': response_obj,
                    },
                )

        return response_obj, status_code

    @classmethod
    def _handle_docs_request(
        cls,
        rsc: resource.Resource,
        request: 'objects.request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:
        if request.path.endswith('.json'):
            response_obj = objects.documentation.SwaggerJSON(
                data=utils.spec_from_api(
                    (
                        '',
                        cls.APPLICATION,
                        *cls.CONFIG
                        ),
                    commands.HELP_TEXT,
                    commands.VALID_FLAGS,
                    commands.VALID_KWARG_FLAGS,
                    commands.DEFAULT_OPENAPI_VERSION,
                    commands.DEFAULT_APP_VERSION
                    )
                )
            status_code = 200
        elif request.path.endswith('.yaml'):
            response_obj = objects.documentation.SwaggerYAML(
                data=utils.spec_from_api(
                    (
                        '',
                        cls.APPLICATION,
                        *cls.CONFIG
                        ),
                    commands.HELP_TEXT,
                    commands.VALID_FLAGS,
                    commands.VALID_KWARG_FLAGS,
                    commands.DEFAULT_OPENAPI_VERSION,
                    commands.DEFAULT_APP_VERSION
                    )
                )
            status_code = 200
        elif request.path.endswith('.ico'):
            response_obj = objects.documentation.SwaggerICON()
            status_code = 200
        elif request.path.endswith('16x16.png'):
            response_obj = objects.documentation.SwaggerICON(
                img=static.ICON16
                )
            status_code = 200
        elif request.path.endswith('32x32.png'):
            response_obj = objects.documentation.SwaggerICON(
                img=static.ICON32
                )
            status_code = 200
        elif rsc.PATH_SUFFICES:
            response_obj = objects.documentation.SwaggerHTML(
                title=docent.core.utils.to_camel_case(cls.APPLICATION),
                path='/' + '/'.join(
                    (
                        *rsc.PATH_SUFFICES,
                        'docs.yaml'
                        )
                    )
                )
            status_code = 200
        else:
            response_obj = objects.documentation.SwaggerHTML(
                title=docent.core.utils.to_camel_case(cls.APPLICATION)
                )
            status_code = 200

        return response_obj, status_code

    @classmethod
    def _handle_resource_request(
        cls,
        method_obj: 'objects.method.Method',
        request: 'objects.request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:

        response_obj = method_obj(request)
        status_code = Constants.METHOD_SUCCESS_CODES.get(
            request.method.lower(),
            200
            )

        return response_obj, status_code

    @classmethod
    def _validate_resource_request(
        cls,
        rsc: resource.Resource,
        request: 'objects.request.Request'
        ) -> tuple['objects.method.Method', 'objects.request.Request']:

        if request.method.lower() == 'post':
            path_key = 'NO_ID'
        else:
            path_key = rsc.validate_path(request.path_as_list)

        path_obj = rsc.PATHS[rsc.resource_key][path_key]
        path_obj.validate_method(request.method, request.path)

        method_obj: 'objects.method.Method' = getattr(
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

        return method_obj, request
