__all__ = (
    'Error',
    'Header',
    'Headers',
    'Response',
    'Responses',
    'ResponseSpec',
    )

import dataclasses
import datetime
import json
import typing

import docent.core

from .. import enums

from . import base
from . import constants
from . import documentation
from . import schema


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class Response(docent.core.objects.DocObject):  # noqa

    body: typing.Union[
        docent.core.objects.DocObject,
        list[docent.core.objects.DocObject],
        str
        ] = None
    status_code: int = 200

    _encoded: bool = False
    _headers: dict[str, str] = dataclasses.field(
        default_factory=lambda: {
            e.value: (
                str(v).lower()
                if isinstance(
                    (v := enums.header.DefaultHeaderValues[e.name].value),
                    bool
                    )
                else v
                )
            for e
            in enums.header.DefaultHeaders
            if e.name in enums.header.DefaultHeaderValues._member_map_
            }
        )

    def __post_init__(self):  # noqa
        if isinstance(self.body, documentation.SwaggerHTML):
            self._content = self.body.html
            self._content_type = enums.component.ContentType.html.value
        elif isinstance(self.body, documentation.SwaggerICON):
            self._content = self.body.img
            self._encoded = True
            self._content_type = enums.component.ContentType.icon.value
        elif isinstance(self.body, documentation.SwaggerJSON):
            self._content = json.dumps(self.body.data, default=str)
            self._content_type = enums.component.ContentType.json.value
        elif isinstance(self.body, documentation.SwaggerYAML):
            self._content = self.body.data
            self._content_type = enums.component.ContentType.yaml.value
        elif isinstance(self.body, docent.core.objects.DocObject):
            self._content = json.dumps(self.body.as_rest, default=str)
            self._content_type = enums.component.ContentType.json.value
        elif isinstance(self.body, str):
            self._content = self.body
            self._content_type = enums.component.ContentType.text.value
        elif isinstance(self.body, list):
            if (
                self.body
                and isinstance(
                    self.body[0],
                    (
                        docent.core.DocObject,
                        docent.core.DocMeta
                        )
                    )
                ):
                self.body = [o.as_rest for o in self.body]
            self._content = json.dumps(self.body, default=str)
            self._content_type = enums.component.ContentType.json.value
        else:
            self._content = ''
            self._content_type = enums.component.ContentType.json.value

        self._headers[
            enums.header.DefaultHeaders.contentLength.value
            ] = len(self._content)
        self._headers[
            enums.header.DefaultHeaders.contentType.value
            ] = self._content_type

        self._headers[
            enums.header.DefaultHeaders.date.value
            ] = datetime.datetime.now(datetime.timezone.utc).isoformat()


@dataclasses.dataclass
class Error(docent.core.objects.DocObject):  # noqa

    errorMessage: str = None
    errorCode: int = 400

    @classmethod
    def from_exception(cls, exception: Exception) -> 'Error':
        obj = cls(
            errorMessage=msg if (
                hasattr(exception, 'msg')
                and (msg := getattr(exception, 'msg'))
                    ) else arg if (
                        (a := getattr(exception, 'args'))
                        and isinstance(a, tuple)
                        and (arg := a[0])
                        ) else Constants.DEFAULT_ERROR_MAP.get(
                            exception,
                            Constants.DEFAULT_ERROR_MAP.get(
                                exception.__class__,
                                (
                                    exception.__doc__
                                    or exception.__class__.__doc__
                                    )
                                )
                            ),
            errorCode=Constants.ERROR_CODES.get(
                exception,
                Constants.ERROR_CODES.get(
                    exception.__class__,
                    400
                    )
                ),
            )
        return obj


@dataclasses.dataclass
class Header(base.Component):  # noqa

    description: str = None
    schema: dict = dataclasses.field(
        default_factory=lambda: {
            'type': enums.component.DataType.string.value
            }
        )

    def __post_init__(self):
        if self._name in {
            enums.header.DefaultHeaders.contentLength.value,
            enums.header.DefaultHeaders.accessControlMaxAge.value,
            }:
            self.schema = {'type': enums.component.DataType.integer.value}
        elif (
            self._name == (
                enums.
                header.
                DefaultHeaders.
                accessControlAllowCredentials.
                value
                )
            ):
            self.schema = {'type': enums.component.DataType.boolean.value}
        elif self._name == enums.header.DefaultHeaders.date.value:
            self.schema['format'] = enums.component.TypeFormat.date_time.value
        if self.description == '*':
            self.description = '\\' + self.description
        elif self.description and not isinstance(self.description, str):
            self.description = f'"{str(self.description).lower()}"'
        super().__post_init__()

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.headers.value


@dataclasses.dataclass
class Headers(base.Component):  # noqa

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.headers.value

    @property
    def as_component(self) -> dict[str, dict[str, typing.Any]]:  # noqa
        d = {}
        for component in self._extensions:
            d.update({component._name: component.as_reference})
        return d

    @classmethod
    def from_list(cls, headers: list[Header]) -> 'Headers':  # noqa
        return cls(_extensions=headers)


@dataclasses.dataclass
class ResponseSpec(base.Component):  # noqa

    description: str = None
    headers: Headers = None
    content: base.Content = None

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.responses.value

    @staticmethod
    def description_from_annotation(
        response_obj_type: typing.Union[
            docent.core.objects.DocObject,
            tuple[docent.core.objects.DocObject],
            None,
            ],
        spacing_multiplier: int = 2,
        ) -> str:  # noqa
        if not response_obj_type:
            description = 'An empty response.'
        elif isinstance(response_obj_type, typing._UnionGenericAlias):
            description = ('\n' + ' ' * spacing_multiplier + '* ').join(
                (
                    'Any of:',
                    *[
                        ResponseSpec.description_from_annotation(
                            t,
                            spacing_multiplier + 2
                            )
                        for t
                        in response_obj_type.__args__
                        ]
                    )
                )
        elif hasattr(response_obj_type, '__args__'):
            description = ('\n' + ' ' * spacing_multiplier + '* ').join(
                (
                    'An iterable container of:',
                    *[
                        ResponseSpec.description_from_annotation(
                            t,
                            spacing_multiplier + 2
                            )
                        for t
                        in response_obj_type.__args__
                        ]
                    )
                )
        else:
            description = response_obj_type.default_description
        return description

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        method_name: str,
        resource_path: str,
        response_headers: Headers = None,
        many: bool = False,
        ) -> 'ResponseSpec':
        error = Error.from_exception(exception)
        name = Constants.DOC_DELIM.join(
            (
                resource_path,
                method_name,
                'many' if many else 'one',
                str(error.errorCode)
                )
            )
        error.reference = Constants.DOC_DELIM.join(
            (
                name,
                exception.__name__
                if hasattr(exception, '__name__')
                else exception.__class__.__name__
                )
            )
        return cls(
            _name=name,
            description=error.errorMessage,
            headers=(
                response_headers.as_reference
                if
                response_headers
                else
                None
                ),
            content=base.Content(
                _name=enums.component.ContentType.json.value,
                schema=schema.SchemaObject.from_object(
                    error,
                    method_name=method_name,
                    many=many,
                    ).as_reference
                ),
            )

    @classmethod
    def from_annotation(
        cls,
        response_obj_type: typing.Type,
        method_name: str,
        resource_path: str,
        response_headers: Headers = None,
        ) -> 'ResponseSpec':
        success_code = Constants.METHOD_SUCCESS_CODES[method_name]
        description = cls.description_from_annotation(
            response_obj_type
            )
        name = Constants.DOC_DELIM.join(
            (
                resource_path,
                method_name,
                'many' if (
                    not isinstance(
                        response_obj_type,
                        typing._UnionGenericAlias
                        )
                    and hasattr(response_obj_type, '__args__')
                    ) else 'one',
                str(success_code)
                )
            )
        if not response_obj_type:
            response_obj = cls(
                _name=name,
                description=description,
                headers=(
                    response_headers.as_reference
                    if
                    response_headers
                    else
                    None
                    ),
                )
        else:
            response_obj = cls(
                _name=name,
                description=description,
                headers=(
                    response_headers.as_reference
                    if
                    response_headers
                    else
                    None
                    ),
                content=base.Content(
                    _name=enums.component.ContentType.json.value,
                    schema=schema.SchemaComponent.from_py_type(
                        response_obj_type,
                        response=True
                        )
                    ),
                )
        return response_obj


@dataclasses.dataclass
class Responses(base.Component):  # noqa

    @property
    def as_reference(self) -> dict[str, dict[str, typing.Any]]:  # noqa
        d = self._to_component()
        for component in self._extensions:
            d.update({component._name[-3:]: component.as_reference})
        else:
            return d

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.responses.value
