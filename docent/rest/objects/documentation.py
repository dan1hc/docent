__all__ = (
    'Swagger',
    'SwaggerHTML',
    'SwaggerICON',
    'SwaggerJSON',
    'SwaggerMeta',
    'SwaggerYAML',
    )

import dataclasses
import string
import traceback
import uuid

import docent.core

from .. import commands
from .. import exceptions
from .. import static
from .. import utils

from . import constants
from . import request
from . import response


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class SwaggerHTML(docent.core.objects.DocObject):  # noqa

    title: str = 'Docent API'
    path: str = '/docs.yaml'
    html: str = static.HTML

    def __post_init__(self):  # noqa
        tpl = string.Template(self.html)
        self.html = tpl.safe_substitute(
            {
                'TITLE': self.title,
                'PATH': self.path
                }
            )


@dataclasses.dataclass
class SwaggerICON(docent.core.objects.DocObject):  # noqa

    img: bytes = static.ICON


@dataclasses.dataclass
class SwaggerJSON(docent.core.objects.DocObject):  # noqa

    data: str = None


@dataclasses.dataclass
class SwaggerYAML(docent.core.objects.DocObject):  # noqa

    data: str = None

    def __post_init__(self):
        yaml = ''

        for k in (
            standard_keys := (
                'openapi',
                'info',
                'servers',
                'paths',
                'components',
                )
            ):
            yaml += docent.core.utils.to_yaml({k: self.data[k]})

        for k in sorted(self.data):
            if k not in standard_keys:
                yaml += docent.core.utils.to_yaml({k: self.data[k]})

        self.data = yaml


class SwaggerMeta(type):

    def __getitem__(
        cls,
        request: 'request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa
        return cls.process_request(request)

    @classmethod
    def process_request(
        cls,
        request: 'request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa
        ...


class Swagger(metaclass=SwaggerMeta):  # noqa

    API: str = None
    ARGS: list[str] = []
    PATH_SUFFICES: list[str] = []

    def __getitem__(
        self,
        request: 'request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa
        return self.__class__[request]

    @classmethod
    def process_request(
        cls,
        request: 'request.Request'
        ) -> tuple[docent.core.objects.DocObject, int]:  # noqa
        try:
            request_id = uuid.uuid4().hex
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': cls.__name__,
                    'message': 'processing docs request',
                    'request': request
                    }
                )
            if request.path.endswith('.json'):
                response_obj = SwaggerJSON(
                    data=utils.spec_from_api(
                        (
                            '',
                            cls.API,
                            *cls.ARGS
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
                response_obj = SwaggerYAML(
                    data=utils.spec_from_api(
                        (
                            '',
                            cls.API,
                            *cls.ARGS
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
                response_obj = SwaggerICON()
                status_code = 200
            elif request.path.endswith('16x16.png'):
                response_obj = SwaggerICON(img=static.ICON16)
                status_code = 200
            elif request.path.endswith('32x32.png'):
                response_obj = SwaggerICON(img=static.ICON32)
                status_code = 200
            elif cls.PATH_SUFFICES:
                response_obj = SwaggerHTML(
                    title=docent.core.utils.to_camel_case(cls.API),
                    path='/' + '/'.join(
                        (
                            *cls.PATH_SUFFICES,
                            'docs.yaml'
                            )
                        )
                    )
                status_code = 200
            else:
                response_obj = SwaggerHTML(
                    title=docent.core.utils.to_camel_case(cls.API)
                    )
                status_code = 200
            docent.core.log.info(
                {
                    'request_id': request_id,
                    'resource': cls.__name__,
                    'message': 'docs request processed successfully',
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
                response_obj = response.Error.from_exception(exception)
            else:
                response_obj = response.Error.from_exception(
                    exceptions.UnexpectedError
                    )
            status_code = response_obj.errorCode
            docent.core.log.error(
                {
                    'request_id': request_id,
                    'resource': cls.__name__,
                    'message': 'error processing docs request',
                    'status_code': str(status_code),
                    'response': response_obj,
                    },
                )
        return response_obj, status_code
