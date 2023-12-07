__all__ = (
    'Route',
    'RouteMeta',
    )

import re
import typing
import uuid

import docent.core

from . import constants
from . import resource
from . import objects


class Constants(constants.FrameworkConstants):  # noqa

    pass


class RouteMeta(type):  # noqa

    APPLICATION_RESOURCES: list[tuple[str, set[int], resource.Resource]] = []

    def __call__(cls, rsc: resource.Resource) -> resource.Resource:
        """Register a resource object for central request processing."""  # noqa

        cls.APPLICATION_RESOURCES: list[tuple[str, set[int], resource.Resource]]
        cls.APPLICATION_RESOURCES.append(
            (
                re.sub(
                    Constants.PATH_ID_PARSE_EXPR,
                    '',
                    rsc.path_schema
                    ).strip('/'),
                {
                    i
                    for i, v
                    in enumerate(rsc.path_schema.split('/'))
                    if v.startswith('{') and v.endswith('}')
                    },
                rsc
                )
            )

        if not objects.documentation.Swagger.API:
            if rsc.__module__.startswith('docent.template'):
                objects.documentation.Swagger.API = 'docent.template.api'
            else:
                objects.documentation.Swagger.API = rsc.__module__.split('.')[0]  # noqa

        return rsc

    def __getitem__(
        cls,
        request: objects.Request
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa

        cls.route_request: typing.Callable[[list[str]], resource.Resource]
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
            response, status_code = requested_resource[request]

        return response, status_code


class Route(metaclass=RouteMeta):
    """
    Primary route registry for Docent APIs.

    ---

    Usage
    -----


    #### Step 1
    Decorate a Resource object to wire it to handle requests.

    ```py
    import docent.rest

    @docent.rest.Route
    class Pets(docent.rest.Resource):  # noqa
        ...

    ```

    #### Step 2
    Then, use the Route object as follows when a request arrives \
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

    response_obj, status_code = docent.rest.Route[request]

    ```
 
    """

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

        for resource_meta in cls.APPLICATION_RESOURCES:
            if (
                resource_meta[0] == 'healthz'
                and not request_path_as_list
                ):
                return resource_meta[2]
            elif len(request_path_as_list) > (
                len(s := resource_meta[0].split('/'))
                + len(resource_meta[1])
                + 1
                ):
                continue
            elif len(request_path_as_list) < (
                len(s := resource_meta[0].split('/'))
                + len(resource_meta[1])
                ):
                continue

            path_trimmed = '/'.join(
                [
                    v
                    for i, v
                    in enumerate(request_path_as_list)
                    if (
                        i not in resource_meta[1]
                        and i < len(s)
                        )
                    ]
                )

            if resource_meta[0] == path_trimmed:
                return resource_meta[2]
